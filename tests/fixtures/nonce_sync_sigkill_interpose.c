/* macOS test observer. Calls real syscalls; only the requested stop is injected. */
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

static int observer_gates;

static int role_is(const char *expected) {
    const char *role = getenv("B60_NONCE_ROLE");
    return role && !strcmp(role, expected);
}
static void event(const char *name, int fd) {
    const char *root = getenv("B60_NONCE_CONTROL");
    const char *role = getenv("B60_NONCE_ROLE");
    char temporary[PATH_MAX], destination[PATH_MAX], record[160];
    struct stat st;
    if (!root || !role || fstat(fd, &st)) _exit(110);
    int a = snprintf(temporary, sizeof temporary, "%s/%s-%s.tmp", root, role, name);
    int b = snprintf(destination, sizeof destination, "%s/%s-%s", root, role, name);
    int n = snprintf(record, sizeof record, "%ld %llu %llu %lld\n", (long)getpid(),
                     (unsigned long long)st.st_dev, (unsigned long long)st.st_ino,
                     (long long)st.st_size);
    if (a < 0 || b < 0 || n <= 0 || a >= (int)sizeof temporary || b >= (int)sizeof destination || n >= (int)sizeof record) _exit(111);
    int out = open(temporary, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (out < 0) _exit(112);
    for (int offset = 0; offset < n;) {
        ssize_t count = write(out, record + offset, (size_t)(n - offset));
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) _exit(113);
        offset += (int)count;
    }
    if (close(out) || rename(temporary, destination)) _exit(114);
}
static void boundary(const char *phase, int fd) {
    event(phase, fd);
    const char *requested = getenv("B60_NONCE_PHASE");
    if (requested && !strcmp(requested, phase) && raise(SIGSTOP)) _exit(115);
}
static int observed_fcntl(int fd, int command, ...) {
    if (command == F_FULLFSYNC) {
        char path[PATH_MAX];
        int target = role_is("writer") && !fcntl(fd, F_GETPATH, path);
        const char *leaf = target ? strrchr(path, '/') : NULL;
        target = leaf && !strcmp(leaf, "/.consumed_nonces.bin");
        if (target) boundary("before-sync", fd);
        int result = fcntl(fd, command);
        int saved_errno = errno;
        if (target && !result) boundary("after-sync", fd);
        errno = saved_errno;
        return result;
    }
    /* Forward only known argument types; fail visibly instead of guessing a vararg. */
    if (command == F_GETFD || command == F_GETFL || command == F_GETOWN) return fcntl(fd, command);
    if (command == F_GETPATH) {
        va_list args;
        va_start(args, command);
        char *path = va_arg(args, char *);
        va_end(args);
        return fcntl(fd, command, path);
    }
    if (command == F_SETFD || command == F_SETFL || command == F_SETOWN ||
        command == F_DUPFD || command == F_DUPFD_CLOEXEC) {
        va_list args;
        va_start(args, command);
        int argument = va_arg(args, int);
        va_end(args);
        return fcntl(fd, command, argument);
    }
    dprintf(STDERR_FILENO, "unsupported fcntl in nonce fixture: %d\n", command);
    _exit(116);
}
static int observed_flock(int fd, int operation) {
    int observe = role_is("observer") && operation == LOCK_EX && ++observer_gates == 2;
    if (observe) event("waiting", fd);
    int result = flock(fd, operation);
    int saved_errno = errno;
    if (observe && !result) event("acquired", fd);
    errno = saved_errno;
    return result;
}
#define INTERPOSE(replacement, original) \
    __attribute__((used)) static struct { const void *new_fn; const void *old_fn; } \
    interpose_##original __attribute__((section("__DATA,__interpose"))) = \
    { (const void *)&replacement, (const void *)&original }
INTERPOSE(observed_fcntl, fcntl);
INTERPOSE(observed_flock, flock);
