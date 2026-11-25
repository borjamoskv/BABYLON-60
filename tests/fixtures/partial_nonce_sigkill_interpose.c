/* Inject a real short append, then stop before write_all can complete it. */
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
static int fired, gates;
static int role_is(const char *expected) {
    const char *role = getenv("B60_PARTIAL_ROLE");
    return role && !strcmp(role, expected);
}
static void event(const char *name, int fd) {
    const char *root = getenv("B60_PARTIAL_CONTROL"), *role = getenv("B60_PARTIAL_ROLE");
    char temporary[PATH_MAX], destination[PATH_MAX], record[160];
    struct stat st;
    if (!root || !role || fstat(fd, &st)) _exit(110);
    int a = snprintf(temporary, sizeof temporary, "%s/%s-%s.tmp", root, role, name);
    int b = snprintf(destination, sizeof destination, "%s/%s-%s", root, role, name);
    int n = snprintf(record, sizeof record, "%ld %llu %llu %lld\n", (long)getpid(),
        (unsigned long long)st.st_dev, (unsigned long long)st.st_ino, (long long)st.st_size);
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
static ssize_t observed_write(int fd, const void *bytes, size_t count) {
    char path[PATH_MAX];
    int target = !fired && role_is("writer") && count == 32 && !fcntl(fd, F_GETPATH, path);
    const char *leaf = target ? strrchr(path, '/') : NULL;
    if (leaf && !strcmp(leaf, "/.consumed_nonces.bin")) {
        const char *requested = getenv("B60_PARTIAL_BYTES");
        int length = requested ? atoi(requested) : 0;
        if (length < 1 || length > 31) _exit(115);
        fired = 1;
        ssize_t result = write(fd, bytes, (size_t)length);
        if (result != length) _exit(116);
        event("partial", fd);
        if (raise(SIGSTOP)) _exit(117);
        return result;
    }
    return write(fd, bytes, count);
}
static int observed_flock(int fd, int operation) {
    int observe = role_is("observer") && operation == LOCK_EX && ++gates == 2;
    if (observe) event("waiting", fd);
    int result = flock(fd, operation), saved_errno = errno;
    if (observe && !result) event("acquired", fd);
    errno = saved_errno;
    return result;
}
#define INTERPOSE(replacement, original) \
    __attribute__((used)) static struct { const void *new_fn; const void *old_fn; } \
    interpose_##original __attribute__((section("__DATA,__interpose"))) = \
    { (const void *)&replacement, (const void *)&original }
INTERPOSE(observed_write, write);
INTERPOSE(observed_flock, flock);
