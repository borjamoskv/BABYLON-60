---
name: shared-manifest-kernel
display_name: Kernel de Manifiesto Compartido (64B Seqlock SPMC)
description: Patrón de diseño C-ABI de 64 Bytes (Seqlock SPMC, Cero-Punteros, Fail-Stop
  SCITT y soporte IPC multiplataforma macOS/Linux/Windows). Dispara con "shared manifest",
  "seqlock 64b", "ring-0 shm", "ipc lock-free".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [cortex-kernel]
- POST-CADENA: [thermo-audit]

# SharedManifest Kernel Skill

Esta referencia comprueba un slot atómico SPMC y su parada terminal dentro de un proceso. No es una implementación del runtime ni certifica IPC, atestación hardware o latencia. Antes de trasladarla a una frontera productiva, validar ABI, orden de memoria y aislamiento en el target elegido.

---

## 1. Axiomas de Hardware e Invariantes

1. **Layout histórico:** `size_of == align_of == 64 B` en los targets probados. Esto no demuestra ausencia de false sharing. Para fronteras de Apple Silicon aplicar el contrato de alineación a 128 B del proyecto; no cambiar el formato de intercambio implícitamente.
2. **Cero Indirecciones:** Contiene únicamente tipos atómicos planos (`AtomicU32`, `AtomicU64`, `[AtomicU64; 4]`). Prohibido incluir punteros o referencias.
3. **Parada terminal:** `epistemic_halt()` lleva a `POISONED = 0xDEAD_6060`; no existe transición de vuelta. Una publicación en curso puede terminar stores atómicos, pero no puede reabrir la admisión ni comunicar éxito tras perder su CAS final.
4. **Lectores sin escrituras:** `MAX_RETRIES = 10_000` acota los intentos. Su agotamiento devuelve `ReadError::Contended`, no una lectura válida ni una transición de estado. El supervisor decide explícitamente si debe invocar el halt. Esto conserva lectores puros-de-carga.
5. **Orden y agotamiento:** el ejemplo usa `SeqCst` para todos los accesos y detiene al escritor antes de que el contador pueda dar la vuelta. No debilitar las barreras sin una prueba del protocolo. Rendimiento y correspondencia IPC requieren pruebas adicionales.

---

## 2. Referencia ejecutable en Rust (`no_std`, sin asignaciones)

```rust
#![no_std]
use core::sync::atomic::{AtomicU32, AtomicU64, Ordering};

pub const RUNNING: u32 = 0x0000_0001;
pub const WRITING: u32 = 0x0000_0002;
pub const POISONED: u32 = 0xDEAD_6060;
pub const MAX_RETRIES: usize = 10_000;

#[derive(Debug, PartialEq, Eq)]
pub enum ReadError {
    Halted,
    Contended,
}

#[repr(C, align(64))]
pub struct SharedManifest {
    status_flag: AtomicU32,     // 0x00; privado para preservar las transiciones
    seq: AtomicU32,             // 0x04
    epoch_id: AtomicU64,        // 0x08
    payload_hash: [AtomicU64; 4],// 0x10
    _padding: [u8; 16],         // 0x30
}

impl SharedManifest {
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            epoch_id: AtomicU64::new(1),
            payload_hash: [const { AtomicU64::new(0) }; 4],
            _padding: [0; 16],
        }
    }

    #[inline]
    pub fn is_halted(&self) -> bool {
        self.status_flag.load(Ordering::SeqCst) == POISONED
    }

    pub fn publish(&self, epoch: u64, hash: &[u64; 4]) -> bool {
        // CAS compartido para admisión: solo RUNNING -> WRITING
        if self.status_flag.compare_exchange(RUNNING, WRITING, Ordering::SeqCst, Ordering::SeqCst).is_err() {
            return false;
        }
        let s = self.seq.load(Ordering::SeqCst);
        let Some(next) = s.checked_add(2) else {
            self.epistemic_halt();
            return false;
        };
        self.seq.store(s + 1, Ordering::SeqCst);
        self.epoch_id.store(epoch, Ordering::SeqCst);
        for i in 0..4 {
            self.payload_hash[i].store(hash[i], Ordering::SeqCst);
        }
        self.seq.store(next, Ordering::SeqCst);
        // Un halt concurrente gana al commit: nunca sobrescribir POISONED.
        self.status_flag.compare_exchange(WRITING, RUNNING, Ordering::SeqCst, Ordering::SeqCst).is_ok()
    }

    pub fn read(&self) -> Result<(u64, [u64; 4]), ReadError> {
        let mut retries = 0;
        while retries < MAX_RETRIES {
            if self.is_halted() {
                return Err(ReadError::Halted);
            }
            let s1 = self.seq.load(Ordering::SeqCst);
            if s1 % 2 != 0 {
                retries += 1;
                core::hint::spin_loop();
                continue;
            }
            let epoch = self.epoch_id.load(Ordering::SeqCst);
            let mut hash = [0u64; 4];
            for i in 0..4 {
                hash[i] = self.payload_hash[i].load(Ordering::SeqCst);
            }
            let s2 = self.seq.load(Ordering::SeqCst);
            if s1 == s2 && self.status_flag.load(Ordering::SeqCst) == RUNNING {
                return Ok((epoch, hash));
            }
            retries += 1;
            core::hint::spin_loop();
        }
        Err(if self.is_halted() { ReadError::Halted } else { ReadError::Contended })
    }

    pub fn epistemic_halt(&self) {
        self.status_flag.store(POISONED, Ordering::SeqCst);
    }
}
```

---

## 3. Leer una instantánea estable en Python

