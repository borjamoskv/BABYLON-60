"""OS read confinement for terminal agents, with a chained local journal.

Linux uses Landlock (unprivileged LSM); macOS uses Seatbelt via ``sandbox-exec``.
The confinement covers filesystem paths only. Network access, Unix sockets with a
path, already-open descriptors and links created before the session are declared
limits, reported by ``babylon60 demo`` instead of counted as blocked.
"""
