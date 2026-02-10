/*
 * KernelSight - Linux Container Runtime
 * cgroup.c - Cgroup v2 management implementation
 */

#define _GNU_SOURCE
#include "../include/container.h"

/* Cgroup v2 base path */
#define CGROUP_ROOT "/sys/fs/cgroup"
#define MINICONTAINER_CGROUP "kernelsight"

/**
 * Check if cgroup v2 is available
 */
static int cgroup_v2_available(void) {
    struct stat st;
    char path[PATH_MAX];
    
    snprintf(path, sizeof(path), "%s/cgroup.controllers", CGROUP_ROOT);
    return stat(path, &st) == 0;
}

/**
 * Read a value from a cgroup file
 */
static long read_cgroup_value(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    
    long value = 0;
    if (fscanf(fp, "%ld", &value) != 1) {
        fclose(fp);
        return -1;
    }
    
    fclose(fp);
    return value;
}

/**
 * Read a string from a cgroup file
 */
static int read_cgroup_string(const char *path, char *buf, size_t size) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return MC_ERR_IO;
    }
    
    if (fgets(buf, size, fp) == NULL) {
        fclose(fp);
        return MC_ERR_IO;
    }
    
    fclose(fp);
    
    /* Remove trailing newline */
    size_t len = strlen(buf);
    if (len > 0 && buf[len - 1] == '\n') {
        buf[len - 1] = '\0';
    }
    
    return MC_OK;
}

/**
 * Write a value to a cgroup file
 */
static int write_cgroup_value(const char *path, const char *value) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        mc_log(3, "Failed to open %s: %s", path, strerror(errno));
        return MC_ERR_IO;
    }
    
    ssize_t len = strlen(value);
    if (write(fd, value, len) != len) {
        mc_log(3, "Failed to write to %s: %s", path, strerror(errno));
        close(fd);
        return MC_ERR_IO;
    }
    
    close(fd);
    return MC_OK;
}

/**
 * Create the kernelsight cgroup hierarchy
 */
static int cgroup_create_hierarchy(void) {
    char path[PATH_MAX];
    
    /* Create base kernelsight cgroup */
    snprintf(path, sizeof(path), "%s/%s", CGROUP_ROOT, MINICONTAINER_CGROUP);
    if (mkdir(path, 0755) != 0 && errno != EEXIST) {
        mc_log(3, "Failed to create cgroup directory %s: %s", path, strerror(errno));
        return MC_ERR_CGROUP;
    }
    
    /* Enable controllers in the base cgroup */
    snprintf(path, sizeof(path), "%s/cgroup.subtree_control", CGROUP_ROOT);
    
    /* Try to enable each controller */
    const char *controllers[] = {"+cpu", "+memory", "+pids", "+io"};
    for (size_t i = 0; i < sizeof(controllers) / sizeof(controllers[0]); i++) {
        if (write_cgroup_value(path, controllers[i]) != MC_OK) {
            mc_log(2, "Could not enable controller %s (may already be enabled)", controllers[i]);
        }
    }
    
    /* Enable controllers in kernelsight cgroup */
    snprintf(path, sizeof(path), "%s/%s/cgroup.subtree_control", 
             CGROUP_ROOT, MINICONTAINER_CGROUP);
    for (size_t i = 0; i < sizeof(controllers) / sizeof(controllers[0]); i++) {
        if (write_cgroup_value(path, controllers[i]) != MC_OK) {
            mc_log(2, "Could not enable controller %s in kernelsight cgroup", controllers[i]);
        }
    }
    
    return MC_OK;
}

/**
 * Initialize cgroup for container
 */
