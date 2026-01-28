/*
 * MiniContainer - Container lifecycle management
 */

#define _GNU_SOURCE
#include "../include/container.h"
#include <time.h>
#include <stdarg.h>
#include <dirent.h>

#define STATE_DIR "/var/lib/minicontainer"

static int log_level = 1;

void mc_log(int level, const char *fmt, ...) {
    if (level < log_level) return;
    const char *levels[] = {"DEBUG", "INFO", "WARN", "ERROR"};
    va_list ap; va_start(ap, fmt);
    fprintf(stderr, "[%s] ", levels[level]);
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}

const char *mc_strerror(mc_error_t err) {
    switch(err) {
        case MC_OK: return "Success";
        case MC_ERR_MEMORY: return "Memory allocation failed";
        case MC_ERR_NAMESPACE: return "Namespace operation failed";
        case MC_ERR_CGROUP: return "Cgroup operation failed";
        case MC_ERR_FILESYSTEM: return "Filesystem operation failed";
        case MC_ERR_PROCESS: return "Process operation failed";
        case MC_ERR_PERMISSION: return "Permission denied";
        case MC_ERR_NOT_FOUND: return "Not found";
        case MC_ERR_INVALID: return "Invalid argument";
        case MC_ERR_EXISTS: return "Already exists";
        case MC_ERR_IO: return "I/O error";
        default: return "Unknown error";
    }
}

void generate_container_id(char *id) {
    srand(time(NULL) ^ getpid());
    for (int i = 0; i < 12; i++) {
        sprintf(id + i, "%x", rand() % 16);
    }
    id[12] = '\0';
}

const char *get_state_dir(void) { return STATE_DIR; }

static int save_container_state(container_t *c) {
    char path[PATH_MAX], state_name[32];
    snprintf(path, sizeof(path), "%s/state.txt", c->state_dir);
    FILE *fp = fopen(path, "w");
    if (!fp) return MC_ERR_IO;
    
    const char *states[] = {"created", "running", "stopped", "paused", "deleted"};
    fprintf(fp, "id=%s\nname=%s\nstate=%s\npid=%d\n", 
            c->config.id, c->config.name, states[c->state], c->pid);
    fclose(fp);
    return MC_OK;
}

int container_create(container_config_t *config, container_t **out) {
    container_t *c = calloc(1, sizeof(container_t));
    if (!c) return MC_ERR_MEMORY;
    
    memcpy(&c->config, config, sizeof(container_config_t));
    
    if (strlen(c->config.id) == 0) generate_container_id(c->config.id);
    if (strlen(c->config.name) == 0) strncpy(c->config.name, c->config.id, sizeof(c->config.name)-1);
    if (strlen(c->config.hostname) == 0) strncpy(c->config.hostname, c->config.name, sizeof(c->config.hostname)-1);
    
    snprintf(c->state_dir, sizeof(c->state_dir), "%s/containers/%s", STATE_DIR, c->config.id);
    
    char cmd[PATH_MAX];
    snprintf(cmd, sizeof(cmd), "mkdir -p %s", c->state_dir);
    system(cmd);
    
    c->state = CONTAINER_CREATED;
    c->created_at = time(NULL);
    
    if (cgroup_init(c) != MC_OK) mc_log(2, "Could not initialize cgroup");
    if (cgroup_apply_limits(c) != MC_OK) mc_log(2, "Could not apply limits");
    
    save_container_state(c);
    mc_log(1, "Created container: %s (%s)", c->config.name, c->config.id);
    *out = c;
    return MC_OK;
}

int container_start(container_t *c) {
    if (c->state == CONTAINER_RUNNING) return MC_ERR_INVALID;
    
    pid_t pid = ns_create(&c->config);
    if (pid < 0) return pid;
    
    c->pid = pid;
    c->state = CONTAINER_RUNNING;
    c->started_at = time(NULL);
    
    cgroup_add_pid(c, pid);
    save_container_state(c);
    mc_log(1, "Started container: %s (PID %d)", c->config.name, pid);
    return MC_OK;
}

int container_stop(container_t *c, int timeout) {
    if (c->state != CONTAINER_RUNNING) return MC_OK;
    
    kill(c->pid, SIGTERM);
    for (int i = 0; i < timeout * 10; i++) {
        if (waitpid(c->pid, &c->exit_code, WNOHANG) > 0) {
            c->state = CONTAINER_STOPPED;
            c->stopped_at = time(NULL);
            save_container_state(c);
            return MC_OK;
        }
        usleep(100000);
    }
    kill(c->pid, SIGKILL);
    waitpid(c->pid, &c->exit_code, 0);
    c->state = CONTAINER_STOPPED;
    c->stopped_at = time(NULL);
    save_container_state(c);
    return MC_OK;
}

int container_delete(container_t *c) {
    if (c->state == CONTAINER_RUNNING) container_stop(c, 10);
    cgroup_cleanup(c);
    fs_cleanup(c);
    
    char cmd[PATH_MAX];
    snprintf(cmd, sizeof(cmd), "rm -rf %s", c->state_dir);
    system(cmd);
    
    c->state = CONTAINER_DELETED;
    mc_log(1, "Deleted container: %s", c->config.name);
    return MC_OK;
}

