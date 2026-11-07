---
name: thermo-audit
display_name: Auditoría Termodinámica de Silicio y Concurrencia
description: Auditoría termodinámica estricta de C5-REAL en silicio (Aritmética, Concurrencia,
  MDL, Ring-0, Seqlocks y Grados de Libertad Parásitos). Dispara con "/thermo-audit",
  "auditoría termodinámica código", "fricción de silicio", "concurrencia landauer",
  "silicon concurrency audit", "grados de libertad parásitos", "potencia causal".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor`
> - **Modo de Acceso a Worktree:** `audit-only`
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [shared-manifest-kernel]
- POST-CADENA: [c5-silicon-stress-suite]

# Directiva thermo-audit

Cuando el usuario invoque `/thermo-audit`, evaluarás el código activo o propuesto bajo la Invariante Termodinámica estricta:

## Reglas de Auditoría
1. **Aritmética Determinista y Slopsquatting:** Si detectas punto flotante (`f32`, `f64`), rechaza el código y exige Punto Fijo o escalado en `u32`/`u64` para garantizar determinismo en Ring-0. Audita explícitamente el riesgo de *Slopsquatting* (inyección de NaN Payloads) y bloqueos en la ALU por números subnormales (*denormals*) en espacios continuos.
2. **Conservación de Sincronización y Memoria de Frontera:** Analiza los bloqueos de hilos y la gestión de memoria cruzando C-FFI. Prohíbe la exposición de `epoch::Guard`, `Arc<T>` o punteros crudos fuera de Rust (`INV_C5_ZERO_POINTER_FFI`). En Apple Silicon (Darwin ARM64), exige alineación estricta de 128 bytes (`#[repr(C, align(128))]`, `INV_C5_APPLE_128B_PING_PONG`) y arquitectura Ping-Pong Left-Right Wait-Free (layout cuádruple de 512B con flip atómico de `control_word`), erradicando el false sharing físico y las invalidaciones RFO de Seqlock. Exige **Apoptosis Asimétrica Externa** (`INV_C5_ASYMMETRIC_APOPTOSIS`): si el consumidor FFI retiene el slot por más de `MAX_FFI_HOLD_TICKS = 64` ticks, el productor de Ring-0 fuerza el centinela con bandera ortogonal `POISON_SENTINEL = POISON_BIT | 0x5EAD_6060_0000_0000` (con `POISON_BIT = 1 << 63`) para evitar colisiones con la generación monótona a $1.87 \times 10^9$ ticks.
3. **Invariante P×S y Amortización Exergética ($B \ge B^*$):** Verifica si hay concurrencia desbocada que pueda causar *Thrashing* o cuellos de botella asíncronos. Prohíbe la persistencia individual `F_FULLFSYNC` en SQLite L0 WAL (techo de 2.000 TPS); exige amortización de lotes $B \ge B^* \ge \lceil \frac{1-\epsilon}{\epsilon} \cdot \frac{\tau_{\text{SE-Sign}} + \tau_{\text{WAL-Sync}}}{\tau_{\text{Ring-0}}} \rceil$ para garantizar $\eta_{\text{exergía}} \ge 95\%$ (`INV_C5_BATCH_AMORTIZATION`). En LARSA-120, la prueba de equivocación $\mathcal{O}(1)$ dispara `ViewChange(v+1)` con evidencia, pero la evicción de validadores se compromete por consenso determinista en la vista siguiente (`INV_C5_LARSA_VIEWCHANGE_EVICTION`).
4. **Transferencia y memoria:** Verifica la versión instalada del cliente y mide memoria máxima con una carga reproducible. En `huggingface_hub` 1.x se retiró `hf_transfer`; no prescribas su variable heredada ni atribuyas consumo nulo de RAM a una implementación nativa. Consulta la [migración oficial](https://huggingface.co/docs/huggingface_hub/en/concepts/migration#hf_transfer) y elige el modo soportado según la restricción de recursos; un modo de alto rendimiento no implica menor uso de memoria.
5. **Cociente de Bisimulación y Purga de Grados de Libertad Parásitos ($\Delta \text{DoF}_p \to 0 \mid \Delta \mathcal{P}_{\text{causal}} = 0$):**
   Descompón el espacio de estados en $\mathcal{S} = \mathcal{S}_{\text{causal}} \oplus \mathcal{S}_{\text{parásito}}$ e inspecciona sistemáticamente estos 5 vectores:
   - **Clonación de Primitivas Lock-Free con Deriva de Barreras:** Detecta reimplementaciones paralelas de `SharedManifest`, Seqlocks o `SpscRingBuffer` entre crates. Exige una única fuente canónica que preserve `dmb ishld` en AArch64, alineación CWG (`align(64)` / `align(128)`), máscaras $2^k$ y `Drop` explícito sobre `MaybeUninit<T>`.
   - **Máquinas de Estado Desacopladas (Mapa sin Territorio):** Detecta enums ontológicos o controladores (`EffectState`, `AdmissionController`) que no son consumidos en la ruta de ejecución real (`SovereignExecutor`, `EffectTxOrchestrator`). Exige morfismos exhaustivos (`From`/`TryFrom`) verificados por el compilador.
   - **Degradación Stringly-Typed en Fronteras IPC:** Rechaza el transporte de errores tipados mediante `format!("{:?}", err)` y su reconstrucción por `.contains(...)`. Exige serialización estructural exhaustiva del enum de error de dominio.
   - **Constructores con Autoridad por Defecto y Contextos Muertos:** Rechaza wrappers no-scoped que inyecten identidades o nonces constantes (`[0x42; 32]`, `[0; 32]`) y funciones de dominio criptográfico (`signing_input`) que no estén atadas al `external_aad` real del sobre `COSE_Sign1`.
   - **Shims de Redirección y Versionado Muerto en Árbol:** Detecta módulos wrapper de compatibilidad perpetua (`utils/*` reexportando `primitives/*`) y múltiples iteraciones `*_poc_v*.py` coexistiendo en paquetes productivos.

**Output:** Tu respuesta debe ser un reporte implacable de Ineficiencias térmicas o de memoria, con sugerencias quirúrgicas en la capa física.
