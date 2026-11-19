# 🧮 PROOF — Especificaciones y Teoremas Formales en Lean 4 (`proof/`)

> **DOMINIO DE VERIFICACIÓN FORMAL (`L1_FORMAL`)**  
> Ubicación: `proof/`  
> Contiene las especificaciones y demostraciones comprobadas por máquina en Lean 4, incluyendo los módulos normativos citados en [`CLAIMS.toml`](../CLAIMS.toml) (`[claim.lean4_formal_trace]`).

---

## 🔍 Alcance y Límites Epistémicos (`L1_FORMAL`)

> [!IMPORTANT]
> **Qué demuestra `L1_FORMAL` y qué requiere evidencia separada (`L2`–`L4`):**
> - Los archivos en `proof/lean/` compilan con Lean 4 / `lake build` con **0 `sorry`** y **0 declaraciones `axiom` de usuario** en los módulos principales (`BabylonTrace.lean`, `AX0.lean`, `Babylon.lean`).
> - **`L1_FORMAL` modela la especificación abstracta:** demuestra propiedades inductivas universales y validación por reflexión sobre trazas de estados del modelo (`Proposed`, `Authorized`, `Dispatched`, `Executed`).
> - **Lo que `L1_FORMAL` no certifica por sí solo:** no modela primitivas criptográficas reales (Ed25519 / P-256), persistencia física en SQLite WAL ni el confinamiento de procesos del sistema operativo. Esas garantías requieren las pruebas `L2_IMPLEMENTATION`, `L3_ISOLATION` y `L4_EXPERIMENTAL` declaradas en [`CLAIMS.toml`](../CLAIMS.toml).

---

## 📐 Módulos Principales en `proof/lean/`

### 1. Módulos Normativos de `CLAIMS.toml` (`[claim.lean4_formal_trace]`)

| Archivo | Líneas / Teoremas | Propiedades Comprobadas en Lean 4 |
| :--- | :--- | :--- |
| **[`BabylonTrace.lean`](./lean/BabylonTrace.lean)** | 277 líneas · 10 `theorem` · 0 `axiom` de usuario (`[propext]` del kernel) · 0 `sorry` | Validación por reflexión de trazas de ejecución finitas, teorema inductivo universal de paridad par de lecturas declaradas (`no_torn_reads_universal`) sobre el modelo del protocolo Seqlock y testigo anti-debilitamiento (`NoTornReadsProp`). |
| **[`AX0.lean`](./lean/AX0.lean)** | 180 líneas · 6 `theorem` · 0 `axiom` de usuario (`[propext]` del kernel) · 0 `sorry` | Invariante de separación cognición/autoridad (`AX-0`), teorema inductivo universal de despacho único (`auth_001_universal_inductive_safety`) desde `Proposed` y testigo anti-debilitamiento (`Auth001SafetyProp`). |

Comando de verificación registrado en `CLAIMS.toml`:
```bash
lean proof/lean/BabylonTrace.lean && lean proof/lean/AX0.lean
```

---

### 2. Corpus Constructivo en [`Babylon.lean`](./lean/Babylon.lean)

| Métrica | Valor Verificado |
| :--- | :--- |
| **Líneas de código** | 644 líneas |
| **Representación Aritmética** | 100% `Rat` ($\mathbb{Q}$) y `Nat` (Cero `Float` IEEE-754) |
| **Axiomas de usuario (`axiom`)** | 0 |
| **Teoremas (`theorem`)** | 26 demostrados constructivamente |
| **`sorry` activos** | 0 |

| Dominio en `Babylon.lean` | Descripción |
| :--- | :--- |
| **Desintegración Bayesiana (`Rat`)** | Cotas algebraicas exactas en $\mathbb{Q}$ y disyuntor de divergencia. |
| **Monitor Tonnetz (`Rat`)** | Invariantes armónicos discretos sin deriva de coma flotante. |
| **Ciclos de Aeones y Caché 64B** | Modelos discretos de reciclaje de estado y alineación de 64 bytes. |
| **Aritmética Sexagesimal (`Q60`)** | Conmutatividad fraccional exacta e involución sobre base 60. |
| **Acumulador Causal MMR y DAG** | Cotas logarítmicas de inclusión y orden parcial causal de Lamport. |

---

### 3. Módulos Especializados Adicionales y Paquetes (`proof/lean/` y `proof/bundles/`)

- **Envoltorios y Protocolos (`proof/lean/`):** `CanonicalEnvelope.lean`, `CanonicalHead.lean`, `TicketEnvelope.lean`, `AcsEnvelope.lean`, `NemesisWave4.lean`, `C5Affine.lean`, `C5PortHamiltonian.lean`, `CognitiveTransitionAlgebra.lean`, entre otros.
- **Paquetes de Atestación Históricos (`proof/bundles/`):** `attestation_bundle_v1/`, `attestation_bundle_v2/` y `artifact_bundle_v3/`.

---

## ⚙️ Compilación Completa con Lake

```bash
cd proof/lean
lake build
```
