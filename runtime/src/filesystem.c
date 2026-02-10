/*
 * KernelSight - Filesystem management
 */

#define _GNU_SOURCE
#include "../include/container.h"
#include <sys/mount.h>
#include <sys/sysmacros.h>

static int mkdir_p(const char *path, mode_t mode) {
    char tmp[PATH_MAX];
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (char *p = tmp + 1; *p; p++) {
        if (*p == '/') { *p = 0; mkdir(tmp, mode); *p = '/'; }
    }
    return mkdir(tmp, mode) == 0 || errno == EEXIST ? MC_OK : MC_ERR_IO;
}

static int dir_exists(const char *path) {
    struct stat st;
    return stat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

int fs_pivot_root(const char *rootfs) {
    char put_old[PATH_MAX];
    if (!rootfs || !dir_exists(rootfs)) {
        mc_log(3, "Rootfs does not exist: %s", rootfs ? rootfs : "(null)");
        return MC_ERR_FILESYSTEM;
    }
    
    /* Make all mounts private first - critical for pivot_root */
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0) {
        mc_log(3, "Failed to make mounts private: %s", strerror(errno));
        return MC_ERR_FILESYSTEM;
    }
    
    /* Bind mount the rootfs to itself */
    if (mount(rootfs, rootfs, NULL, MS_BIND | MS_REC, NULL) != 0) {
        mc_log(3, "Failed to bind mount rootfs: %s", strerror(errno));
        return MC_ERR_FILESYSTEM;
    }
    
    snprintf(put_old, sizeof(put_old), "%s/.old_root", rootfs);
    mkdir_p(put_old, 0700);
    
    /* Switch root filesystem */
    if (syscall(SYS_pivot_root, rootfs, put_old) != 0) {
        mc_log(3, "pivot_root failed: %s", strerror(errno));
        rmdir(put_old);
        return MC_ERR_FILESYSTEM;
    }
    
    if (chdir("/") != 0) {
        mc_log(3, "chdir to / failed: %s", strerror(errno));
    }
    
    /* Unmount old root */
    if (umount2("/.old_root", MNT_DETACH) != 0) {
        mc_log(2, "umount old_root failed: %s", strerror(errno));
    }
    rmdir("/.old_root");
    
    mc_log(1, "pivot_root completed successfully");
    return MC_OK;
}

int fs_mount_essentials(void) {
    mkdir_p("/proc", 0555); mkdir_p("/sys", 0555);
    mkdir_p("/dev", 0755); mkdir_p("/dev/pts", 0755);
    mkdir_p("/dev/shm", 1777); mkdir_p("/tmp", 01777);
    
    mount("proc", "/proc", "proc", MS_NOSUID | MS_NOEXEC | MS_NODEV, NULL);
    mount("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY, NULL);
    
    if (mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID | MS_NOEXEC, NULL) != 0)
        mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC, "mode=755");
    
    mount("devpts", "/dev/pts", "devpts", MS_NOSUID | MS_NOEXEC, "newinstance,ptmxmode=0666");
    mount("shm", "/dev/shm", "tmpfs", MS_NOSUID | MS_NOEXEC | MS_NODEV, "mode=1777");
    mount("tmpfs", "/tmp", "tmpfs", MS_NOSUID | MS_NODEV, "mode=1777");
    
    struct { const char *name; mode_t mode; dev_t dev; } devs[] = {
        {"/dev/null", S_IFCHR|0666, makedev(1,3)}, {"/dev/zero", S_IFCHR|0666, makedev(1,5)},
        {"/dev/random", S_IFCHR|0666, makedev(1,8)}, {"/dev/urandom", S_IFCHR|0666, makedev(1,9)},
        {"/dev/tty", S_IFCHR|0666, makedev(5,0)}, {"/dev/console", S_IFCHR|0600, makedev(5,1)},
    };
    for (size_t i = 0; i < sizeof(devs)/sizeof(devs[0]); i++)
        mknod(devs[i].name, devs[i].mode, devs[i].dev);
    
    symlink("/proc/self/fd", "/dev/fd");
    symlink("/proc/self/fd/0", "/dev/stdin");
    symlink("/proc/self/fd/1", "/dev/stdout");
    symlink("/proc/self/fd/2", "/dev/stderr");
    return MC_OK;
}

int fs_setup(container_t *container) {
    if (!container->config.rootfs[0]) {
        mc_log(3, "ERROR: No rootfs specified - refusing to run without filesystem isolation!");
        return MC_ERR_FILESYSTEM;  /* REQUIRE rootfs for safety */
    }
    if (!dir_exists(container->config.rootfs)) {
        mc_log(3, "ERROR: Rootfs does not exist: %s", container->config.rootfs);
        return MC_ERR_FILESYSTEM;
    }
    
    /* Perform full filesystem isolation using pivot_root */
    int ret = fs_pivot_root(container->config.rootfs);
    if (ret != MC_OK) {
        mc_log(3, "ERROR: pivot_root failed - cannot ensure filesystem isolation!");
        return ret;
    }
    
    /* Mount essential filesystems inside the isolated root */
    ret = fs_mount_essentials();
    if (ret != MC_OK) {
        mc_log(2, "Warning: Some essential mounts may have failed");
    }
    
    mc_log(1, "Filesystem isolation complete with rootfs: %s", container->config.rootfs);
    return MC_OK;
}

int fs_cleanup(container_t *container) {
    if (container->state_dir[0]) {
        char merged[PATH_MAX];
        snprintf(merged, sizeof(merged), "%s/merged", container->state_dir);
        umount2(merged, MNT_DETACH);
    }
    return MC_OK;
}
