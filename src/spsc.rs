// Certified Specification — BABYLON-60 — SPSC Ring Buffer Lock-Free
// Single-Producer Single-Consumer (SPSC) Zero-Copy Channel para AArch64/ARMv9
//
// ALINEACIÓN Y COHERENCIA:
// Punteros head y tail separados por relleno de 128 B para evitar false sharing
// en arquitecturas ARMv9/Apple Silicon (CWG = 128 B).
//
// GARANTÍA CALM (MONOTONICIDAD):
// Los punteros de secuencia incrementan de forma estrictamente monótona (u64).
// No existe coordinación global ni bloqueos mutuos entre productor y consumidor.

use core::cell::UnsafeCell;
use core::mem::MaybeUninit;
use core::sync::atomic::{AtomicU64, Ordering};

/// Relleno de alineación para prevenir False Sharing en caché L1/L2 (128 bytes).
#[repr(align(128))]
struct CachePaddedAtomicU64 {
    val: AtomicU64,
}

impl CachePaddedAtomicU64 {
    const fn new(val: u64) -> Self {
        Self {
            val: AtomicU64::new(val),
        }
    }
}

/// Buffer circular SPSC (Single-Producer Single-Consumer) Lock-Free.
///
/// La capacidad `CAP` debe ser una potencia de 2.
pub struct SpscRingBuffer<T, const CAP: usize> {
    head: CachePaddedAtomicU64,
    tail: CachePaddedAtomicU64,
    buffer: UnsafeCell<[MaybeUninit<T>; CAP]>,
}

unsafe impl<T: Send, const CAP: usize> Sync for SpscRingBuffer<T, CAP> {}
unsafe impl<T: Send, const CAP: usize> Send for SpscRingBuffer<T, CAP> {}

impl<T, const CAP: usize> SpscRingBuffer<T, CAP> {
    /// Constante de assert en tiempo de compilación: CAP debe ser potencia de 2 y > 0.
    const MASK: usize = {
        assert!(CAP > 0, "Capacity must be greater than 0");
        assert!((CAP & (CAP - 1)) == 0, "Capacity must be a power of 2");
        CAP - 1
    };

    /// Crea una nueva instancia de `SpscRingBuffer` sin alojar memoria en heap.
    #[must_use]
    pub const fn new() -> Self {
        // Inicialización segura de array de MaybeUninit sin copias
        let uninit_arr: [MaybeUninit<T>; CAP] = unsafe {
            MaybeUninit::uninit().assume_init()
        };

        Self {
            head: CachePaddedAtomicU64::new(0),
            tail: CachePaddedAtomicU64::new(0),
            buffer: UnsafeCell::new(uninit_arr),
        }
    }

    /// Inserta un elemento en el ring buffer de forma lock-free.
    ///
    /// Solo debe ser invocado por el **único hilo productor**.
    /// Retorna `Err(value)` si el buffer está lleno.
    pub fn push(&self, value: T) -> Result<(), T> {
        let head = self.head.val.load(Ordering::Relaxed);
        let tail = self.tail.val.load(Ordering::Acquire);

        if head.wrapping_sub(tail) as usize >= CAP {
            return Err(value);
        }

        let index = (head as usize) & Self::MASK;
        unsafe {
            let buffer_ptr = self.buffer.get() as *mut MaybeUninit<T>;
            buffer_ptr.add(index).write(MaybeUninit::new(value));
        }

        // Publicación con semántica Release (STLR en AArch64)
        self.head.val.store(head.wrapping_add(1), Ordering::Release);
        Ok(())
    }

    /// Extrae un elemento del ring buffer de forma lock-free.
    ///
    /// Solo debe ser invocado por el **único hilo consumidor**.
    /// Retorna `None` si el buffer está vacío.
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.val.load(Ordering::Relaxed);
        let head = self.head.val.load(Ordering::Acquire);

        if tail == head {
            return None;
        }

        let index = (tail as usize) & Self::MASK;
        let value = unsafe {
            let buffer_ptr = self.buffer.get() as *mut MaybeUninit<T>;
            buffer_ptr.add(index).read().assume_init()
        };

        // Avanzar el consumidor con semántica Release
        self.tail.val.store(tail.wrapping_add(1), Ordering::Release);
        Some(value)
    }

    /// Retorna la cantidad actual de elementos en el ring buffer.
    #[must_use]
    pub fn len(&self) -> usize {
        let head = self.head.val.load(Ordering::Relaxed);
        let tail = self.tail.val.load(Ordering::Acquire);
        head.wrapping_sub(tail) as usize
    }

    /// Retorna `true` si el ring buffer está vacío.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Retorna `true` si el ring buffer ha alcanzado su capacidad máxima.
    #[must_use]
    pub fn is_full(&self) -> bool {
        self.len() >= CAP
    }

    /// Capacidad total del buffer.
    #[must_use]
    pub const fn capacity(&self) -> usize {
        CAP
    }
}

impl<T, const CAP: usize> Default for SpscRingBuffer<T, CAP> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T, const CAP: usize> Drop for SpscRingBuffer<T, CAP> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}
