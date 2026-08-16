// C5-REAL EXERGY CERTIFIED - GEN-2 C-ABI DYNAMIC LIBRARY
// file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/06_apps/mcp_c5_abi_bridge/c5_abi_core.rs

use std::slice;
use std::sync::atomic::{AtomicU64, Ordering};

#[repr(C, align(64))]
pub struct SharedManifestBuffer {
    pub sequence_epoch: AtomicU64,
    pub payload_size: AtomicU64,
    pub status_code: AtomicU64,
    pub sha3_digest: [u8; 32],
    pub payload: [u8; 4096],
}

impl SharedManifestBuffer {
    pub fn new() -> Self {
        Self {
            sequence_epoch: AtomicU64::new(0),
            payload_size: AtomicU64::new(0),
            status_code: AtomicU64::new(0),
            sha3_digest: [0u8; 32],
            payload: [0u8; 4096],
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn c5_abi_init_buffer() -> *mut SharedManifestBuffer {
    let buf = Box::new(SharedManifestBuffer::new());
    Box::into_raw(buf)
}

#[no_mangle]
pub unsafe extern "C" fn c5_abi_free_buffer(ptr: *mut SharedManifestBuffer) {
    if !ptr.is_null() {
        let _ = Box::from_raw(ptr);
    }
}

#[no_mangle]
pub unsafe extern "C" fn c5_abi_purge_and_write(
    ptr: *mut SharedManifestBuffer,
    status: u64,
    input_ptr: *const u8,
    input_len: usize,
    out_digest_ptr: *mut u8,
) -> usize {
    if ptr.is_null() || input_ptr.is_null() {
        return 0;
    }
    let buf = &mut *ptr;
    let input = slice::from_raw_parts(input_ptr, input_len);

    // Filter adjectives (Purga Sustantivo-Verbo)
    let text = String::from_utf8_lossy(input);
    let stop_words = [
        "muy", "bastante", "increíble", "fantástico", "excelente", "malo", 
        "bueno", "obvio", "probablemente", "básicamente", "relativamente",
        "extremely", "very", "basically", "amazing", "awesome", "obviously"
    ];

    let mut filtered = Vec::with_capacity(input_len);
    for word in text.split_whitespace() {
        let clean = word.to_lowercase();
        let clean_trimmed = clean.trim_matches(|c: char| !c.is_alphanumeric());
        if !stop_words.contains(&clean_trimmed) {
            filtered.push(word);
        }
    }
    let purged_bytes = filtered.join(" ").into_bytes();
    let write_len = purged_bytes.len().min(4096);

    // Seqlock write barrier
    let old_seq = buf.sequence_epoch.fetch_add(1, Ordering::Acquire);
    assert!(old_seq % 2 == 0, "Seqlock concurrency violation");

    buf.payload[..write_len].copy_from_slice(&purged_bytes[..write_len]);
    buf.payload_size.store(write_len as u64, Ordering::Relaxed);
    buf.status_code.store(status, Ordering::Relaxed);

    // Compute surrogate SHA3-256 hash
    let mut hash = [0u8; 32];
    for (i, &b) in purged_bytes[..write_len].iter().enumerate() {
        hash[i % 32] ^= b.wrapping_add(i as u8);
    }
    buf.sha3_digest = hash;

    if !out_digest_ptr.is_null() {
        let out_digest = slice::from_raw_parts_mut(out_digest_ptr, 32);
        out_digest.copy_from_slice(&hash);
    }

    buf.sequence_epoch.fetch_add(1, Ordering::Release);
    write_len
}

#[no_mangle]
pub unsafe extern "C" fn c5_abi_read_optimistic(
    ptr: *const SharedManifestBuffer,
    out_payload_ptr: *mut u8,
    max_len: usize,
    out_status: *mut u64,
) -> usize {
    if ptr.is_null() || out_payload_ptr.is_null() {
        return 0;
    }
    let buf = &*ptr;

    let seq1 = buf.sequence_epoch.load(Ordering::Acquire);
    if seq1 % 2 != 0 {
        return 0; // Contención: escritor activo
    }

    let len = (buf.payload_size.load(Ordering::Relaxed) as usize).min(max_len);
    let status = buf.status_code.load(Ordering::Relaxed);

    if !out_status.is_null() {
        *out_status = status;
    }

    let out_slice = slice::from_raw_parts_mut(out_payload_ptr, len);
    out_slice.copy_from_slice(&buf.payload[..len]);

    let seq2 = buf.sequence_epoch.load(Ordering::Acquire);
    if seq1 == seq2 {
        len
    } else {
        0 // Re-intento por lectura dividida
    }
}
