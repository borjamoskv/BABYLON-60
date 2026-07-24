/// █ OPSEC MEMORY SHIELD PROTOCOL (C5-REAL)
/// Translates the C5-REAL Python doctrine into safe Rust bindings for macOS.
#[cfg(target_os = "macos")]
pub fn ignite_memory_shield() {
    use std::process;

    let limit = libc::rlimit {
        rlim_cur: 0,
        rlim_max: 0,
    };
    
    let res_core = unsafe { libc::setrlimit(libc::RLIMIT_CORE, &limit) };
    if res_core != 0 {
        process::abort();
    }

    let res_ptrace = unsafe { libc::ptrace(31, 0, std::ptr::null_mut(), 0) };
    
    if res_ptrace != 0 {
        unsafe {
            libc::kill(libc::getpid(), libc::SIGKILL);
        }
    }
}

#[cfg(target_os = "linux")]
pub fn ignite_memory_shield() {
    use std::process;

    let limit = libc::rlimit {
        rlim_cur: 0,
        rlim_max: 0,
    };
    
    let res_core = unsafe { libc::setrlimit(libc::RLIMIT_CORE, &limit) };
    if res_core != 0 {
        process::abort();
    }

    let res_prctl = unsafe { libc::prctl(libc::PR_SET_DUMPABLE, 0, 0, 0, 0) };
    if res_prctl != 0 {
        unsafe {
            libc::kill(libc::getpid(), libc::SIGKILL);
        }
    }
}

#[cfg(not(any(target_os = "macos", target_os = "linux")))]
pub fn ignite_memory_shield() {
    std::process::abort();
}
