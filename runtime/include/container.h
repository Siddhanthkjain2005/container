/*
 * MiniContainer - Linux Container Runtime
 * container.h - Main header file
 */

#ifndef MINICONTAINER_H
#define MINICONTAINER_H

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sched.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <linux/limits.h>

/* Version info */
#define MINICONTAINER_VERSION "1.0.0"
#define MINICONTAINER_NAME "minicontainer"

/* Container states */
typedef enum {
    CONTAINER_CREATED = 0,
    CONTAINER_RUNNING = 1,
    CONTAINER_STOPPED = 2,
    CONTAINER_PAUSED = 3,
    CONTAINER_DELETED = 4
} container_state_t;

/* Error codes */
typedef enum {
    MC_OK = 0,
    MC_ERR_MEMORY = -1,
    MC_ERR_NAMESPACE = -2,
    MC_ERR_CGROUP = -3,
    MC_ERR_FILESYSTEM = -4,
    MC_ERR_PROCESS = -5,
    MC_ERR_PERMISSION = -6,
    MC_ERR_NOT_FOUND = -7,
    MC_ERR_INVALID = -8,
    MC_ERR_EXISTS = -9,
    MC_ERR_IO = -10
} mc_error_t;

/* Resource limits configuration */
typedef struct {
    long memory_limit_bytes;      /* Memory limit in bytes (0 = unlimited) */
    long memory_swap_bytes;       /* Swap limit in bytes (-1 = same as memory) */
    int cpu_shares;               /* CPU shares (relative weight) */
    int cpu_quota_us;             /* CPU quota in microseconds */
    int cpu_period_us;            /* CPU period in microseconds (default 100000) */
    int pids_max;                 /* Maximum number of PIDs (0 = unlimited) */
} resource_limits_t;

/* Container configuration */
typedef struct {
    char id[65];                  /* Container ID (64 chars + null) */
    char name[256];               /* Container name */
    char hostname[256];           /* Hostname inside container */
    char rootfs[PATH_MAX];        /* Path to rootfs directory */
    char **cmd;                   /* Command to execute */
    int cmd_count;                /* Number of command arguments */
    char **env;                   /* Environment variables */
    int env_count;                /* Number of environment variables */
    resource_limits_t limits;     /* Resource limits */
    int enable_network;           /* Enable network namespace */
    int enable_user_ns;           /* Enable user namespace */
    uid_t uid_map_host;           /* Host UID for mapping */
    uid_t uid_map_container;      /* Container UID for mapping */
    gid_t gid_map_host;           /* Host GID for mapping */
    gid_t gid_map_container;      /* Container GID for mapping */
} container_config_t;

/* Container runtime metrics */
typedef struct {
    long memory_usage_bytes;      /* Current memory usage */
    long memory_max_usage_bytes;  /* Peak memory usage */
    long memory_limit_bytes;      /* Memory limit */
    double cpu_usage_percent;     /* CPU usage percentage */
    long cpu_usage_ns;            /* CPU usage in nanoseconds */
    int pids_current;             /* Current number of PIDs */
    int pids_limit;               /* PID limit */
    long net_rx_bytes;            /* Network bytes received */
    long net_tx_bytes;            /* Network bytes transmitted */
} container_metrics_t;

/* Container structure */
typedef struct {
    container_config_t config;    /* Container configuration */
    container_state_t state;      /* Current state */
    pid_t pid;                    /* Container init PID */
    int exit_code;                /* Exit code if stopped */
    char cgroup_path[PATH_MAX];   /* Cgroup path */
    char state_dir[PATH_MAX];     /* State directory path */
    time_t created_at;            /* Creation timestamp */
    time_t started_at;            /* Start timestamp */
    time_t stopped_at;            /* Stop timestamp */
} container_t;

/* Stack size for clone */
#define STACK_SIZE (1024 * 1024)

/* ===== Namespace Functions ===== */

/**
 * Create new namespaces for a container
 * @param config Container configuration
 * @return MC_OK on success, error code on failure
 */
int ns_create(container_config_t *config);

/**
 * Set up UTS namespace (hostname)
 * @param hostname Hostname to set
 * @return MC_OK on success, error code on failure
 */
int ns_setup_uts(const char *hostname);

/**
 * Set up user namespace mappings
 * @param pid Process ID
 * @param uid_host Host UID
 * @param uid_container Container UID
 * @param gid_host Host GID
 * @param gid_container Container GID
 * @return MC_OK on success, error code on failure
 */
