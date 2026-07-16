use std::slice;
use std::os::raw::c_char;
use sha2::{Sha256, Digest};
use rayon::prelude::*;

// Keep the old FFI for backward compatibility (Phase 3)
#[unsafe(no_mangle)]
pub extern "C" fn process_payload_rust(payload: *const c_char) -> *mut c_char {
    let c_str = unsafe { std::ffi::CStr::from_ptr(payload) };
    let mut hasher = Sha256::new();
    hasher.update(c_str.to_bytes());
    let out = hex::encode(hasher.finalize());
    std::ffi::CString::new(out).unwrap().into_raw()
}

#[unsafe(no_mangle)]
pub extern "C" fn free_string_rust(s: *mut c_char) {
    unsafe { if !s.is_null() { let _ = std::ffi::CString::from_raw(s); } }
}

// PHASE 4: ZERO-COPY MMAP BFT CONSENSUS
#[unsafe(no_mangle)]
pub extern "C" fn process_mmap_rust(in_ptr: *const u8, out_ptr: *mut u8, num_records: usize, record_size: usize, hash_size: usize) {
    // We treat the input as a massive contiguous byte slice
    let in_slice = unsafe { slice::from_raw_parts(in_ptr, num_records * record_size) };
    let out_slice = unsafe { slice::from_raw_parts_mut(out_ptr, num_records * hash_size) };

    // Parallel chunk processing using Rayon
    in_slice.par_chunks_exact(record_size)
        .zip(out_slice.par_chunks_exact_mut(hash_size))
        .for_each(|(in_chunk, out_chunk)| {
            let mut hasher = Sha256::new();
            hasher.update(in_chunk);
            let result = hasher.finalize();
            // result is 32 bytes, we write it directly to the output buffer
            out_chunk.copy_from_slice(&result);
        });
}
