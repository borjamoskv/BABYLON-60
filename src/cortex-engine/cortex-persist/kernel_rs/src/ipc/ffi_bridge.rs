// C5-REAL EXERGY CERTIFIED
// ffi_bridge.rs — Implementación axiomáticamente verificable
#![allow(unsafe_op_in_unsafe_fn)]
use std::os::raw::{c_int, c_void};
use std::ptr;
use std::sync::atomic::Ordering;

use crate::ipc::ebr::EpochState;

pub const SHARED_STATE_SIZE: usize = std::mem::size_of::<EpochState>();

/// AXIOMA 3: Mapeo sin inicialización. Estado es ⊥ hasta initialize_epoch_state.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn init_shared_memory(fd: c_int) -> *mut EpochState {
    let flags = if fd < 0 {
        libc::MAP_SHARED | libc::MAP_ANONYMOUS
    } else {
        libc::MAP_SHARED
    };
    let addr = libc::mmap(
        ptr::null_mut(),
        SHARED_STATE_SIZE,
        libc::PROT_READ | libc::PROT_WRITE,
        flags,
        fd,
        0,
    );
    if addr == libc::MAP_FAILED {
        return ptr::null_mut();
    }
    debug_assert_eq!(addr as usize % 8, 0); // AXIOMA 1: alineación
    addr as *mut EpochState
}

/// AXIOMA 3: Constructor in-place determinista sobre memoria externa.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn initialize_epoch_state(ptr: *mut EpochState) {
    if ptr.is_null() { return; }
    (*ptr).active_epoch_ptr.store(ptr::null_mut(), Ordering::Release);
    (*ptr).stable_fallback_ptr.store(ptr::null_mut(), Ordering::Release);
    (*ptr).global_epoch_counter.store(0, Ordering::Release);
}

/// AXIOMA 2 + AXIOMA 7: Lectura con Acquire fence, sin efectos secundarios.
/// Retorna 1 si válido, 0 si nulo. Valores por copia, no por puntero expuesto.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn read_active_epoch_safe(
    state: *const EpochState,
    out_epoch_id: *mut u64,
    out_timestamp_ns: *mut u64,
) -> i32 {
    if state.is_null() || out_epoch_id.is_null() || out_timestamp_ns.is_null() {
        return 0;
    }
    // AXIOMA 2: Acquire garantiza happens-before en TODAS las arquitecturas
    let manifest_ptr = (*state).active_epoch_ptr.load(Ordering::Acquire);
    if manifest_ptr.is_null() {
        *out_epoch_id = 0;
        *out_timestamp_ns = 0;
        return 0;
    }
    // AXIOMA 7: Solo lecturas, ninguna escritura
    *out_epoch_id = (*manifest_ptr).epoch_id;
    *out_timestamp_ns = (*manifest_ptr).timestamp_ns;
    1
}

/// AXIOMA 4: Liberación solo válida en mismo espacio de direcciones.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn destroy_shared_memory(ptr: *mut EpochState) {
    if !ptr.is_null() {
        libc::munmap(ptr as *mut c_void, SHARED_STATE_SIZE);
    }
}

/// AXIOMA 3: Transición atómica expuesta a Python. Devuelve epoch_id o -HaltReason.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn commit_epoch_transition(
    state: *const EpochState,
    manifest: *mut crate::ipc::ebr::SharedManifest,
    digest: *const u8,
    raw_text: *const u8,
    text_len: usize,
) -> i64 {
    if state.is_null() || manifest.is_null() || digest.is_null() {
        return -2; // HaltReason::NullPointer
    }

    let expected_digest = &*(digest as *const [u8; 32]);
    let epoch_state = &*state;

    match epoch_state.commit_transition(manifest, expected_digest, raw_text, text_len) {
        Ok(epoch_id) => epoch_id as i64,
        Err(halt) => -(halt.reason as i64),
    }
}

/// AXIOMA 7: Helper FFI para retener lectura (EBR Stress Test).
#[unsafe(no_mangle)]
pub unsafe extern "C" fn acquire_reader_ffi(manifest: *mut crate::ipc::ebr::SharedManifest) {
    if !manifest.is_null() {
        unsafe { (*manifest).acquire_reader(); }
    }
}

/// AXIOMA 7: Helper FFI para liberar lectura (EBR Stress Test).
#[unsafe(no_mangle)]
pub unsafe extern "C" fn release_reader_ffi(manifest: *mut crate::ipc::ebr::SharedManifest) {
    if !manifest.is_null() {
        unsafe { (*manifest).release_reader(); }
    }
}
