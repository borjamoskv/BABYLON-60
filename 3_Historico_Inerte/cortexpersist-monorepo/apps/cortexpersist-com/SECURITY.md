# Security Policy

## Supported Versions

| Package | Version | Supported |
| :--- | :--- | :--- |
| `cortex-persist` | 0.1.x | ✅ |
| `cortex-persist-langchain` | 0.1.x | ✅ |

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Use [GitHub Security Advisories](https://github.com/borjamoskv/Cortex-Persist/security/advisories/new) to report vulnerabilities privately.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

### Response Timeline

| Stage | SLA |
| :--- | :--- |
| Acknowledgment | 48 hours |
| Triage & severity assessment | 5 business days |
| Patch release (Critical/High) | 7 business days |
| Patch release (Medium/Low) | 30 business days |

### Scope

The following are **in scope**:

- Hash chain integrity bypass
- Ed25519 signature forgery or verification bypass
- Ledger entry mutation after append
- Information leakage through timing side-channels
- Dependency confusion attacks

The following are **out of scope**:

- Denial of service via large JSONL files (expected behavior for local storage)
- Issues in the website (`src/`, `index.html`) — these are not part of the SDK

## Contact

security@cortexpersist.com