int cgroup_init(container_t *container) {
    if (!cgroup_v2_available()) {
        mc_log(3, "Cgroup v2 is not available");
        return MC_ERR_CGROUP;
    }
    
    /* Create hierarchy if needed */
    int ret = cgroup_create_hierarchy();
    if (ret != MC_OK) {
        return ret;
    }
    
    /* Create container-specific cgroup */
    snprintf(container->cgroup_path, sizeof(container->cgroup_path),
             "%s/%s/%s", CGROUP_ROOT, MINICONTAINER_CGROUP, container->config.id);
    
    if (mkdir(container->cgroup_path, 0755) != 0 && errno != EEXIST) {
        mc_log(3, "Failed to create container cgroup: %s", strerror(errno));
        return MC_ERR_CGROUP;
    }
    
    mc_log(1, "Created cgroup: %s", container->cgroup_path);
    return MC_OK;
}

/**
 * Apply resource limits to cgroup
 */
int cgroup_apply_limits(container_t *container) {
    char path[PATH_MAX];
    char value[128];
    resource_limits_t *limits = &container->config.limits;
    
    /* Apply memory limit */
    if (limits->memory_limit_bytes > 0) {
        snprintf(path, sizeof(path), "%s/memory.max", container->cgroup_path);
        snprintf(value, sizeof(value), "%ld", limits->memory_limit_bytes);
        if (write_cgroup_value(path, value) != MC_OK) {
            mc_log(2, "Could not set memory limit");
        } else {
            mc_log(1, "Set memory limit: %ld bytes", limits->memory_limit_bytes);
        }
        
        /* Apply swap limit */
        if (limits->memory_swap_bytes >= 0) {
            snprintf(path, sizeof(path), "%s/memory.swap.max", container->cgroup_path);
            snprintf(value, sizeof(value), "%ld", limits->memory_swap_bytes);
            if (write_cgroup_value(path, value) != MC_OK) {
                mc_log(2, "Could not set swap limit");
            }
        }
    }
    
    /* Apply CPU limit */
    if (limits->cpu_quota_us > 0) {
        int period = limits->cpu_period_us > 0 ? limits->cpu_period_us : 100000;
        snprintf(path, sizeof(path), "%s/cpu.max", container->cgroup_path);
        snprintf(value, sizeof(value), "%d %d", limits->cpu_quota_us, period);
        if (write_cgroup_value(path, value) != MC_OK) {
            mc_log(2, "Could not set CPU limit");
        } else {
            mc_log(1, "Set CPU limit: %d/%d us", limits->cpu_quota_us, period);
        }
    }
    
    /* Apply CPU weight (shares) */
    if (limits->cpu_shares > 0) {
        /* Convert shares (Docker-style) to weight (cgroup v2 style) */
        /* shares: 2-262144, default 1024 -> weight: 1-10000, default 100 */
        int weight = (limits->cpu_shares * 100) / 1024;
        if (weight < 1) weight = 1;
        if (weight > 10000) weight = 10000;
        
        snprintf(path, sizeof(path), "%s/cpu.weight", container->cgroup_path);
        snprintf(value, sizeof(value), "%d", weight);
        if (write_cgroup_value(path, value) != MC_OK) {
            mc_log(2, "Could not set CPU weight");
        }
    }
    
    /* Apply PID limit */
    if (limits->pids_max > 0) {
        snprintf(path, sizeof(path), "%s/pids.max", container->cgroup_path);
        snprintf(value, sizeof(value), "%d", limits->pids_max);
        if (write_cgroup_value(path, value) != MC_OK) {
            mc_log(2, "Could not set PID limit");
        } else {
            mc_log(1, "Set PID limit: %d", limits->pids_max);
        }
    }
    
    return MC_OK;
}

/**
 * Add process to cgroup
 */
int cgroup_add_pid(container_t *container, pid_t pid) {
    char path[PATH_MAX];
    char value[32];
    
    snprintf(path, sizeof(path), "%s/cgroup.procs", container->cgroup_path);
    snprintf(value, sizeof(value), "%d", pid);
    
    int ret = write_cgroup_value(path, value);
    if (ret != MC_OK) {
        mc_log(3, "Failed to add PID %d to cgroup", pid);
        return ret;
    }
    
    mc_log(1, "Added PID %d to cgroup", pid);
    return MC_OK;
}

