"""OS read confinement for terminal agents, with a chained local journal.

Linux uses Landlock (unprivileged LSM); macOS uses Seatbelt via ``sandbox-exec``.
Filesystem paths are confined by Landlock or Seatbelt; on Linux a seccomp filter
also blocks terminal injection, Unix domain sockets and io_uring. Network access,
metadata operations (Linux), already-open descriptors and links created before the
session are declared limits, reported by ``babylon60 demo`` instead of counted as
blocked.
"""
