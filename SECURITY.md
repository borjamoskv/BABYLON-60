# BABYLON-60 Security Policy & Threat Model

BABYLON-60 and the C5-REAL Sovereign Trust Substrate follow an immutable Fail-Closed Architecture principle. We enforce cryptographic verification, C-ABI cache-line isolation, and zero stochastic privilege escalation (`AX-0`).

## Supported Versions

| Version  | Status             | Security Maintenance |
| :------- | :----------------- | :------------------- |
| `v5.x`   | :white_check_mark: | Active (Ring-0/1/2)  |
| `v4.x`   | :white_check_mark: | Maintenance (Kernel) |
| `< v4.0` | :x:                | End of Life          |

## Formal Threat Model

BABYLON-60 enforces deterministic boundaries against four canonical threat classes:
1. **Stochastic Agent Hijacking (Ring-2 Compromise):** LLMs or subagents generating arbitrary shell strings or attempting self-authorization. Mitigated by `AX-0` (stochastic clients cannot authorize irreversible side effects), strict AST sandboxing, and token filters.
2. **Memory & Concurrency Attacks (Ring-0 Race Conditions):** Multi-threaded or multi-process race conditions attempting torn reads or seqlock sequence poisoning. Mitigated by `KUDURRU-64` cache-line alignment (`align(64)`), CAS seqlock synchronization, and memory barriers (`dmb ishld` / `fence(Release)`).
3. **Supply Chain & CI/CD Tampering:** Malicious dependencies or compromised action tags. Mitigated by `uv.lock` / `Cargo.lock` cryptographic pinning, least-privilege CI tokens (`permissions: contents: read`), and strict linting (`deny(unsafe_op_in_unsafe_fn)`).
4. **Hardware & Side-Channel Tampering:** Physical access or timing observation. Mitigated by constant-time cryptographic equality comparisons, zero-reuse biometric gates (`Touch ID`), and hardware-enclave-backed signing.

## Coordinated Vulnerability Disclosure (CVD)

If you discover a security vulnerability or invariant deviation within BABYLON-60:
- **Email:** `borja@babylon60.com` or `security@babylon60.com`
- **PGP/Encrypted:** Available upon request.
- **Protocol:** Please **DO NOT** disclose vulnerabilities in public GitHub issues or forums prior to remediation.

### Response Timelines (150/100 Protocol)
- **Triage & Acknowledgment:** Within **24 hours**.
- **Root Cause & Patch Strategy:** Within **72 hours**.
- **Coordinated Advisory & CVE:** Following validated release and tag.

## Emergency Apoptosis & Key Rotation

In the event of an attested Ring-0 key compromise or catastrophic invariant violation:
1. The emergency opcode `0xDEAD_6060` (`MUSHUSHU-0`) triggers immediate memory poisoning on `SharedManifest.status_flag`, closing all write admissions.
2. Operators execute offline key rotation via Apple Secure Enclave re-pairing.
3. The state trailer is anchored to persistent storage with an explicit `PersistenceFailed` or `SignedDurable` receipt.