/**
 * Get container metrics from cgroup
 */
int cgroup_get_metrics(container_t *container, container_metrics_t *metrics) {
    char path[PATH_MAX];
    char buf[1024];
    
    memset(metrics, 0, sizeof(*metrics));
    
    /* Memory usage */
    snprintf(path, sizeof(path), "%s/memory.current", container->cgroup_path);
    metrics->memory_usage_bytes = read_cgroup_value(path);
    
    /* Memory max usage */
    snprintf(path, sizeof(path), "%s/memory.peak", container->cgroup_path);
    metrics->memory_max_usage_bytes = read_cgroup_value(path);
    
    /* Memory limit */
    snprintf(path, sizeof(path), "%s/memory.max", container->cgroup_path);
    if (read_cgroup_string(path, buf, sizeof(buf)) == MC_OK) {
        if (strcmp(buf, "max") == 0) {
            metrics->memory_limit_bytes = -1;  /* Unlimited */
        } else {
            metrics->memory_limit_bytes = atol(buf);
        }
    }
    
    /* CPU usage */
    snprintf(path, sizeof(path), "%s/cpu.stat", container->cgroup_path);
    FILE *fp = fopen(path, "r");
    if (fp) {
        while (fgets(buf, sizeof(buf), fp)) {
            long value;
            if (sscanf(buf, "usage_usec %ld", &value) == 1) {
                metrics->cpu_usage_ns = value * 1000;  /* Convert to nanoseconds */
            }
        }
        fclose(fp);
    }
    
    /* PID count */
    snprintf(path, sizeof(path), "%s/pids.current", container->cgroup_path);
    metrics->pids_current = (int)read_cgroup_value(path);
    
    /* PID limit */
    snprintf(path, sizeof(path), "%s/pids.max", container->cgroup_path);
    if (read_cgroup_string(path, buf, sizeof(buf)) == MC_OK) {
        if (strcmp(buf, "max") == 0) {
            metrics->pids_limit = -1;  /* Unlimited */
        } else {
            metrics->pids_limit = atoi(buf);
        }
    }
    
    return MC_OK;
}

/**
 * Freeze container processes
 */
int cgroup_freeze(container_t *container) {
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/cgroup.freeze", container->cgroup_path);
    return write_cgroup_value(path, "1");
}

/**
 * Unfreeze container processes
 */
int cgroup_unfreeze(container_t *container) {
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/cgroup.freeze", container->cgroup_path);
    return write_cgroup_value(path, "0");
}

/**
 * Kill all processes in cgroup
 */
int cgroup_kill_all(container_t *container) {
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/cgroup.kill", container->cgroup_path);
    
    /* cgroup.kill might not exist in all kernels */
    if (access(path, W_OK) == 0) {
        return write_cgroup_value(path, "1");
    }
    
    /* Fallback: read PIDs and kill them */
    snprintf(path, sizeof(path), "%s/cgroup.procs", container->cgroup_path);
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return MC_ERR_IO;
    }
    
    pid_t pid;
    while (fscanf(fp, "%d", &pid) == 1) {
        kill(pid, SIGKILL);
    }
    fclose(fp);
    
    return MC_OK;
}

/**
 * Cleanup cgroup for container
 */
int cgroup_cleanup(container_t *container) {
    if (strlen(container->cgroup_path) == 0) {
        return MC_OK;
    }
    
    /* Kill all processes first */
    cgroup_kill_all(container);
    
    /* Wait a bit for processes to die */
    usleep(100000);  /* 100ms */
    
    /* Remove the cgroup directory */
    if (rmdir(container->cgroup_path) != 0 && errno != ENOENT) {
        mc_log(2, "Could not remove cgroup %s: %s", 
               container->cgroup_path, strerror(errno));
        return MC_ERR_CGROUP;
    }
    
    mc_log(1, "Removed cgroup: %s", container->cgroup_path);
    return MC_OK;
}
