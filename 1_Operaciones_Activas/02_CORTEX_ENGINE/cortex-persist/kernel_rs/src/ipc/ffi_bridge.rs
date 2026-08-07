// C5-REAL EXERGY CERTIFIED
use std::os::raw::{c_int, c_void};
use std::ptr;

// Asumiendo que ebr.rs está en el mismo crate y exporta estos tipos.
use crate::ipc::ebr::{EpochState, SharedManifest};

/// Tamaño exacto del segmento de control requerido.
pub const SHARED_STATE_SIZE: usize = std::mem::size_of::<EpochState>();

/// Inicializa el acceso al estado compartido vía File Descriptor.
/// Mapea el FD en el espacio de direcciones actual y retorna un puntero tipado.
///
/// # Safety
/// - `fd` debe ser un descriptor de archivo válido apuntando a memoria compartida.
/// - El tamaño del objeto subyacente al FD debe ser >= SHARED_STATE_SIZE.
/// - El llamador es responsable de asegurar que la memoria esté correctamente inicializada
///   antes de usar los punteros atómicos (o usar init() posteriormente).
#[no_mangle]
pub unsafe extern "C" fn init_shared_memory(fd: c_int) -> *mut EpochState {
    // Mapeo compartido: cambios visibles instantáneamente entre hilos/procesos mapeados
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

    // Verificación de alineación crítica para atomics de 64 bits
    debug_assert_eq!(addr as usize % 8, 0, "mmap returned unaligned address");

    addr as *mut EpochState
}

/// Libera el mapeo de memoria compartida.
/// # Safety
/// - `ptr` debe haber sido obtenido vía init_shared_memory.
/// - Ningún otro hilo debe estar accediendo a esta memoria tras la llamada.
#[no_mangle]
pub unsafe extern "C" fn destroy_shared_memory(ptr: *mut EpochState) {
    if !ptr.is_null() {
        libc::munmap(ptr as *mut c_void, SHARED_STATE_SIZE);
    }
}
