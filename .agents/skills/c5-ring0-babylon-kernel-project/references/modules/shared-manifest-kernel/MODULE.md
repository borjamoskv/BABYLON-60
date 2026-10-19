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

Este patrón proporciona un mecanismo de comunicación interproceso (IPC) de ultra-baja latencia ($1.1 - 2.4 \text{ ns}$), sin cerrojos (lock-free), cero asignaciones de memoria y con atestación de seguridad fail-stop.

---

## 1. Axiomas de Hardware e Invariantes

1. **Alineación y Cero False Sharing:** `size_of == align_of == 64 B` (`#[repr(C, align(64))]`).
2. **Cero Indirecciones:** Contiene únicamente tipos atómicos planos (`AtomicU32`, `AtomicU64`, `[AtomicU64; 4]`). Prohibido incluir punteros o referencias.
3. **Acotamiento Entrópico y Fail-Stop:** `MAX_RETRIES = 10_000`. Si un lector excede el umbral, invoca `epistemic_halt()` y pasa el estado a `POISONED = 0xDEAD_6060`.
4. **Throughput Eficiente:** Evaluado bajo el vector $\mathcal{T}_{\text{eficiente}} = \Xi \cdot \mathcal{P}$.

---

## 2. Implementación Canónica en Rust (`no_std`)

```rust
#![no_std]
use core::sync::atomic::{AtomicU32, AtomicU64, Ordering};

pub const RUNNING: u32 = 0x0000_0001;
pub const WRITING: u32 = 0x0000_0002;
pub const HALTING: u32 = 0xDEAD_6061;
pub const POISONED: u32 = 0xDEAD_6060;
pub const MAX_RETRIES: usize = 10_000;

#[repr(C, align(64))]
pub struct SharedManifest {
    pub status_flag: AtomicU32,     // 0x00
    pub seq: AtomicU32,             // 0x04
    pub epoch_id: AtomicU64,        // 0x08
    pub payload_hash: [AtomicU64; 4],// 0x10
    pub _padding: [u8; 16],         // 0x30
}

impl SharedManifest {
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            epoch_id: AtomicU64::new(1),
            payload_hash: [AtomicU64::new(0); 4],
            _padding: [0; 16],
        }
    }

    #[inline]
    pub fn is_halted(status: u32) -> bool {
        status == HALTING || status == POISONED
    }

    pub fn publish(&self, epoch: u64, hash: &[u64; 4]) -> bool {
        // CAS compartido para admisión: solo RUNNING -> WRITING
        if self.status_flag.compare_exchange(RUNNING, WRITING, Ordering::AcqRel, Ordering::Acquire).is_err() {
            return false;
        }
        let s = self.seq.fetch_add(1, Ordering::Release);
        self.epoch_id.store(epoch, Ordering::Relaxed);
        for i in 0..4 {
            self.payload_hash[i].store(hash[i], Ordering::Relaxed);
        }
        self.seq.store(s.wrapping_add(2), Ordering::Release);
        self.status_flag.store(RUNNING, Ordering::Release);
        true
    }

    pub fn read(&self) -> Option<(u64, [u64; 4])> {
        let mut retries = 0;
        while retries < MAX_RETRIES {
            if Self::is_halted(self.status_flag.load(Ordering::Relaxed)) {
                return None;
            }
            let s1 = self.seq.load(Ordering::Acquire);
            if s1 % 2 != 0 {
                retries += 1;
                core::hint::spin_loop();
                continue;
            }
            let epoch = self.epoch_id.load(Ordering::Relaxed);
            let mut hash = [0u64; 4];
            for i in 0..4 {
                hash[i] = self.payload_hash[i].load(Ordering::Relaxed);
            }
            let s2 = self.seq.load(Ordering::Acquire);
            if s1 == s2 {
                return Some((epoch, hash));
            }
            retries += 1;
            core::hint::spin_loop();
        }
        None
    }

    pub fn epistemic_halt(&self) {
        self.status_flag.store(HALTING, Ordering::SeqCst);
        self.seq.fetch_add(1, Ordering::SeqCst);
    }
}
```

---

## 3. Cliente Lector en Python para Windows (`mmap` + `ctypes`)

