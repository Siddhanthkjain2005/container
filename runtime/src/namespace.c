/*
 * MiniContainer - Linux Container Runtime
 * namespace.c - Namespace management implementation
 */

#define _GNU_SOURCE
#include "../include/container.h"
#include <sys/prctl.h>

/* Default namespace flags for container isolation */
#define DEFAULT_NS_FLAGS (CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWUTS | \
                          CLONE_NEWIPC | CLONE_NEWCGROUP)

/**
 * Get namespace flags based on configuration
 */
static int get_ns_flags(container_config_t *config) {
    int flags = DEFAULT_NS_FLAGS;
    
    if (config->enable_network) {
        flags |= CLONE_NEWNET;
    }
    
    if (config->enable_user_ns) {
        flags |= CLONE_NEWUSER;
    }
    
    return flags;
}

/**
 * Write to a file (helper for uid_map, gid_map, etc.)
 */
static int write_file(const char *path, const char *content) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        mc_log(3, "Failed to open %s: %s", path, strerror(errno));
        return MC_ERR_IO;
    }
    
    ssize_t len = strlen(content);
    if (write(fd, content, len) != len) {
        mc_log(3, "Failed to write to %s: %s", path, strerror(errno));
        close(fd);
        return MC_ERR_IO;
    }
    
    close(fd);
    return MC_OK;
}

/**
 * Set up UTS namespace (hostname)
 */
int ns_setup_uts(const char *hostname) {
    if (hostname == NULL || strlen(hostname) == 0) {
        return MC_OK;
    }
    
    if (sethostname(hostname, strlen(hostname)) != 0) {
        mc_log(3, "Failed to set hostname: %s", strerror(errno));
        return MC_ERR_NAMESPACE;
    }
    
    mc_log(1, "Set hostname to: %s", hostname);
    return MC_OK;
}

/**
 * Set up user namespace mappings
 */
int ns_setup_user(pid_t pid, uid_t uid_host, uid_t uid_container,
                  gid_t gid_host, gid_t gid_container) {
    char path[PATH_MAX];
    char content[256];
    int ret;
    
    /* Disable setgroups first (required for unprivileged user namespaces) */
    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    ret = write_file(path, "deny");
    if (ret != MC_OK) {
        mc_log(2, "Could not write setgroups deny (may be already denied)");
    }
    
    /* Write UID mapping */
    snprintf(path, sizeof(path), "/proc/%d/uid_map", pid);
    snprintf(content, sizeof(content), "%u %u 1\n", uid_container, uid_host);
    ret = write_file(path, content);
    if (ret != MC_OK) {
        mc_log(3, "Failed to write uid_map");
        return ret;
    }
    mc_log(1, "Set UID mapping: %u -> %u", uid_container, uid_host);
    
    /* Write GID mapping */
    snprintf(path, sizeof(path), "/proc/%d/gid_map", pid);
    snprintf(content, sizeof(content), "%u %u 1\n", gid_container, gid_host);
    ret = write_file(path, content);
    if (ret != MC_OK) {
        mc_log(3, "Failed to write gid_map");
        return ret;
    }
    mc_log(1, "Set GID mapping: %u -> %u", gid_container, gid_host);
    
    return MC_OK;
}

/**
 * Container child process entry point
 * This runs inside the new namespaces
 */
typedef struct {
    container_config_t *config;
    int sync_pipe[2];  /* Pipe for synchronization */
} child_args_t;

static int container_child(void *arg) {
    child_args_t *args = (child_args_t *)arg;
    container_config_t *config = args->config;
    char buf;
    
    /* Wait for parent to set up user namespace mappings */
    close(args->sync_pipe[1]);
    if (read(args->sync_pipe[0], &buf, 1) != 1) {
        mc_log(3, "Failed to read from sync pipe");
        exit(1);
    }
    close(args->sync_pipe[0]);
    
    /* Set up UTS namespace (hostname) */
    if (ns_setup_uts(config->hostname) != MC_OK) {
        exit(1);
    }
    
    /* Set up mount namespace and filesystem */
    if (strlen(config->rootfs) > 0) {
        if (fs_pivot_root(config->rootfs) != MC_OK) {
            exit(1);
        }
        
        if (fs_mount_essentials() != MC_OK) {
            exit(1);
        }
    }
    
    /* Set environment variables */
    clearenv();
    setenv("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", 1);
    setenv("TERM", "xterm-256color", 1);
    setenv("HOME", "/root", 1);
    
    for (int i = 0; i < config->env_count && config->env[i]; i++) {
        char *eq = strchr(config->env[i], '=');
        if (eq) {
            *eq = '\0';
            setenv(config->env[i], eq + 1, 1);
            *eq = '=';
        }
    }
    
    /* Execute the command */
    if (config->cmd_count > 0 && config->cmd[0]) {
        mc_log(1, "Executing: %s", config->cmd[0]);
        execvp(config->cmd[0], config->cmd);
        mc_log(3, "Failed to exec: %s", strerror(errno));
        exit(127);
    }
    
    /* Default to /bin/sh if no command specified */
    char *default_cmd[] = {"/bin/sh", NULL};
    execvp(default_cmd[0], default_cmd);
    mc_log(3, "Failed to exec default shell: %s", strerror(errno));
    exit(127);
}

