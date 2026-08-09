//! # SPSC Ring Buffer — Lock-Free Communication Ring (Capa 3 / CALM)
//!
//! Implements a 100% coordination-free, single-producer single-consumer ring
//! buffer for lock-free IPC messaging.

use core::sync::atomic::{AtomicUsize, Ordering};
use core::mem::MaybeUninit;

/// Struct de control del búfer circular SPSC libre de bloqueos.
/// Alineado a 64 bytes para eliminar el *false sharing* entre hilos.
#[repr(C, align(64))]
pub struct SpscRingBuffer<T, const CAP: usize = 1024> {
    /// Índice de escritura del productor (Release).
    pub head: AtomicUsize,
    /// Pad para evitar false sharing entre head y tail.
    _pad1: [u8; 56],
    /// Índice de lectura del consumidor (Acquire).
    pub tail: AtomicUsize,
    /// Pad para evitar false sharing.
    _pad2: [u8; 56],
    /// Slots del anillo.
    ring: [MaybeUninit<T>; CAP],
}

impl<T, const CAP: usize> SpscRingBuffer<T, CAP> {
    /// Crea una nueva instancia del anillo SPSC.
    #[must_use]
    pub fn new() -> Self {
        let ring = unsafe { MaybeUninit::uninit().assume_init() };
        Self {
            head: AtomicUsize::new(0),
            _pad1: [0; 56],
            tail: AtomicUsize::new(0),
            _pad2: [0; 56],
            ring,
        }
    }

    /// Retorna la cantidad de elementos en el búfer.
    #[inline]
    pub fn len(&self) -> usize {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Relaxed);
        head.wrapping_sub(tail)
    }

    /// Retorna `true` si el búfer está vacío.
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Retorna `true` si el búfer está lleno.
    #[inline]
    pub fn is_full(&self) -> bool {
        self.len() >= CAP
    }

    /// Publica un nuevo ítem en el anillo (Productor Único).
    #[inline]
    pub fn push(&self, val: T) -> Result<(), T> {
        let _probe_start = crate::probe_start!();
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);

        if head.wrapping_sub(tail) >= CAP {
            return Err(val); // Ring lleno
        }

        let slot_idx = head % CAP;
        unsafe {
            let slot_ptr = self.ring[slot_idx].as_ptr() as *mut T;
            slot_ptr.write(val);
        }

        self.head.store(head.wrapping_add(1), Ordering::Release);
        crate::probe_end!("spsc_push", _probe_start);
        Ok(())
    }

    /// Extrae el siguiente ítem del anillo (Consumidor Único).
    #[inline]
    pub fn pop(&self) -> Option<T> {
        let _probe_start = crate::probe_start!();
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);

        if tail == head {
            return None; // Ring vacío
        }

        let slot_idx = tail % CAP;
        let val = unsafe {
            let slot_ptr = self.ring[slot_idx].as_ptr();
            slot_ptr.read()
        };

        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        crate::probe_end!("spsc_pop", _probe_start);
        Some(val)
    }
}

impl<T, const CAP: usize> Default for SpscRingBuffer<T, CAP> {
    fn default() -> Self {
        Self::new()
    }
}