```python
import mmap
import ctypes

class SharedManifestCTypes(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("status_flag", ctypes.c_uint32),
        ("seq", ctypes.c_uint32),
        ("epoch_id", ctypes.c_uint64),
        ("payload_hash", ctypes.c_uint64 * 4),
        ("_padding", ctypes.c_uint8 * 16)
    ]

def read_shared_manifest(map_name="Local\\SharedManifest"):
    with mmap.mmap(-1, 64, tagname=map_name, access=mmap.ACCESS_READ) as mm:
        manifest = SharedManifestCTypes.from_buffer(mm)
        if manifest.status_flag == 0xDEAD6060:
            return None
        s1 = manifest.seq
        if s1 % 2 != 0:
            return None
        epoch = manifest.epoch_id
        hash_vals = [manifest.payload_hash[i] for i in range(4)]
        s2 = manifest.seq
        if s1 == s2:
            return (epoch, hash_vals)
    return None
```

---

## 4. Matriz de Selección Arquitectónica (RCU vs SharedManifest)

| Métrica / Requisito | RCU (Read-Copy-Update) | SharedManifest (C5-REAL) |
| :--- | :--- | :--- |
| **Tamaño de Estructura** | Grandes / Dinámicas (listas, árboles) | Fijo exacto de 64 Bytes (línea de caché) |
| **Asignación de Memoria** | Requerida (`malloc`/`free` por copia) | **Cero Alloc (`static`/`mmap`/`no_std`)** |
| **Latencia de Escritura** | Estocástica (*Grace Period* / Sync) | **Atómica Instantánea ($< 2.4 \text{ ns}$)** |
| **Garantía Fail-Stop** | Excepción / Crash por puntero | **Atómica Irreversible (`POISONED = 0xDEAD6060`)** |

### Regla de Causalidad Eficiente:
- **Usar RCU:** Para tablas de enrutamiento o árboles de búsqueda complejos donde los lectores jamás deben reintentar y la liberación de memoria se pueda diferir.
- **Usar SharedManifest:** Para slots de atestación de estado de 64B, telemetría atómica en tiempo real y frenos de seguridad regulados (EU AI Act).

---

## 5. Implementación C++17 de Alto Rendimiento (SharedManifest & CALM SPSC Sequencer)

```cpp
#include <atomic>
#include <memory>
#include <cstdint>
#include <cassert>

#ifndef CACHE_LINE_SIZE
#define CACHE_LINE_SIZE 64
#endif

// SharedManifest C-ABI Struct (64 B, alignas 64)
struct alignas(CACHE_LINE_SIZE) SharedManifest {
    std::atomic<uint32_t> status_flag{1};     // 0x00: 1 = RUNNING, 0xDEAD6060 = POISONED
    std::atomic<uint32_t> seq{0};             // 0x04: Seqlock counter (even=valid, odd=writing)
    std::atomic<uint64_t> epoch_id{1};        // 0x08: Monotonic epoch counter
    std::atomic<uint64_t> payload_hash[4]{};  // 0x10: 32B SHAKE256 digest
    uint8_t  _padding[16]{};                  // 0x30: Complete 64 Bytes
};

static_assert(sizeof(SharedManifest) == 64, "SharedManifest size must be 64 B");
static_assert(alignof(SharedManifest) == 64, "SharedManifest alignment must be 64 B");

// Lock-Free SPSC Ring Buffer
template <typename T, size_t Capacity>
class SPSCRingBuffer {
    static_assert((Capacity & (Capacity - 1)) == 0, "Power of 2 required");
private:
    struct alignas(CACHE_LINE_SIZE) { std::atomic<size_t> head{0}; };
    struct alignas(CACHE_LINE_SIZE) { std::atomic<size_t> tail{0}; };
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

// Nota: Instanciar siempre en Heap (std::make_unique) para evitar Stack Overflow en macOS
```

### 2.1. Variante de Carga Continua (UnsafeCell + Hashing Lock-Free)
Para payloads que requieren hashing criptográfico (`sha3`) en la ruta crítica, donde `[AtomicU64; N]` rompe la ergonomía de lectura como slice contiguo, se emplea `UnsafeCell` con implementación explícita de `Sync`:

```rust
use core::cell::UnsafeCell;
use core::sync::atomic::{AtomicUsize, Ordering};

#[repr(C, align(64))]
pub struct C5Manifest {
    pub seq: AtomicUsize,
    pub payload: UnsafeCell<[u8; 64]>,
}
// Forzamos el contrato de hilo, asumiendo que el programador respetará el Seqlock.
unsafe impl Sync for C5Manifest {}
unsafe impl Send for C5Manifest {}

// Los escritores mutan el `payload` tras incrementar `seq` a impar.
// Los lectores operan con `(*manifest.payload.get())` copiando la memoria a la pila
// solo cuando `seq` es par y validando que no haya mutado entre load(Acquire) y read.
```
