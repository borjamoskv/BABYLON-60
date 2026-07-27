# BABYLON-60 Formal Specification (v2.5.1-C5-REAL)

> **C5-REAL Axiom:** El lenguaje no comunica; compila. Esta especificación formal define la semántica operacional, la máquina abstracta, las invariantes y el modelo de fallo de BABYLON-60, permitiendo que un asistente de pruebas (Lean 4 / Coq) razone sobre los artefactos exportados sin ambigüedad.

---

## 1. Abstract Machine (Máquina Abstracta)

El motor BABYLON-60 se define formalmente como la 6-tupla:

$$\mathcal{M} = \langle R, H, L, C, Q, T \rangle$$

```
   ┌───────────────────────────────────────────────────────────────────┐
   │                  Máquina Abstracta M = ⟨R, H, L, C, Q, T⟩         │
   ├───────────┬───────────┬───────────┬───────────┬───────────┬───────┤
   │ Registers │   Heap    │  Ledger   │   Clock   │ Scheduler │ Proof │
   │   R[0..N] │  (Linear) │(Append-   │ (Planck)  │  Queue Q  │Harness│
   │  (Immutable│           │   Only)   │  C.tick   │           │   T   │
   │    COW)   │           │           │           │           │       │
   └───────────┴───────────┴───────────┴───────────┴───────────┴───────┘
```

Donde:
- $R$ (**Registers**): Conjunto de registros locales por corrutina $R[0..N]$. Son puramente **inmutables** y sujetos a *Copy-on-Write* (COW) durante el paso de mensajes.
- $H$ (**Heap**): Memoria compartida estructurada con **Tipos Lineales** (*Linear Types*). Un recurso en el Heap solo puede tener un único dueño (corrutina) activo en un instante dado, eliminando por diseño las carreras de datos (*data races*).
- $L$ (**Ledger**): Estructura de eventos inmutable y *append-only*, ordenada de forma causal mediante sellos criptográficos.
- $C$ (**Clock**): Reloj monotónico global discreto escalado en `UNIT.TICK` (Resolución Planck de 1ms).
- $Q$ (**Coroutine Queue**): Cola de planificadores (Scheduler) de corrutinas en estados $\{\text{Ready}, \text{Waiting}, \text{Running}, \text{Completed}, \text{Halted}\}$.
- $T$ (**Trace Export**): Acumulador de pruebas (*Proof Harness*) que captura snapshots deterministas tras transiciones observables para verificación en Lean 4.

---

## 2. Tipo Numérico `F60` y Modelo de Memoria

### 2.1 Exactitud y Reducción Sexagesimal Determinista

El tipo `F60` se refina matemáticamente para prevenir la acumulación de errores y el *Blowup de Numerador*:

$$\text{F60} = \{ N \in \mathbb{Z}, S \in \mathbb{N}_{60} \}$$

$$\text{ValorMatemático}(\text{F60}) = \frac{N}{60^S}$$

#### Operación de Reducción Determinista:
$$\text{reduce}(N, S) = \left( \frac{N}{\gcd(N, 60^S)}, S - \log_{60}(\gcd(N, 60^S)) \right)$$

> [!WARNING]
> **Desbordamiento Comprobable:** Si la memoria de $N \in \mathbb{Z}$ excede la cuota estricta (256 bytes por escalar) para evitar ataques de agotamiento de memoria, la máquina virtual dispara de inmediato la transición de fallo `CRITICAL_HALT`.

### 2.2 Modelo de Memoria y Transferencia de Propiedad
- **Inmutabilidad de Registros:** Ninguna instrucción muta un registro *in situ*. Toda evaluación funcional genera un nuevo estado inmutable.
- **Copy-on-Write (COW):** En operaciones `FORK`, la nueva corrutina hereda una vista superficial de $R$ y $H$. La primera escritura clona el bloque correspondiente.
- **Linear Type Invariant:** Liberar o duplicar un recurso del Heap sin consumo explícito genera un error de verificación estática de tipos en tiempo de compilación.

---

