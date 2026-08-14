<!-- C5-REAL EXERGY CERTIFIED -->
# Módulo Epistémico: Arquitectura de Silicio e IPC (`docs/architecture/`)

Este subdirectorio define las **Invariantes Arquitectónicas de Silicio**, especificando el acoplamiento directo C-ABI y la comunicación de memoria compartida entre procesos de alto rendimiento.

---

## 🔗 Vinculación con Silicio (`src/`)

- **Capa en `src/`**: [`src/01_kernel/ring0_rust/`](../../src/01_kernel/ring0_rust/) & [`src/01_kernel/ipc_daemon/`](../../src/01_kernel/ipc_daemon/)
- **Propósito**: Garantizar latencias sub-nanosegundo (T_{\text{eff}} < 1\text{ ms}) mediante buffers de memoria alineados a la línea de caché de la CPU sin bloqueos de bus lentos.

---

## 📂 Documentos Clave

- [`c5_real_ring_buffer_manifesto.md`](c5_real_ring_buffer_manifesto.md): Especificación formal del Manifiesto `SharedManifest` de 64 bytes (`#[repr(C, align(64))]` / 128 bytes en Apple Silicon) y el protocolo IPC sin bloqueos de memoria (*Lock-Free Epoch-Based Reclamation*).
