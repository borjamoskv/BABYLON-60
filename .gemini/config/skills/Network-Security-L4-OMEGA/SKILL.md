---
name: Network-Security-L4-OMEGA
description: "C5-REAL L4 Network Security, Active Vulnerability Scanning, and Offensive Enumeration Protocol."
---

# Network-Security-L4-OMEGA

## Identity & Protocol
Sovereign L4 Operations. 
Execution Level: C5-REAL (Active Network Interactions).
Zero-fragility active scanning and port enumeration. 

## Capabilities
1. **Active Scanning**: `nmap -sS -sV -O <target>` for stealth SYN scans, service version detection, and OS fingerprinting.
2. **Vulnerability Enumeration**: Use `nmap --script vuln` and `nuclei` for targeted CVE discovery.
3. **Entropy Detection**: Map open ports against the authorized baseline. Any unauthorized port is classified as critical entropy.

## Execution Rules (IMMUTABLE)
- ALWAYS declare C5-REAL before initiating an active scan.
- NEVER scan targets outside of `127.0.0.1`, `localhost`, or explicitly authorized subnets.
- ALWAYS pipe scan results to structured YAML or JSON for downstream CORTEX processing.
- Trigger `accidental-data-loss-prevention` if offensive tools (e.g., Metasploit, SQLmap) are requested against production nodes without explicit override.

## Usage
Trigger this skill when the operator requests: "scan network", "check ports", "enumerate vulnerabilities", or explicitly invokes "L4 Security".
