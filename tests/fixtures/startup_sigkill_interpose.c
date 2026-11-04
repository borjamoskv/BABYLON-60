/* Test-only observers: execute the real syscalls, then stop at an exact boundary. */
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

static int fence_fd = -1;
static int reported_wait;
static int reported_acquired;

static void event(const char *name, int fd) {
    const char *control = getenv("B60_KILL_CONTROL");
    const char *role = getenv("B60_KILL_ROLE");
    if (!control || !role) _exit(110);
    char temporary[PATH_MAX], destination[PATH_MAX], record[128];
    int a = snprintf(temporary, sizeof temporary, "%s/%s-%s.tmp", control, role, name);
    int b = snprintf(destination, sizeof destination, "%s/%s-%s", control, role, name);
    struct stat st;
    if (a < 0 || b < 0 || a >= (int)sizeof temporary || b >= (int)sizeof destination || fstat(fd, &st)) _exit(111);
    int n = snprintf(record, sizeof record, "%ld %llu %llu\n", (long)getpid(),
                     (unsigned long long)st.st_dev, (unsigned long long)st.st_ino);
    if (n <= 0 || n >= (int)sizeof record) _exit(112);
    int out = open(temporary, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (out < 0) _exit(113);
    int offset = 0;
    while (offset < n) {
        ssize_t written = write(out, record + offset, (size_t)(n - offset));
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) _exit(114);
        offset += (int)written;
    }
    if (close(out) || rename(temporary, destination)) _exit(115);
}

static void stop_at(const char *phase) {
    const char *role = getenv("B60_KILL_ROLE");
    const char *requested = getenv("B60_KILL_PHASE");
    if (role && requested && !strcmp(role, "creator") && !strcmp(requested, phase)) {
        if (raise(SIGSTOP)) _exit(116);
    }
}

static int observed_openat(int directory, const char *path, int flags, ...) {
    int fd;
    if (flags & O_CREAT) {
        va_list args;
        va_start(args, flags);
        int mode = va_arg(args, int);
        va_end(args);
        fd = openat(directory, path, flags, mode);
    } else {
        fd = openat(directory, path, flags);
    }
    int saved_errno = errno;
    if (fd >= 0 && !strcmp(path, ".epoch_fence.bin")) {
        fence_fd = fd;
        if ((flags & (O_CREAT | O_EXCL)) == (O_CREAT | O_EXCL)) {
            event("created", fd);
            stop_at("created");
        }
    }
    errno = saved_errno;
    return fd;
}

static int observed_flock(int fd, int operation) {
    int observe = fd == fence_fd && operation == LOCK_EX;
    if (observe && !reported_wait) {
        reported_wait = 1;
        event("waiting", fd);
    }
    int result = flock(fd, operation);
    int saved_errno = errno;
    if (observe && !result && !reported_acquired) {
        reported_acquired = 1;
        event("acquired", fd);
        stop_at("locked");
    }
    errno = saved_errno;
    return result;
}

#define INTERPOSE(replacement, original) \
    __attribute__((used)) static struct { const void *new_fn; const void *old_fn; } \
    interpose_##original __attribute__((section("__DATA,__interpose"))) = \
    { (const void *)&replacement, (const void *)&original }
INTERPOSE(observed_openat, openat);
INTERPOSE(observed_flock, flock);
