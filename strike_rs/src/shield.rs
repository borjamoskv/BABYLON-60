/// █ OPSEC MEMORY SHIELD PROTOCOL (C5-REAL)
///
/// Implements early process isolation (Anti-debugging via PT_DENY_ATTACH, 
/// Anti-coredump via RLIMIT_CORE) to protect keys and sensitive structs in RAM.
/// Translates the C5-REAL Python doctrine into safe Rust bindings for macOS.

#[cfg(target_os = "macos")]
pub fn ignite_memory_shield() {
    use std::process;

    // 1. Core Dump Deactivation (RLIMIT_CORE to 0)
    let limit = libc::rlimit {
        rlim_cur: 0,
        rlim_max: 0,
    };
    
    let res_core = unsafe { libc::setrlimit(libc::RLIMIT_CORE, &limit) };
    if res_core != 0 {
        process::abort();
    }

    // 2. Syscall Anti-Attach (PT_DENY_ATTACH)
    // 31 is PT_DENY_ATTACH on macOS
    let res_ptrace = unsafe { libc::ptrace(31, 0, std::ptr::null_mut(), 0) };
    
    // 3. FAIL-FAST
    if res_ptrace != 0 {
        unsafe {
            libc::kill(libc::getpid(), libc::SIGKILL);
        }
    }
}

#[cfg(target_os = "linux")]
pub fn ignite_memory_shield() {
    use std::process;

    // 1. Core Dump Deactivation (RLIMIT_CORE to 0)
    let limit = libc::rlimit {
        rlim_cur: 0,
        rlim_max: 0,
    };
    
    let res_core = unsafe { libc::setrlimit(libc::RLIMIT_CORE, &limit) };
    if res_core != 0 {
        process::abort();
    }

    // 2. Dumpable deactivation (PR_SET_DUMPABLE = 0)
    let res_prctl = unsafe { libc::prctl(libc::PR_SET_DUMPABLE, 0, 0, 0, 0) };
    if res_prctl != 0 {
        unsafe {
            libc::kill(libc::getpid(), libc::SIGKILL);
        }
    }
}

#[cfg(not(any(target_os = "macos", target_os = "linux")))]
pub fn ignite_memory_shield() {
    // Fail-fast on unsupported platforms to ensure strict compliance
    std::process::abort();
}
