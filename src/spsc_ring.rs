//! # SPSC Ring Buffer — Lock-Free Communication Ring (Capa 3 / CALM)
//!
//! Implements a 100% coordination-free, single-producer single-consumer ring
//! buffer for `SharedManifest` slots. Producers update `head` with Release
//! semantics; consumers update `tail` with Acquire semantics.

use core::sync::atomic::{AtomicUsize, Ordering};
use crate::manifest::SharedManifest;

/// Tamaño por defecto del anillo SPSC (potencia de 2 para operación bitwise).
pub const RING_CAPACITY: usize = 1024;

/// Struct de control del búfer circular SPSC libre de bloqueos.
/// Alineado a 64 bytes para eliminar el *false sharing* entre hilos.
#[repr(C, align(64))]
pub struct SpscRingBuffer {
    /// Índice de escritura del productor (Release).
    pub head: AtomicUsize,
    /// Pad para evitar false sharing entre head y tail.
    _pad1: [u8; 56],
    /// Índice de lectura del consumidor (Acquire).
    pub tail: AtomicUsize,
    /// Pad para evitar false sharing.
    _pad2: [u8; 56],
    /// Slots contiguos de SharedManifest.
    pub ring: [SharedManifest; RING_CAPACITY],
}

impl SpscRingBuffer {
    /// Crea una nueva instancia inicializada del anillo SPSC.
    #[must_use]
    pub fn new() -> Self {
        // En lugar de inicializar un array grande inline que puede desbordar la pila,
        // creamos una instancia limpia.
        const INIT_MANIFEST: SharedManifest = SharedManifest::new();
        Self {
            head: AtomicUsize::new(0),
            _pad1: [0; 56],
            tail: AtomicUsize::new(0),
            _pad2: [0; 56],
            ring: [INIT_MANIFEST; RING_CAPACITY],
        }
    }

    /// Publica un nuevo estado en el anillo (Productor Único).
    #[inline]
    pub fn push(&self, epoch: u64, hash: &[u64; 4]) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);

        if head.wrapping_sub(tail) >= RING_CAPACITY {
            return false; // Ring lleno
        }

        let slot_idx = head & (RING_CAPACITY - 1);
        crate::seqlock::publish(&self.ring[slot_idx], epoch, hash);

        self.head.store(head.wrapping_add(1), Ordering::Release);
        true
    }

    /// Extrae el siguiente estado del anillo (Consumidor Único).
    #[inline]
    pub fn pop(&self) -> Option<(u64, [u64; 4])> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);

        if tail == head {
            return None; // Ring vacío
        }

        let slot_idx = tail & (RING_CAPACITY - 1);
        let data = crate::seqlock::read(&self.ring[slot_idx])?;

        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        Some(data)
    }
}

impl Default for SpscRingBuffer {
    fn default() -> Self {
        Self::new()
    }
}
