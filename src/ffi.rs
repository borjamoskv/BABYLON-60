//! # FFI — C ABI Bindings
//! Exportaciones C-compatible para integración con sistemas C/C++ (ej. C++20 SPSC harness).

use crate::manifest::{HaltReason, SharedManifest};
use crate::seqlock;
use crate::halt;

/// Inicializa una instancia de `SharedManifest` a su estado por defecto (`RUNNING`).
///
/// # Safety
/// `manifest` debe ser un puntero válido y alineado a 64 bytes hacia una memoria escribible.
#[no_mangle]
pub unsafe extern "C" fn babylon60_manifest_init(manifest: *mut SharedManifest) -> bool {
    if manifest.is_null() {
        return false;
    }
    if (manifest as usize) % core::mem::align_of::<SharedManifest>() != 0 {
        return false;
    }
    unsafe {
        manifest.write(SharedManifest::new());
    }
    true
}

/// Publica un par (epoch, hash) sobre el slot del manifest.
///
/// # Safety
/// - `manifest` debe apuntar a una estructura `SharedManifest` válida.
/// - `hash_ptr` debe apuntar a un array de 4 elementos `u64`.
/// - Debe ser invocado por un **único escritor**.
#[no_mangle]
pub unsafe extern "C" fn babylon60_publish(
    manifest: *const SharedManifest,
    epoch: u64,
    hash_ptr: *const u64,
) -> bool {
    if manifest.is_null() || hash_ptr.is_null() {
        return false;
    }
    if (manifest as usize) % core::mem::align_of::<SharedManifest>() != 0 {
        return false;
    }
    let m = unsafe { &*manifest };
    let hash = unsafe { &*(hash_ptr as *const [u64; 4]) };
    seqlock::publish(m, epoch, hash);
    true
}

/// Lee de forma consistente (epoch, hash) del manifest.
///
/// # Safety
/// - `manifest` debe ser un puntero válido a `SharedManifest`.
/// - `out_epoch` debe ser un puntero no nulo escribible para recibir el `u64` del epoch.
/// - `out_hash_ptr` debe ser un puntero no nulo a un buffer de al menos 4 elementos `u64`.
///
/// Retorna `true` si la lectura fue consistente y `false` si se agotaron los reintentos (`MAX_RETRIES`).
#[no_mangle]
pub unsafe extern "C" fn babylon60_read(
    manifest: *const SharedManifest,
    out_epoch: *mut u64,
    out_hash_ptr: *mut u64,
) -> bool {
    if manifest.is_null() || out_epoch.is_null() || out_hash_ptr.is_null() {
        return false;
    }
    if (manifest as usize) % core::mem::align_of::<SharedManifest>() != 0 {
        return false;
    }
    let m = unsafe { &*manifest };
    match seqlock::read(m) {
        Some((epoch, hash)) => {
            unsafe {
                *out_epoch = epoch;
                let out_hash = &mut *(out_hash_ptr as *mut [u64; 4]);
                *out_hash = hash;
            }
            true
        }
        None => false,
    }
}

/// Retorna `true` si el manifest está en estado `POISONED`.
///
/// # Safety
/// `manifest` debe apuntar a una estructura `SharedManifest` válida.
#[no_mangle]
pub unsafe extern "C" fn babylon60_is_halted(manifest: *const SharedManifest) -> bool {
    if manifest.is_null() {
        return true;
    }
    if (manifest as usize) % core::mem::align_of::<SharedManifest>() != 0 {
        return true;
    }
    let m = unsafe { &*manifest };
    halt::is_halted(m)
}

/// Transiciona el manifest a `POISONED` según el código de motivo especificado.
///
/// Código de motivo:
/// - 0: `SeqRetryExhausted`
/// - 1: `HashMismatch`
/// - 2: `EpochNonMonotonic`
/// - 3: `AlreadyPoisoned`
/// - 4: `ExternalSignal`
///
/// # Safety
/// Esta función marca el flag `POISONED` y aborta el proceso si la feature `std` está activa.
#[no_mangle]
pub unsafe extern "C" fn babylon60_epistemic_halt(manifest: *const SharedManifest, reason_code: u32) -> ! {
    let motivo = match reason_code {
        0 => HaltReason::SeqRetryExhausted,
        1 => HaltReason::HashMismatch,
        2 => HaltReason::EpochNonMonotonic,
        3 => HaltReason::AlreadyPoisoned,
        _ => HaltReason::ExternalSignal,
    };
    if !manifest.is_null() {
        let m = unsafe { &*manifest };
        halt::epistemic_halt(m, motivo);
    } else {
        #[cfg(feature = "std")]
        std::process::abort();
        #[cfg(not(feature = "std"))]
        loop {
            core::hint::spin_loop();
        }
    }
}
