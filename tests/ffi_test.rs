// C5-REAL EXERGY CERTIFIED — BABYLON-60 — C FFI BINDINGS INTEGRATION TEST

#![cfg(not(loom))]

use babylon_60::ffi::*;
use babylon_60::manifest::SharedManifest;
use std::mem::MaybeUninit;

#[test]
fn test_c_ffi_lifecycle() {
    let mut manifest_uninit = MaybeUninit::<SharedManifest>::uninit();
    let m_ptr = manifest_uninit.as_mut_ptr();

    unsafe {
        assert!(babylon60_manifest_init(m_ptr));

        assert!(!babylon60_is_halted(m_ptr));

        let hash = [0x1111u64, 0x2222u64, 0x3333u64, 0x4444u64];
        assert!(babylon60_publish(m_ptr, 100, hash.as_ptr()));

        let mut out_epoch = 0u64;
        let mut out_hash = [0u64; 4];
        assert!(babylon60_read(m_ptr, &mut out_epoch, out_hash.as_mut_ptr()));

        assert_eq!(out_epoch, 100);
        assert_eq!(out_hash, hash);
    }
}
