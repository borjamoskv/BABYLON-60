#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import signal

# Sovereign whitelist of allowed remote domains, hosts, and local services
# We allow:
# - Loopback connections (localhost, 127.0.0.1, ::1) for NATS, Neo4j, etc.
# - DNS queries (port 53)
# - Standard local subnets (192.168.x.x, 10.x.x.x, 172.16.x.x)
# - Valid Gemini API or Google domains for model execution
# - Safe HTTPS domains (GitHub/Git operations)
WHITELIST_PATTERNS = [
    r"^127\.\d+\.\d+\.\d+",
    r"^::1$",
    r"^localhost$",
    r"^192\.168\.",
    r"^10\.",
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
    r":53$", # DNS
]

# Process whitelist (processes that are allowed to make outgoing connections)
WHITELIST_PROCESSES = {
    "git",
    "curl",
    "wget",
    "python",
    "python3",
    "node",
    "go",
    "zsh",
    "bash",
    "ssh",
}

def get_active_connections():
    """
    Executes 'lsof -i -P -n' to capture active TCP/UDP connections.
    """
    try:
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"[V-OMEGA] Error running lsof: {e}", file=sys.stderr)
        return []

def audit_connections(kill_violators=False):
    lines = get_active_connections()
    if not lines:
        return 0

    violations = 0
    # Header is: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
    # Example: node 1234 user 5u IPv4 0x... 0t0 TCP 127.0.0.1:4222 (ESTABLISHED)
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        
        command = parts[0]
        pid = int(parts[1])
        connection_type = parts[4] # IPv4 or IPv6
        name = parts[8] # e.g. 127.0.0.1:4222 or *:53 or 104.18.23.41:443
        
        # Extract IP/Host and Port
        match = re.match(r"^(.*?):(\d+|\*)$", name)
        if not match:
            continue
        
        ip_host, port = match.groups()
        
        # Check if local loopback or allowed network pattern
        is_whitelisted = False
        if ip_host == "*" or ip_host == "localhost":
            is_whitelisted = True
        else:
            for pattern in WHITELIST_PATTERNS:
                if re.match(pattern, ip_host):
                    is_whitelisted = True
                    break
        
        # Check if process itself is explicitly whitelisted for external calls
        if not is_whitelisted:
            if command.lower() in WHITELIST_PROCESSES:
                is_whitelisted = True
        
        if not is_whitelisted:
            violations += 1
            print(f"[V-OMEGA] VIOLATION: Process '{command}' (PID: {pid}) connected to '{name}' is not whitelisted.")
            if kill_violators:
                try:
                    print(f"[V-OMEGA] Apoptosis Triggered: Terminating PID {pid}...")
                    os.kill(pid, signal.SIGKILL)
                    print(f"[V-OMEGA] PID {pid} terminated successfully.")
                except ProcessLookupError:
                    pass
                except PermissionError:
                    print(f"[V-OMEGA] Error: Insufficient permissions to terminate PID {pid}.", file=sys.stderr)
                    
    return violations

if __name__ == "__main__":
    kill_mode = "--kill" in sys.argv
    print("[V-OMEGA] Starting Network Zero-Trust Shield audit...")
    violation_count = audit_connections(kill_violators=kill_mode)
    print(f"[V-OMEGA] Audit complete. Violations found: {violation_count}")
    sys.exit(violation_count)
