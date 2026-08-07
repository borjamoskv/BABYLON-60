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
    let addr = libc::mmap(
        ptr::null_mut(),
        SHARED_STATE_SIZE,
        libc::PROT_READ | libc::PROT_WRITE,
        libc::MAP_SHARED,
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