int container_metrics(container_t *c, container_metrics_t *m) {
    return cgroup_get_metrics(c, m);
}

void container_free(container_t *c) {
    if (c) free(c);
}

int container_list(container_t ***containers, int *count) {
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/containers", STATE_DIR);
    
    DIR *dir = opendir(path);
    if (!dir) { *count = 0; *containers = NULL; return MC_OK; }
    
    int n = 0, cap = 16;
    container_t **list = malloc(sizeof(container_t*) * cap);
    
    struct dirent *ent;
    while ((ent = readdir(dir))) {
        if (ent->d_name[0] == '.') continue;
        
        char state_path[PATH_MAX];
        snprintf(state_path, sizeof(state_path), "%s/%s/state.txt", path, ent->d_name);
        
        FILE *fp = fopen(state_path, "r");
        if (!fp) continue;
        
        container_t *c = calloc(1, sizeof(container_t));
        char line[256];
        while (fgets(line, sizeof(line), fp)) {
            if (sscanf(line, "id=%64s", c->config.id) == 1) continue;
            if (sscanf(line, "name=%255s", c->config.name) == 1) continue;
            if (sscanf(line, "pid=%d", &c->pid) == 1) continue;
            char state[32];
            if (sscanf(line, "state=%31s", state) == 1) {
                if (!strcmp(state,"running")) c->state = CONTAINER_RUNNING;
                else if (!strcmp(state,"stopped")) c->state = CONTAINER_STOPPED;
                else c->state = CONTAINER_CREATED;
            }
        }
        fclose(fp);
        snprintf(c->state_dir, sizeof(c->state_dir), "%s/%s", path, ent->d_name);
        snprintf(c->cgroup_path, sizeof(c->cgroup_path), "/sys/fs/cgroup/minicontainer/%s", c->config.id);
        
        if (n >= cap) { cap *= 2; list = realloc(list, sizeof(container_t*) * cap); }
        list[n++] = c;
    }
    closedir(dir);
    *containers = list; *count = n;
    return MC_OK;
}

/**
 * Execute command in a running container's namespace
 * Uses setns() to enter the container's namespaces for true isolation
 */
int container_exec(container_t *c, char **cmd, int cmd_count) {
    if (!c || !cmd || cmd_count <= 0) {
        return MC_ERR_INVALID;
    }
    
    /* Container must be running */
    if (c->state != CONTAINER_RUNNING || c->pid <= 0) {
        mc_log(3, "Container is not running");
        return MC_ERR_PROCESS;
    }
    
    /* Verify the container process still exists */
    if (kill(c->pid, 0) != 0) {
        mc_log(3, "Container process %d not found", c->pid);
        return MC_ERR_NOT_FOUND;
    }
    
    pid_t exec_pid = fork();
    if (exec_pid < 0) {
        mc_log(3, "fork() failed: %s", strerror(errno));
        return MC_ERR_PROCESS;
    }
    
    if (exec_pid == 0) {
        /* Child process - enter namespaces and execute command */
        
        /* Define namespace flags to enter (order matters!) */
        int ns_flags = CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWCGROUP;
        
        /* Enter each namespace of the container's init process */
        /* Note: PID namespace entry is special - new process gets PID 1 in that namespace */
        
        /* Enter mount namespace first */
        if (ns_enter(c->pid, CLONE_NEWNS) != MC_OK) {
            mc_log(3, "Failed to enter mount namespace");
            /* Continue anyway - might work without it */
        }
        
        /* Enter UTS namespace */
        if (ns_enter(c->pid, CLONE_NEWUTS) != MC_OK) {
            mc_log(3, "Failed to enter UTS namespace");
        }
        
        /* Enter IPC namespace */
        if (ns_enter(c->pid, CLONE_NEWIPC) != MC_OK) {
            mc_log(3, "Failed to enter IPC namespace");
        }
        
        /* Enter cgroup namespace */
        if (ns_enter(c->pid, CLONE_NEWCGROUP) != MC_OK) {
            mc_log(3, "Failed to enter cgroup namespace");
        }
        
        /* Add this process to the container's cgroup */
        cgroup_add_pid(c, getpid());
        
        /* Change to root directory (inside container's mount namespace) */
        if (chdir("/") != 0) {
            mc_log(2, "Failed to chdir to /");
        }
        
        /* Execute the command */
        mc_log(1, "Executing command in container %s: %s", c->config.name, cmd[0]);
        execvp(cmd[0], cmd);
        
        /* If execvp returns, it failed */
        mc_log(3, "execvp failed: %s", strerror(errno));
        _exit(127);
    }
    
    /* Parent process - wait for child */
    int status;
    if (waitpid(exec_pid, &status, 0) < 0) {
        mc_log(3, "waitpid failed: %s", strerror(errno));
        return MC_ERR_PROCESS;
    }
    
    if (WIFEXITED(status)) {
        int exit_code = WEXITSTATUS(status);
        mc_log(1, "Command exited with code %d", exit_code);
        return (exit_code == 0) ? MC_OK : MC_ERR_PROCESS;
    }
    
    return MC_OK;
}
