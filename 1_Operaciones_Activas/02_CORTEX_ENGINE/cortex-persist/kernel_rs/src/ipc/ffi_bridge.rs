// C5-REAL EXERGY CERTIFIED
use std::os::unix::io::RawFd;
use std::ptr;

// Re-exportar tipos del módulo ebr (asumido en el mismo crate)
use crate::ipc::ebr::{EpochState, SharedManifest};

/// Tamaño del segmento de memoria compartida requerido.
pub const SHARED_MEM_SIZE: usize = std::mem::size_of::<EpochState>();

/// Mapea un file descriptor de memoria compartida y retorna puntero a EpochState.
/// # Safety
/// - `fd` debe ser un FD válido de memoria compartida (shm_open / memfd_create).
/// - El segmento debe tener al menos SHARED_MEM_SIZE bytes.
/// - El llamador garantiza que ningún otro proceso está inicializando simultáneamente.
/// - El puntero retornado NO debe ser liberado con free; solo con munmap.
#[no_mangle]
pub unsafe extern "C" fn init_shared_memory(fd: RawFd) -> *mut EpochState {
    let addr = libc::mmap(
        ptr::null_mut(),
        SHARED_MEM_SIZE,
        libc::PROT_READ | libc::PROT_WRITE,
        libc::MAP_SHARED,
        fd,
        0,
    );

    if addr == libc::MAP_FAILED {
        return ptr::null_mut();
    }

    // Verificar alineación de 8 bytes (debería estar garantizada por mmap en x86_64)
    if (addr as usize) % 8 != 0 {
        libc::munmap(addr, SHARED_MEM_SIZE);
        return ptr::null_mut();
    }

    addr as *mut EpochState
}

/// Desmapea el segmento de memoria compartida.
/// # Safety
/// - `state` debe haber sido retornado por init_shared_memory.
/// - No debe haber lectores activos usando el puntero.
#[no_mangle]
pub unsafe extern "C" fn destroy_shared_memory(state: *mut EpochState) {
    if !state.is_null() {
        libc::munmap(state as *mut libc::c_void, SHARED_MEM_SIZE);
    }
}
