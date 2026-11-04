//! Canonical binary serialization LP(x) and dual digest computation (SHA-256).
//! Law O1, INV_C5_CANONICAL_LOGICAL_TICK & FL-027 v3:
//! Separates content_digest I_content from event_digest I_event.
//! Physical wall-clock timestamps are excluded from canonical event identity.

use sha2::{Digest, Sha256};
use std::fmt::Write;

pub struct SourcePreimageInput<'a> {
    pub provider: &'a str,
    pub conversation_id: &'a str,
    pub message_id: &'a str,
    pub timestamp_original: &'a str,
    pub role: &'a str,
    pub raw_bytes: &'a [u8],
}

pub struct EventIdentityInput<'a> {
    pub namespace: &'a str,
    pub conversation_id: &'a str,
    pub message_id: &'a str,
    pub revision: u64,
    pub logical_tick: u64,
}

#[inline]
fn bytes_to_hex(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        let _ = write!(s, "{:02x}", b);
    }
    s
}

/// Serializes with 64-bit big-endian length prefix: LP(x) = len(x)_64BE || x
#[inline]
pub fn write_lp(buf: &mut Vec<u8>, data: &[u8]) {
    let len = (data.len() as u64).to_be_bytes();
    buf.extend_from_slice(&len);
    buf.extend_from_slice(data);
}

/// Computes canonical event identity I_event excluding physical timestamps (INV_C5_CANONICAL_LOGICAL_TICK).
pub fn compute_event_identity(input: EventIdentityInput) -> String {
    let mut preimage = Vec::with_capacity(128);
    preimage.extend_from_slice(b"CORTEX-EVENT-v3\0");
    write_lp(&mut preimage, input.namespace.as_bytes());
    write_lp(&mut preimage, input.conversation_id.as_bytes());
    write_lp(&mut preimage, input.message_id.as_bytes());
    preimage.extend_from_slice(&input.revision.to_le_bytes());
    preimage.extend_from_slice(&input.logical_tick.to_le_bytes());

    let mut hasher = Sha256::new();
    hasher.update(&preimage);
    format!("sha256:{}", bytes_to_hex(&hasher.finalize()))
}

/// Computes both content_digest and source_digest under CORTEX-SOURCE-v1 canonical wire format.
/// Label accurately reflects the underlying SHA-256 primitive (`sha256:`).
pub fn compute_digests(input: SourcePreimageInput) -> (String, String) {
    // 1. content_digest = "sha256:" + hex(SHA256(raw_bytes))
    let mut hasher = Sha256::new();
    hasher.update(input.raw_bytes);
    let content_digest = format!("sha256:{}", bytes_to_hex(&hasher.finalize()));

    // 2. source_preimage = UTF8("CORTEX-SOURCE-v1") + 0x00 + LP(provider) + ... + LP(raw_bytes)
    let mut preimage = Vec::with_capacity(256 + input.raw_bytes.len());
    preimage.extend_from_slice(b"CORTEX-SOURCE-v1\0");
    write_lp(&mut preimage, input.provider.as_bytes());
    write_lp(&mut preimage, input.conversation_id.as_bytes());
    write_lp(&mut preimage, input.message_id.as_bytes());
    write_lp(&mut preimage, input.timestamp_original.as_bytes());
    write_lp(&mut preimage, input.role.as_bytes());
    write_lp(&mut preimage, input.raw_bytes);

    let mut hasher = Sha256::new();
    hasher.update(&preimage);
    let source_digest = format!("sha256:{}", bytes_to_hex(&hasher.finalize()));

    (content_digest, source_digest)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lp_and_double_hash_invariants() {
        let raw = b"Reversible Landauer memory archaeology";
        let in1 = SourcePreimageInput {
            provider: "openai",
            conversation_id: "conv_123",
            message_id: "msg_456",
            timestamp_original: "2024-01-01T12:00:00Z",
            role: "user",
            raw_bytes: raw,
        };
        let (c1, s1) = compute_digests(in1);

        // Same content, different role
        let in2 = SourcePreimageInput {
            provider: "openai",
            conversation_id: "conv_123",
            message_id: "msg_456",
            timestamp_original: "2024-01-01T12:00:00Z",
            role: "assistant",
            raw_bytes: raw,
        };
        let (c2, s2) = compute_digests(in2);

        assert_eq!(c1, c2, "content_digest must be identical for identical raw bytes");
        assert_ne!(s1, s2, "source_digest must differ when role differs");
        assert!(c1.starts_with("sha256:"));
        assert!(s1.starts_with("sha256:"));
    }

    #[test]
    fn test_event_identity_excludes_physical_clock() {
        let ev_a = compute_event_identity(EventIdentityInput {
            namespace: "ChatGPT",
            conversation_id: "conv_feb_24",
            message_id: "msg_01",
            revision: 1,
            logical_tick: 42,
        });
        let ev_b = compute_event_identity(EventIdentityInput {
            namespace: "Antigravity",
            conversation_id: "conv_feb_24",
            message_id: "msg_01",
            revision: 1,
            logical_tick: 42,
        });
        assert!(ev_a.starts_with("sha256:"));
        assert_ne!(ev_a, ev_b, "Distinct namespaces must yield distinct event identities");
    }
}
