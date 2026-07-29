# BABYLON-60 Cryptographic Profile

## 1. Official Algorithms

| Component | Algorithm | Input | Encoding | Version |
| :--- | :--- | :--- | :--- | :--- |
| **Object ID** | SHA3-256 | `type_prefix` + CBOR | Deterministic CBOR | v1 |
| **Event ID** | SHA3-256 | Canonical event | Deterministic CBOR | v1 |
| **Chain Root** | SHA3-256 | `previous_root` + `event_ID` | Length-prefixed bytes | v1 |
| **Merkle Parent** | SHA3-256 | `domain_tag` + `left` + `right`| Fixed binary | v1 |
| **Timestamp** | Integer (ms) | UTC | Unsigned integer | v1 |

## 2. Domain Separation Tags

To prevent second-preimage attacks across different contexts, all Merkle tree nodes use a domain tag:
- **Leaf Node Tag:** `0x00`
- **Internal Node Tag:** `0x01`

## 3. Serialization Rules

Events MUST be serialized using Deterministic CBOR before hashing:
- Map keys must be sorted strictly by byte value.
- Integers must be encoded in the smallest possible representation.
- Strings must be UTF-8.

## 4. Hash Chain vs Merkle Tree

- **Hash Chain:** Used for linear sequential logging within a single tenant/agent stream. This is the `Chain Root`.
- **Merkle Tree:** Used for creating global snapshot roots across multiple streams/tenants at specific checkpoints. This uses `Merkle Parent`.
