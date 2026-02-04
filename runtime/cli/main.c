/*
 * MiniContainer CLI - Low-level runtime interface
 */

#define _GNU_SOURCE
#include "../include/container.h"
#include <getopt.h>
#include <time.h>

static void print_usage(const char *prog) {
    printf("MiniContainer Runtime v%s\n\n", MINICONTAINER_VERSION);
    printf("Usage: %s <command> [options]\n\n", prog);
    printf("Commands:\n");
    printf("  create   Create a new container\n");
    printf("  start    Start a container\n");
    printf("  stop     Stop a container\n");
    printf("  delete   Delete a container\n");
    printf("  list     List containers\n");
    printf("  stats    Show container stats\n");
    printf("  run      Create and start container\n");
    printf("  exec     Execute command in container's cgroup\n");
    printf("  shell    Start interactive shell in new container\n\n");
    printf("Options:\n");
    printf("  --name <name>        Container name\n");
    printf("  --rootfs <path>      Path to rootfs\n");
    printf("  --memory <bytes>     Memory limit\n");
    printf("  --cpus <percent>     CPU limit (0-100)\n");
    printf("  --pids <max>         PID limit\n");
    printf("  --cmd <command>      Command to run\n");
    printf("  --help               Show this help\n");
}

static void print_containers(void) {
    container_t **list;
    int count;
    container_list(&list, &count);
    
    printf("%-12s %-20s %-10s %-8s\n", "ID", "NAME", "STATUS", "PID");
    printf("%-12s %-20s %-10s %-8s\n", "----", "----", "------", "---");
    
    const char *states[] = {"created", "running", "stopped", "paused", "deleted"};
    for (int i = 0; i < count; i++) {
        printf("%-12s %-20s %-10s %-8d\n",
               list[i]->config.id, list[i]->config.name,
               states[list[i]->state], list[i]->pid);
        container_free(list[i]);
    }
    if (list) free(list);
    printf("\nTotal: %d containers\n", count);
}

static void print_stats(const char *id) {
    container_t **list;
    int count;
    container_list(&list, &count);
    
    for (int i = 0; i < count; i++) {
        if (id && strcmp(list[i]->config.id, id) != 0 && strcmp(list[i]->config.name, id) != 0) {
            container_free(list[i]);
            continue;
        }
        container_metrics_t m;
        if (cgroup_get_metrics(list[i], &m) == MC_OK) {
            printf("Container: %s (%s)\n", list[i]->config.name, list[i]->config.id);
            printf("  Memory: %.2f MB / %.2f MB\n",
                   m.memory_usage_bytes / 1048576.0,
                   m.memory_limit_bytes > 0 ? m.memory_limit_bytes / 1048576.0 : -1);
            printf("  CPU: %ld ns\n", m.cpu_usage_ns);
            printf("  PIDs: %d / %d\n", m.pids_current, m.pids_limit);
            printf("\n");
        }
        container_free(list[i]);
    }
    if (list) free(list);
}

