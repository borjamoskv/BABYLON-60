#!/usr/sbin/dtrace -s
/*
 * DTrace Script: Cowork Sandbox Monitor (M1/M2)
 * C5-REAL Protocol
 */

#pragma D option quiet
#pragma D option switchrate=10hz

/* Capturar ejecuciones de procesos (execve) */
syscall::execve:entry
/execname == "claude" || execname == "node" || execname == "bun"/
{
    printf("\n[M1-BOOTSTRAP] Process Execution Detected:\n");
    printf("PID: %d | PPID: %d | Exec: %s\n", pid, ppid, copyinstr(arg0));
}

/* Rastrear intentos de dlopen (M2 Hook Audit) */
pid$target::dlopen:entry
{
    printf("\n[M2-HOOK] dlopen() intercepted in PID: %d\n", pid);
    printf("Library Target: %s\n", copyinstr(arg0));
    ustack();
}

/* Capturar fallos de permisos (macOS Sandbox / Bubblewrap) */
syscall::open*:return
/arg1 == -1 && errno == EPERM/
{
    printf("\n[M2-SANDBOX] Operation denied by sandbox (EPERM)\n");
    printf("PID: %d | Exec: %s\n", pid, execname);
}