int ns_setup_user(pid_t pid, uid_t uid_host, uid_t uid_container,
                  gid_t gid_host, gid_t gid_container);

/**
 * Enter an existing namespace of a process
 * @param pid Process ID whose namespace to enter
 * @param ns_type Namespace type (CLONE_NEWPID, CLONE_NEWNS, etc.)
 * @return MC_OK on success, error code on failure
 */
int ns_enter(pid_t pid, int ns_type);

/**
 * Enter all namespaces of a process
 * @param pid Process ID whose namespaces to enter
 * @param flags Namespace flags to enter
 * @return MC_OK on success, error code on failure
 */
int ns_enter_all(pid_t pid, int flags);

/* ===== Cgroup Functions ===== */

/**
 * Initialize cgroup for container
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int cgroup_init(container_t *container);

/**
 * Apply resource limits to cgroup
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int cgroup_apply_limits(container_t *container);

/**
 * Add process to cgroup
 * @param container Container structure
 * @param pid Process ID to add
 * @return MC_OK on success, error code on failure
 */
int cgroup_add_pid(container_t *container, pid_t pid);

/**
 * Get container metrics from cgroup
 * @param container Container structure
 * @param metrics Output metrics structure
 * @return MC_OK on success, error code on failure
 */
int cgroup_get_metrics(container_t *container, container_metrics_t *metrics);

/**
 * Cleanup cgroup for container
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int cgroup_cleanup(container_t *container);

/* ===== Filesystem Functions ===== */

/**
 * Set up container filesystem
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int fs_setup(container_t *container);

/**
 * Set up mount namespace and pivot root
 * @param rootfs Path to rootfs
 * @return MC_OK on success, error code on failure
 */
int fs_pivot_root(const char *rootfs);

/**
 * Mount essential filesystems (/proc, /sys, /dev)
 * @return MC_OK on success, error code on failure
 */
int fs_mount_essentials(void);

/**
 * Cleanup filesystem mounts
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int fs_cleanup(container_t *container);

/* ===== Container Lifecycle Functions ===== */

/**
 * Create a new container
 * @param config Container configuration
 * @param container Output container structure
 * @return MC_OK on success, error code on failure
 */
int container_create(container_config_t *config, container_t **container);

/**
 * Start a container
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int container_start(container_t *container);

/**
 * Stop a container
 * @param container Container structure
 * @param timeout Timeout in seconds before SIGKILL
 * @return MC_OK on success, error code on failure
 */
int container_stop(container_t *container, int timeout);

/**
 * Delete a container
 * @param container Container structure
 * @return MC_OK on success, error code on failure
 */
int container_delete(container_t *container);

/**
 * Get container by ID or name
 * @param id_or_name Container ID or name
 * @param container Output container structure
 * @return MC_OK on success, error code on failure
 */
int container_get(const char *id_or_name, container_t **container);

/**
 * List all containers
 * @param containers Output array of containers
 * @param count Output count
 * @return MC_OK on success, error code on failure
 */
int container_list(container_t ***containers, int *count);

/**
 * Execute command in running container
 * @param container Container structure
 * @param cmd Command to execute
 * @param cmd_count Number of command arguments
 * @return MC_OK on success, error code on failure
 */
int container_exec(container_t *container, char **cmd, int cmd_count);

/**
 * Get container metrics
 * @param container Container structure
 * @param metrics Output metrics structure
 * @return MC_OK on success, error code on failure
 */
int container_metrics(container_t *container, container_metrics_t *metrics);

/**
 * Free container structure
 * @param container Container structure to free
 */
void container_free(container_t *container);

/* ===== Utility Functions ===== */

/**
 * Generate random container ID
 * @param id Output buffer (must be at least 65 bytes)
 */
void generate_container_id(char *id);

/**
 * Get state directory for containers
 * @return Path to state directory
 */
const char *get_state_dir(void);

/**
 * Get error message for error code
 * @param err Error code
 * @return Error message string
 */
const char *mc_strerror(mc_error_t err);

/**
 * Log message with level
 * @param level Log level (0=debug, 1=info, 2=warn, 3=error)
 * @param fmt Format string
 */
void mc_log(int level, const char *fmt, ...);

#endif /* MINICONTAINER_H */
