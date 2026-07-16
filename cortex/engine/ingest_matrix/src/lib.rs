use std::ffi::CStr;
use std::os::raw::c_char;
use sha2::{Sha256, Digest};

#[unsafe(no_mangle)]
pub extern "C" fn process_payload_rust(payload: *const c_char) -> *mut c_char {
    let c_str = unsafe {
        assert!(!payload.is_null());
        CStr::from_ptr(payload)
    };
    let r_str = c_str.to_str().unwrap();
    
    let mut hasher = Sha256::new();
    hasher.update(r_str.as_bytes());
    let hash_result = hasher.finalize();
    
    let out = hex::encode(hash_result);
    // Return to C via leak (caller must free)
    std::ffi::CString::new(out).unwrap().into_raw()
}

#[unsafe(no_mangle)]
pub extern "C" fn free_string_rust(s: *mut c_char) {
    unsafe {
        if s.is_null() { return }
        let _ = std::ffi::CString::from_raw(s);
    }
}