/**
 * Create new namespaces for a container
 * Uses clone() with namespace flags
 */
int ns_create(container_config_t *config) {
    child_args_t args;
    args.config = config;
    
    /* Create synchronization pipe */
    if (pipe(args.sync_pipe) != 0) {
        mc_log(3, "Failed to create sync pipe: %s", strerror(errno));
        return MC_ERR_IO;
    }
    
    /* Allocate stack for child process */
    char *stack = malloc(STACK_SIZE);
    if (!stack) {
        mc_log(3, "Failed to allocate stack");
        close(args.sync_pipe[0]);
        close(args.sync_pipe[1]);
        return MC_ERR_MEMORY;
    }
    
    /* Get namespace flags */
    int flags = get_ns_flags(config) | SIGCHLD;
    
    /* Clone with new namespaces */
    pid_t pid = clone(container_child, stack + STACK_SIZE, flags, &args);
    if (pid < 0) {
        mc_log(3, "clone() failed: %s", strerror(errno));
        free(stack);
        close(args.sync_pipe[0]);
        close(args.sync_pipe[1]);
        return MC_ERR_NAMESPACE;
    }
    
    mc_log(1, "Created container process with PID: %d", pid);
    
    /* Set up user namespace mappings if enabled */
    if (config->enable_user_ns) {
        int ret = ns_setup_user(pid, 
                                config->uid_map_host, config->uid_map_container,
                                config->gid_map_host, config->gid_map_container);
        if (ret != MC_OK) {
            kill(pid, SIGKILL);
            waitpid(pid, NULL, 0);
            free(stack);
            close(args.sync_pipe[0]);
            close(args.sync_pipe[1]);
            return ret;
        }
    }
    
    /* Signal child to continue */
    close(args.sync_pipe[0]);
    write(args.sync_pipe[1], "x", 1);
    close(args.sync_pipe[1]);
    
    /* Note: stack should not be freed while child is running */
    /* In a real implementation, we would track this and free on container exit */
    
    return pid;  /* Return the child PID */
}

/**
 * Enter an existing namespace
 */
int ns_enter(pid_t pid, int ns_type) {
    char ns_path[PATH_MAX];
    const char *ns_name;
    
    switch (ns_type) {
        case CLONE_NEWPID: ns_name = "pid"; break;
        case CLONE_NEWNS:  ns_name = "mnt"; break;
        case CLONE_NEWUTS: ns_name = "uts"; break;
        case CLONE_NEWIPC: ns_name = "ipc"; break;
        case CLONE_NEWNET: ns_name = "net"; break;
        case CLONE_NEWUSER: ns_name = "user"; break;
        case CLONE_NEWCGROUP: ns_name = "cgroup"; break;
        default:
            return MC_ERR_INVALID;
    }
    
    snprintf(ns_path, sizeof(ns_path), "/proc/%d/ns/%s", pid, ns_name);
    
    int fd = open(ns_path, O_RDONLY);
    if (fd < 0) {
        mc_log(3, "Failed to open %s: %s", ns_path, strerror(errno));
        return MC_ERR_NOT_FOUND;
    }
    
    if (setns(fd, ns_type) != 0) {
        mc_log(3, "setns() failed: %s", strerror(errno));
        close(fd);
        return MC_ERR_NAMESPACE;
    }
    
    close(fd);
    return MC_OK;
}

/**
 * Enter all namespaces of a container
 */
int ns_enter_all(pid_t pid, int flags) {
    int ns_types[] = {
        CLONE_NEWUSER,   /* User namespace must be first */
        CLONE_NEWPID,
        CLONE_NEWNS,
        CLONE_NEWUTS,
        CLONE_NEWIPC,
        CLONE_NEWNET,
        CLONE_NEWCGROUP
    };
    
    for (size_t i = 0; i < sizeof(ns_types) / sizeof(ns_types[0]); i++) {
        if (flags & ns_types[i]) {
            int ret = ns_enter(pid, ns_types[i]);
            if (ret != MC_OK && ret != MC_ERR_NOT_FOUND) {
                return ret;
            }
        }
    }
    
    return MC_OK;
}