## 3. Operational Semantics (Small-Step Semantics)

Se define el estado de una corrutina individual como la 3-tupla:

$$\Gamma = (\text{PC}, R, S)$$

### 3.1 Conjunto de Opcodes y Reglas de Transición

| Opcode | Descripción Semántica | Regla de Transición Small-Step |
| :--- | :--- | :--- |
| `FORK Label` | Bifurca la corrutina actual clonando entorno sin afectar causalidad. | $\frac{\Gamma \vdash \text{FORK Label}}{Q' = Q \cup \{ (\text{Label}, R_{\text{cow}}, \text{Ready}) \}, \; \Gamma' = (\text{PC} + 1, R, \text{Running})}$ |
| `AWAIT Symbol Label` | Emite evento al Ledger y suspende en espera de ACK causal. | $\frac{\Gamma \vdash \text{AWAIT Symbol Label}}{L' = L \cup \{ (C.\text{now}(), \text{Emitted}(\text{Symbol})) \}, \; \Gamma' = (\text{Label}, R, \text{Waiting}(\text{Symbol\_ACK}))}$ |
| `AFTER R_ticks Label` | Suspende explícitamente en el tiempo discreto. | $\frac{\Gamma \vdash \text{AFTER } R_{\text{ticks}} \text{ Label}}{Q' = Q \cup \{ (\text{Label}, R, \text{Waiting\_Timer}(C.\text{now}() + R_{\text{ticks}})) \}, \; \Gamma' = (-, R, \text{Suspended})}$ |
| `HALT` | Detiene inmediatamente la corrutina y exporta su traza. | $\frac{\Gamma \vdash \text{HALT}}{T' = T \cup \{ \text{Snapshot}(\Gamma) \}, \; \Gamma' = (-, R, \text{Halted})}$ |

---

## 4. Invariantes del Sistema (Proof Constraints)

Estas invariantes son formalmente comprobadas por el kernel y cualquier violación dispara un aborto inmediato:

- **I1 (Unicidad Operacional):** Ninguna corrutina ejecuta más de una instrucción por `UNIT.TICK` escalar, previniendo carreras de concurrencia.
- **I2 (Causalidad Única):** Cada evento $e \in L$ posee una firma criptográfica única perteneciente al productor registrado.
- **I3 (Inmutabilidad del Pasado):** El Ledger $L$ es estrictamente *append-only*. No existe el opcode de borrado ni de modificación histórica.
- **I4 (Monotonía Temporal):** El reloj global $C$ satisface la monotonía estricta: $C.\text{now}() \le C.\text{next}()$.
- **I5 (Ausencia de Anergía):** No existe estado mutable oculto (*Hidden Mutable State*). Toda mutación se refleja de forma transparente en $R$, $H$ o $L$.
- **INV_BFT_04:** Transacciones en la persistencia con conflicto de `payload_hash` disparan `ValueError` instantáneo.
- **INV_C5_28:** Toda comparación de grafos ejecuta filtro 1-WL antes de VF2.

---

## 5. Modelo de Fallo Formal y Exportación a Lean 4

Cuando se detecta una condición de inestabilidad, fallo causal o violación de invariante, la máquina virtual sigue la secuencia rígida:

```
[ CRITICAL HALT ] ──► [ CAUSAL SNAPSHOT ] ──► [ ARTIFACT EXPORT ] ──► [ ABORT PROCESS ]
```

1. **CRITICAL HALT:** Se suspende el despachador de la corrutina infractora de forma inmediata.
2. **CAUSAL SNAPSHOT:** Se extrae un digest SHA-256 inmutable del estado completo de la máquina $\mathcal{M} = \langle R, H, L, C, Q, T \rangle$.
3. **ARTIFACT EXPORT:** Se serializa el snapshot en el esquema formal `export_schema.json` para su posterior importación en el asistente de demostraciones Lean 4 (`BabylonTrace.lean`).
4. **ABORT PROCESS:** Terminación determinista del proceso con código de salida no nulo (`EXIT_FAILURE`).
