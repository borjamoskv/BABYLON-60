# Propuesta de Aprendizaje (C5-REAL / Autocognición)

## 📌 Contexto del Aprendizaje
Durante la iteración de purga termodinámica (Operativo Legión-100) y la integración del puente IPC Causal-Determinist entre Python y Rust, enfrentamos dos cuellos de botella técnicos severos:
1. **Fragilidad de AST en Python (IndentationError):** El intento de parchar bloques `except Exception: pass` usando herramientas de shell multilínea (`sed`) destruyó la tabulación del script `browser_cdp_engine.py`, causando errores catastróficos de sintaxis.
2. **Restricción Sized en Iceoryx2:** El intento de crear un canal Zero-Copy para el *payload* binario (CBOR) usando el tipo *slice* dinámico `open_or_create::<[u8]>()` falló en tiempo de compilación (Error `E0277`) porque la versión actual de la API de Iceoryx2 requiere tipos `Sized`.

## 🛠️ Resolución Implementada
1. Para Python, se abandonó `sed` a favor de pequeños scripts *ad-hoc* en Python que usan `str.replace()` exacto.
2. Para Iceoryx2, se encapsuló el *payload* dinámico dentro de un `struct` de memoria contigua y tamaño fijo (`#[repr(C)] pub struct IpcEnvelope { len: usize, data: [u8; 8192] }`).

## 🔄 Clasificación y Alcance
- **Tipo de Modificación:** Actualización de Invariantes Universales (Reglas de Arquitectura).
- **Archivo Objetivo:** `/Users/borjafernandezangulo/10_PROJECTS/.agents/AGENTS.md`
- **Secciones Afectadas:** `1. INVARIANTES DE ARQUITECTURA Y KERNEL RING-0` y `2.2 Invariantes de Shell y Toolchain`.

---

## 📝 Modificaciones Propuestas

### Adición a la Sección 1 (Arquitectura)
Se agregará una nueva sub-sección **1.5 Invariante de Concurrencia IPC (Iceoryx2)**:
```markdown
### 1.5 Invariante de Concurrencia IPC y FFI (Iceoryx2)
- **Zero-Copy Payload Wrapping:** La API de *publish-subscribe* de `iceoryx2` (v0.3.x) impone restricciones `Sized` en tiempo de compilación (`E0277`). Queda prohibido instanciar canales genéricos con slices dinámicos `open_or_create::<[u8]>()`. Todo *payload* binario de longitud variable (como paquetes CBOR/ExergyPacket) DEBE encapsularse en un `struct` `#[repr(C)]` de tamaño fijo pre-acordado con un campo de longitud (ej. `IpcEnvelope { len: usize, data: [u8; MAX] }`).
```

### Adición a la Sección 2.2 (Invariantes de Shell y Toolchain)
Se agregará la siguiente viñeta a las invariantes de Shell:
```markdown
- **Inyección Python Segura (AST Fragility):** Queda estrictamente prohibido usar utilidades multilínea de shell (`sed`, `awk`) para inyectar o modificar bloques tabulados (como `try/except`) en archivos `.py`. La estricta sangría de Python genera invariablemente un `IndentationError`. Utilizar siempre micro-scripts en Python (`open`, `str.replace()`) para aplicar mutaciones de código en scripts existentes.
```

¿Apruebas esta cristalización del conocimiento en la base de datos de los agentes (AGENTS.md)?