int main(int argc, char *argv[]) {
    if (argc < 2 || strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        print_usage(argv[0]);
        return 0;
    }
    
    if (geteuid() != 0) {
        fprintf(stderr, "Warning: Running without root privileges. Some features may not work.\n");
    }
    
    container_config_t config = {0};
    config.limits.cpu_period_us = 100000;
    
    static struct option opts[] = {
        {"name", required_argument, 0, 'n'},
        {"rootfs", required_argument, 0, 'r'},
        {"memory", required_argument, 0, 'm'},
        {"cpus", required_argument, 0, 'c'},
        {"pids", required_argument, 0, 'p'},
        {"cmd", required_argument, 0, 'x'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    
    char *run_cmd = NULL;
    int opt;
    while ((opt = getopt_long(argc, argv, "n:r:m:c:p:x:h", opts, NULL)) != -1) {
        switch (opt) {
            case 'n': 
                strncpy(config.name, optarg, sizeof(config.name)-1);
                strncpy(config.id, optarg, sizeof(config.id)-1); 
                break;
            case 'r': strncpy(config.rootfs, optarg, sizeof(config.rootfs)-1); break;
            case 'm': config.limits.memory_limit_bytes = atoll(optarg); break;
            case 'c': config.limits.cpu_quota_us = atoi(optarg) * 1000; break;
            case 'p': config.limits.pids_max = atoi(optarg); break;
            case 'x': run_cmd = optarg; break;
            case 'h': print_usage(argv[0]); return 0;
            default: print_usage(argv[0]); return 1;
        }
    }

    if (optind >= argc) {
        fprintf(stderr, "Error: No command specified\n");
        print_usage(argv[0]);
        return 1;
    }

    const char *cmd = argv[optind++];
    
    if (run_cmd) {
        config.cmd = malloc(sizeof(char*) * 4);
        config.cmd[0] = "/bin/sh"; config.cmd[1] = "-c";
        config.cmd[2] = run_cmd; config.cmd[3] = NULL;
        config.cmd_count = 3;
    }
    
    if (strcmp(cmd, "list") == 0 || strcmp(cmd, "ps") == 0) {
        print_containers();
    } else if (strcmp(cmd, "stats") == 0) {
        print_stats(optind < argc ? argv[optind] : NULL);
    } else if (strcmp(cmd, "create") == 0) {
        container_t *c;
        if (container_create(&config, &c) == MC_OK) {
            printf("Created container: %s\n", c->config.id);
            container_free(c);
        }
    } else if (strcmp(cmd, "run") == 0) {
        container_t *c;
        /* Parse --name if present after 'run' */
        while (optind < argc && strncmp(argv[optind], "--", 2) == 0) {
            if (strcmp(argv[optind], "--name") == 0 && optind + 1 < argc) {
                strncpy(config.name, argv[optind + 1], sizeof(config.name) - 1);
                strncpy(config.id, argv[optind + 1], sizeof(config.id) - 1);
                optind += 2;
            } else if (strcmp(argv[optind], "--") == 0) {
                /* Reached end of options */
                optind++;
                break;
            } else {
                optind++;
            }
        }
        /* Remaining args are the command */
        if (optind < argc) {
            config.cmd = &argv[optind];
            config.cmd_count = argc - optind;
        }
        if (container_create(&config, &c) == MC_OK) {
            printf("Created container: %s\n", c->config.id);
            if (container_start(c) == MC_OK) {
                printf("Started container (PID %d)\n", c->pid);
                int status;
                waitpid(c->pid, &status, 0);
                printf("Container exited with code %d\n", WEXITSTATUS(status));
            }
            container_delete(c);
            container_free(c);
        }
    } else if (strcmp(cmd, "start") == 0 || strcmp(cmd, "stop") == 0 || strcmp(cmd, "delete") == 0) {
        if (optind >= argc) { fprintf(stderr, "Container ID required\n"); return 1; }
        container_t **list; int count;
        container_list(&list, &count);
        for (int i = 0; i < count; i++) {
            if (strcmp(list[i]->config.id, argv[optind]) == 0 || 
                strcmp(list[i]->config.name, argv[optind]) == 0) {
                if (strcmp(cmd, "start") == 0) container_start(list[i]);
                else if (strcmp(cmd, "stop") == 0) container_stop(list[i], 10);
                else container_delete(list[i]);
                printf("Done\n");
            }
            container_free(list[i]);
        }
        if (list) free(list);
    } else if (strcmp(cmd, "exec") == 0) {
        /* Execute command inside container's cgroup */
        if (optind >= argc) { fprintf(stderr, "Container ID required\n"); return 1; }
        const char *container_id = argv[optind];
        
        /* Find the container */
        container_t **list; int count;
        container_list(&list, &count);
        container_t *target = NULL;
        for (int i = 0; i < count; i++) {
            if (strcmp(list[i]->config.id, container_id) == 0 || 
                strcmp(list[i]->config.name, container_id) == 0) {
                target = list[i];
            } else {
                container_free(list[i]);
            }
        }
        if (list) free(list);
        
        if (!target) {
            fprintf(stderr, "Container not found: %s\n", container_id);
            return 1;
        }
        
        /* Use container_exec which enters namespaces via setns() */
        char **exec_cmd;
        int exec_cmd_count;
        
        if (run_cmd) {
            exec_cmd = malloc(sizeof(char*) * 4);
            exec_cmd[0] = "/bin/sh";
            exec_cmd[1] = "-c";
            exec_cmd[2] = run_cmd;
            exec_cmd[3] = NULL;
            exec_cmd_count = 3;
        } else {
            /* Interactive shell */
            exec_cmd = malloc(sizeof(char*) * 2);
            exec_cmd[0] = "/bin/sh";
            exec_cmd[1] = NULL;
            exec_cmd_count = 1;
        }
        
        printf("Executing in container %s (PID %d) with namespace isolation...\n", 
               target->config.name, target->pid);
        
        int result = container_exec(target, exec_cmd, exec_cmd_count);
        if (result == MC_OK) {
            printf("Command completed successfully\n");
        } else {
            printf("Command failed (code %d)\n", result);
        }
        
        free(exec_cmd);
        container_free(target);
    } else if (strcmp(cmd, "shell") == 0) {
        /* Start interactive shell in a new container */
        if (strlen(config.rootfs) == 0) {
            strncpy(config.rootfs, "/tmp/alpine-rootfs", sizeof(config.rootfs)-1);
        }
        if (strlen(config.name) == 0) {
            snprintf(config.name, sizeof(config.name), "shell-%d", (int)time(NULL));
        }
        
        container_t *c;
        if (container_create(&config, &c) == MC_OK) {
            printf("Starting interactive shell in container %s\n", c->config.id);
            
            /* Set up interactive command */
            config.cmd = malloc(sizeof(char*) * 2);
            config.cmd[0] = "/bin/sh";
            config.cmd[1] = NULL;
            config.cmd_count = 1;
            
            if (container_start(c) == MC_OK) {
                int status;
                waitpid(c->pid, &status, 0);
            }
            container_delete(c);
            container_free(c);
        }
    } else {
        fprintf(stderr, "Unknown command: %s\n", cmd);
        return 1;
    }
    
    if (config.cmd) free(config.cmd);
    return 0;
}

