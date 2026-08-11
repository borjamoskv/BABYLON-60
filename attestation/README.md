# 🛡️ BABYLON-60 Causal Attestation (`attestation/`)

[![Rust Crate](https://img.shields.io/badge/Rust-Crate-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![TPM 2.0](https://img.shields.io/badge/TPM_2.0-PCR_Anchoring-blue?style=for-the-badge)]()
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Art_10_Governance-purple?style=for-the-badge)](../docs/04_research/eu_ai_act_compliance_whitepaper.md)

The **Attestation Module** (`attestation`) is a high-assurance Rust component responsible for anchoring the BABYLON-60 state vector root into hardware enclave PCR quotes (TPM 2.0) and external notary blockchains / Git Sentinels.

---

## 🎯 Features

- **Merkle DAG State Anchoring (`merkle_anchor.rs`)**: Computes SHA-256 root digests of execution state and anchors them to external immutable witnesses.
- **Hardware Security Enclave Integration**: Bridges state transitions with TPM 2.0 Platform Configuration Registers (PCRs) to guarantee zero post-hoc log alteration.
- **P2P Notary Verification**: Inter-node verification protocols to detect and reject non-deterministic agent execution branches.

---

## 🛠️ Usage

```rust
use babylon60_attestation::merkle_anchor::anchor_state_root;

fn main() {
    let state_root: [u8; 32] = [0u8; 32];
    match anchor_state_root(&state_root) {
        Ok(receipt) => println!("State root anchored: {}", receipt),
        Err(err) => eprintln!("Attestation failed: {}", err),
    }
}
```

---

## 🧪 Testing

```bash
cargo test -p babylon60_attestation
```

---

<sub>BABYLON-60 Attestation Substrate · Hardware PCR Notary · Borja Moskv</sub>
