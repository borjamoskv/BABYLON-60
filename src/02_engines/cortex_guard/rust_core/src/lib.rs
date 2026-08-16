// C5-REAL EXERGY CERTIFIED
// Zero-Dependency Lock-Free EBR Ring Buffer Core

use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};

// C-ABI alignment to 128 bytes to prevent False Sharing on Apple Silicon L1 cache
#[repr(C, align(128))]
pub struct SharedManifest {
    pub status_flag: AtomicU32, // 0x00
    pub active_readers: AtomicU32, // 0x04
    pub epoch_id: AtomicU64, // 0x08
    pub payload_hash: [u8; 32], // 0x10
    pub _padding: [u8; 80], // 0x30 to 0x7F
}

impl SharedManifest {
    pub const STATUS_IDLE: u32 = 0;
    pub const STATUS_ACTIVE: u32 = 1;
    pub const STATUS_HALT: u32 = 99;
}

#[unsafe(no_mangle)]
pub extern "C" fn init_manifest(manifest_ptr: *mut SharedManifest) {
    if manifest_ptr.is_null() {
        return;
    }
    unsafe {
        (*manifest_ptr).status_flag.store(SharedManifest::STATUS_IDLE, Ordering::Release);
        (*manifest_ptr).active_readers.store(0, Ordering::Release);
        (*manifest_ptr).epoch_id.store(0, Ordering::Release);
        for i in 0..32 {
            (*manifest_ptr).payload_hash[i] = 0;
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn read_manifest_seqlock(manifest_ptr: *const SharedManifest, out_hash: *mut u8) -> u32 {
    if manifest_ptr.is_null() || out_hash.is_null() {
        return 1; // Error
    }

    unsafe {
        let manifest = &*manifest_ptr;
        let mut retries = 0;
        
        loop {
            // Spin-wait mechanism for odd epochs (producer is writing)
            let mut epoch1;
            loop {
                epoch1 = manifest.epoch_id.load(Ordering::Acquire);
                if epoch1 % 2 == 0 {
                    break;
                }
                retries += 1;
                if retries > 100_000 {
                    // Deadlock / EpistemicHalt scenario
                    return 2; 
                }
                std::hint::spin_loop();
            }

            // Register active reader
            manifest.active_readers.fetch_add(1, Ordering::Release);

            // Read the non-atomic payload
            let mut local_hash = [0u8; 32];
            local_hash.copy_from_slice(&manifest.payload_hash);

            manifest.active_readers.fetch_sub(1, Ordering::Release);

            // Verify if sequence mutated during our read
            let epoch2 = manifest.epoch_id.load(Ordering::Acquire);
            
            if epoch1 == epoch2 {
                // Success, write to out pointer
                std::ptr::copy_nonoverlapping(local_hash.as_ptr(), out_hash, 32);
                return 0; // Success
            }
            
            // Torn read detected, loop again
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn force_epistemic_halt(manifest_ptr: *mut SharedManifest) {
    if manifest_ptr.is_null() {
        return;
    }
    unsafe {
        (*manifest_ptr).status_flag.store(SharedManifest::STATUS_HALT, Ordering::Release);
    }
    // Logic for SCITT Receipt generation will be added here
}
