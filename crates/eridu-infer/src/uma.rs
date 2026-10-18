//! Abstracción de memoria unificada (UMA) de Apple Silicon para tensores Zero-Copy (RFO = 0).
//! Alineación estricta a páginas de 16 KB (Darwin ARM64) y líneas de caché de 128 bytes.

use std::alloc::{alloc_zeroed, dealloc, Layout};
use std::ptr::NonNull;

pub const DARWIN_PAGE_SIZE: usize = 16384; // 16 KB en Apple Silicon
pub const M_SERIES_CACHE_LINE: usize = 128; // 128 bytes en Apple Silicon

/// Buffer alineado en memoria unificada (UMA) sin duplicación de páginas.
pub struct UmaAlignedBuffer {
    ptr: NonNull<u8>,
    layout: Layout,
    pub size: usize,
}

unsafe impl Send for UmaAlignedBuffer {}
unsafe impl Sync for UmaAlignedBuffer {}

impl UmaAlignedBuffer {
    /// Asigna un buffer en memoria física contigua alineada a páginas de 16 KB.
    pub fn allocate(size: usize) -> Result<Self, String> {
        let aligned_size = (size + DARWIN_PAGE_SIZE - 1) & !(DARWIN_PAGE_SIZE - 1);
        let layout = Layout::from_size_align(aligned_size, DARWIN_PAGE_SIZE)
            .map_err(|e| format!("Layout inválido para UMA: {}", e))?;

        let raw_ptr = unsafe { alloc_zeroed(layout) };
        let ptr = NonNull::new(raw_ptr)
            .ok_or_else(|| "Fallo asignando buffer alineado en memoria unificada".to_string())?;

        Ok(Self {
            ptr,
            layout,
            size: aligned_size,
        })
    }

    /// Retorna una rodaja inmutable de los bytes del buffer.
    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr.as_ptr(), self.size) }
    }

    /// Retorna una rodaja mutable de los bytes del buffer.
    pub fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.ptr.as_ptr(), self.size) }
    }

    /// Retorna el puntero crudo para interoperabilidad con Metal `MTLBuffer` (`newBufferWithBytesNoCopy`).
    pub fn as_ptr(&self) -> *const u8 {
        self.ptr.as_ptr()
    }
}

impl Drop for UmaAlignedBuffer {
    fn drop(&mut self) {
        unsafe {
            dealloc(self.ptr.as_ptr(), self.layout);
        }
    }
}

/// Pool de buffers UMA reutilizables para inferencia sin fragmentación de heap.
pub struct UmaBufferPool {
    pool: Vec<UmaAlignedBuffer>,
    buffer_size: usize,
}

impl UmaBufferPool {
    pub fn new(capacity: usize, buffer_size: usize) -> Result<Self, String> {
        let mut pool = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            pool.push(UmaAlignedBuffer::allocate(buffer_size)?);
        }
        Ok(Self { pool, buffer_size })
    }

    pub fn acquire(&mut self) -> Result<UmaAlignedBuffer, String> {
        if let Some(buf) = self.pool.pop() {
            Ok(buf)
        } else {
            UmaAlignedBuffer::allocate(self.buffer_size)
        }
    }

    pub fn release(&mut self, buf: UmaAlignedBuffer) {
        if self.pool.len() < self.pool.capacity() {
            self.pool.push(buf);
        }
    }
}