Este formato de archivo es una exportación explícita little-endian de 64 B, no una vista directa del layout de atómicos Rust. El productor debe publicar el archivo completo y dejarlo inmutable mientras se lee. Para IPC en vivo usar una API nativa que implemente los accesos atómicos y el protocolo del target; ni copiar bytes ni `ctypes` aportan esas garantías.

```python
import mmap
import os
import struct

SNAPSHOT = struct.Struct("<IIQ4Q16x")

def read_shared_manifest_snapshot(path):
    with open(path, "rb") as source:
        if os.fstat(source.fileno()).st_size != SNAPSHOT.size:
            raise ValueError("Expected a complete 64-byte immutable snapshot")
        with mmap.mmap(source.fileno(), SNAPSHOT.size, access=mmap.ACCESS_READ) as mm:
            data = mm[:]  # bytes propios; no queda ningún puntero exportado
    status, seq, epoch, *hash_values = SNAPSHOT.unpack(data)
    if status != 1 or seq % 2:
        return None
    return epoch, hash_values
```

---

## 4. Matriz de Selección Arquitectónica (RCU vs SharedManifest)

| Métrica / Requisito | RCU (Read-Copy-Update) | SharedManifest (C5-REAL) |
| :--- | :--- | :--- |
| **Tamaño de Estructura** | Grandes / Dinámicas (listas, árboles) | Slot histórico de 64 B; coherencia depende del hardware |
| **Asignación de Memoria** | Requerida (`malloc`/`free` por copia) | **Cero Alloc (`static`/`mmap`/`no_std`)** |
| **Latencia de Escritura** | Depende del protocolo y carga | NO_VERIFICADO hasta ejecutar un benchmark |
| **Parada** | Depende de la implementación | Estado terminal del ejemplo; no sustituye atestación |

### Regla de Causalidad Eficiente:
- **Usar RCU:** Para tablas de enrutamiento o árboles de búsqueda complejos donde los lectores jamás deben reintentar y la liberación de memoria se pueda diferir.
- **Usar SharedManifest:** Para slots de atestación de estado de 64B, telemetría atómica en tiempo real y frenos de seguridad regulados (EU AI Act).

---

## 5. Layout y cola SPSC de referencia en C++17

El layout siguiente no implementa publish/read/halt; no usarlo como un segundo protocolo de parada. La cola admite un productor y un consumidor, tipos copiables y capacidad no nula potencia de dos. Verificar estos límites antes de reutilizarla.

```cpp
#include <atomic>
#include <memory>
#include <cstdint>
#include <cassert>
#include <cstddef>
#include <type_traits>

#ifndef CACHE_LINE_SIZE
#define CACHE_LINE_SIZE 64
#endif

// SharedManifest C-ABI Struct (64 B, alignas 64)
struct alignas(CACHE_LINE_SIZE) SharedManifest {
    std::atomic<uint32_t> status_flag{1};     // 0x00: 1 = RUNNING, 0xDEAD6060 = POISONED
    std::atomic<uint32_t> seq{0};             // 0x04: Seqlock counter (even=valid, odd=writing)
    std::atomic<uint64_t> epoch_id{1};        // 0x08: Monotonic epoch counter
    std::atomic<uint64_t> payload_hash[4]{};  // 0x10: digest de 32 B
    uint8_t  _padding[16]{};                  // 0x30: Complete 64 Bytes
};

static_assert(sizeof(SharedManifest) == 64, "SharedManifest size must be 64 B");
static_assert(alignof(SharedManifest) == 64, "SharedManifest alignment must be 64 B");

// Lock-Free SPSC Ring Buffer
template <typename T, size_t Capacity>
class SPSCRingBuffer {
    static_assert(Capacity > 0 && (Capacity & (Capacity - 1)) == 0, "Nonzero power of 2 required");
    static_assert(std::is_trivially_copyable<T>::value, "Reference queue requires trivially copyable T");
private:
    alignas(CACHE_LINE_SIZE) std::atomic<std::size_t> head{0};
    alignas(CACHE_LINE_SIZE) std::atomic<std::size_t> tail{0};
    alignas(CACHE_LINE_SIZE) T buffer[Capacity];
public:
    bool push(const T& item) {
        const size_t current_tail = tail.load(std::memory_order_relaxed);
        const size_t current_head = head.load(std::memory_order_acquire);
        if (current_tail - current_head >= Capacity) return false;
        buffer[current_tail & (Capacity - 1)] = item;
        tail.store(current_tail + 1, std::memory_order_release);
        return true;
    }
    bool pop(T& item) {
        const size_t current_head = head.load(std::memory_order_relaxed);
        const size_t current_tail = tail.load(std::memory_order_acquire);
        if (current_head == current_tail) return false;
        item = buffer[current_head & (Capacity - 1)];
        head.store(current_head + 1, std::memory_order_release);
        return true;
    }
};

// Dimensionar el almacenamiento según la capacidad; una cola grande puede requerir heap.
```

## 6. Payloads y sincronización

Conservar payloads atómicos como en la referencia Rust. Para calcular un hash, trabajar sobre la copia local obtenida por `read()` después de validar la secuencia. Un contador no hace seguras las lecturas y escrituras concurrentes de bytes no atómicos: [UnsafeCell no evita carreras de datos](https://doc.rust-lang.org/std/cell/struct.UnsafeCell.html). No añadir `unsafe impl Sync` para eludir esa obligación. Para otro tamaño o una representación no atómica, elegir un protocolo que excluya los accesos conflictivos y comprobarlo antes de incorporarlo.
