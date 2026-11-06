# BABYLON-60: Ontología Canónica Congelada v1.0.0

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>


> **Directiva de Congelamiento Semántico (v1.0.0):**  
> *«Dejar de cambiar continuamente los conceptos fundamentales del producto y empezar a construirlos.»*  
> La implementación (código bare-metal, UX, algoritmos, backends) es mutable; la ontología (entidades, significados, tipos de relación y leyes de conservación) queda fijada bajo SemVer formal: `1.0 -> 1.1` (cambios compatibles y aditivos), `1.x -> 2.0` (ruptura semántica mayor).

---

## 1. Los Tres Dominios Ortogonales Cerrados

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                CORTEX (REMEMBER)                                │
├─────────────────────┬───────────────────────────────────────────────────────────┤
│ Entidad             │ Definición Semántica Invariante                           │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ • SourceRecord      │ Registro de origen original inmutable auditado con hash.  │
│ • MemoryEvent       │ Evento discreto de ingesta o traza indexada desde Source. │
│ • IdeaThread        │ Hilo conceptual y recurrente que agrupa MemoryEvents.     │
│ • Inference         │ Interpretación probabilística derivada por un modelo.     │
│ • ProposalContext   │ Contexto estructurado deliberativo hacia Trust Boundary.  │
└─────────────────────┴───────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                BABYLON (CONTROL)                                │
├─────────────────────┬───────────────────────────────────────────────────────────┤
│ Entidad             │ Definición Semántica Invariante                           │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ • Authority         │ Principal soberano (Touch ID, Secure Enclave, Kernel).    │
│ • Capability        │ Token de permiso delimitado en ámbito, recurso y época.   │
│ • Policy            │ Regla determinista de control y salvaguarda (Fail-Closed).│
│ • Resource          │ Entidad física o lógica sujeta a mediación (VFS, Red...). │
│ • EffectRequest     │ Petición formal de invocación de mutación física.         │
│ • Decision          │ Veredicto tras evaluar (Auth, Cap, Pol, Res, Eff, Ctx, Ep)│
│ • Effect            │ Transición de estado observable mediada por BABYLON.      │
│ • EffectOutcome     │ Consecuencia física observada y contrastada en silicio.   │
│ • Receipt           │ Recibo criptográfico que documenta evidencia del outcome. │
└─────────────────────┴───────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 NEMESIS (VERIFY)                                │
├─────────────────────┬───────────────────────────────────────────────────────────┤
│ Entidad             │ Definición Semántica Invariante                           │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ • Assertion         │ Invariante formal o propiedad de seguridad falsable.      │
│ • FaultModel        │ Modelo explícito de perturbación o ataque adversarial.    │
│ • Test              │ Arnés ejecutable que confronta una Assertion con un Fallo.│
│ • Evidence          │ Telemetría física y recibos observados durante un Test.   │
│ • Attestation       │ Vinculación criptográfica [Sujeto + Evidencia + Env + T]. │
└─────────────────────┴───────────────────────────────────────────────────────────┘
```

---

## 2. Las Seis Correcciones Ontológicas Cardinales

### 2.1. `Effect`: Transición Observable, no solo Mutación Irreversible
El efecto es una **transición de estado externamente observable mediada por BABYLON**.  
La irreversibilidad es una **propiedad ortogonal del efecto**, no su definición:
```text
Effect
├── Reversible     (ej. archivo temporal con rollback, lock en memoria)
├── Compensatable  (ej. transacción en base de datos con reverse-delta / SAGA)
└── Irreversible   (ej. borrado criptomecánico unlink-quarantine, tx PoW L1)
```

### 2.2. La 7-Tupla de Autorización (`EffectRequest` y `Decision`)
Una `Policy` jamás autoriza sola de forma aislada. La evaluación formal de gobernanza requiere la 7-tupla canónica:
```text
(Authority, Capability, Policy, Resource, Effect, Context, Epoch)
```
Flujo de decisión:
```text
EffectRequest
      │
      ▼
AuthorizationDecision (evalúa la 7-tupla)
      │
      ▼
ALLOW / DENY / REQUIRE_APPROVAL / SECURITY_ABORT
```

### 2.3. `Receipt` registra Evidencia sobre `EffectOutcome` (No "prueba" el Effect)
Un recibo no es una prueba óntica de verdad universal exterior (`RECEIPT ≠ TRUTH`). Un API o driver puede retornar `200 OK` y el territorio divergir posteriormente.  
El recibo certifica lo que BABYLON observó y registró a través de sus **cinco fases causales**:
```text
1. REQUESTED   ──► Petición formal registrada en el broker.
2. AUTHORIZED  ──► Decisión afirmativa (ALLOW) tras evaluar la tupla.
3. DISPATCHED  ──► Despacho emitido al driver de silicio o red.
4. OBSERVED    ──► Medición física del estado resultante (pre vs post).
5. COMMITTED   ──► Sello inmutable en ledger append-only (WORM).
```

### 2.4. `Attestation`: Vinculación Criptográfica de Evidencia
Una firma no hace que una aserción sea verdadera (`ATTESTATION ≠ TRUTH`). Una firma atesta autenticidad e integridad respecto a una clave:
```text
Evidence ──supports / falsifies──► Assertion

Attestation ──binds──►
    Assertion
    Evidence
    Artifact (Digest binario)
    Environment (Digest kernel, CPU, toolchain)
    Timestamp
```

### 2.5. NEMESIS como Martillo Popperiano (`challenges / attempts to falsify`)
NEMESIS no es un oráculo dogmático de "verificación absoluta". NEMESIS es un motor de falsación adversarial:
```text
NEMESIS / FaultModel ──challenges──► Assertion
```
Estados epistémicos de la aserción:
- `UNTESTED`: Declarada en especificación formal, sin campaña de pruebas ejecutada.
- `SUPPORTED`: Sometida a modelos de fallo sin haber sido refutada hasta la fecha.
- `FALSIFIED`: Refutada empíricamente mediante un contraejemplo reproducible.
- `STALE`: Invalidada por deriva de código, entorno o caducidad temporal.

### 2.6. La Frontera de Confianza CORTEX ⇎ BABYLON (Veto a la Autoridad Estocástica)
CORTEX jamás puede escalar semánticamente a Autoridad:
```text
SOURCE
  ↓
MemoryEvent
  ↓
IdeaThread
  ↓
Inference
  ↓
Proposal / Context
  ║
  ║  TRUST BOUNDARY (Frontera Inviolable)
  ║
Authority
  ↓
Capability
  ↓
EffectRequest ──► Decision ──► Effect ──► EffectOutcome ──► Receipt
```
Leyes de contorno:
$$\text{Inference} \not\Rightarrow \text{Authority}$$
$$\text{Inference} \not\Rightarrow \text{Capability}$$

---

## 3. Las Diez Leyes Ontológicas Invariantes (O1 - O10)

```text
O1   SOURCE ≠ INFERENCE
     Ningún dato de origen puede falsearse como inferencia, ni una inferencia simular ser fuente primaria.

O2   INFERENCE ≠ AUTHORITY
     Ningún modelo estocástico o probabilidad generativa posee autoridad por sí mismo.

O3   AUTHORITY ≠ CAPABILITY
     Poseer un rol de autoridad no equivale a tener una capacidad de ejecución sin token explícito.

O4   REQUEST ≠ DECISION
     Una solicitud de mutación no predetermina su aprobación; requiere arbitraje de la 7-tupla.

O5   DECISION ≠ EFFECT
     Un veredicto ALLOW no es la mutación física; requiere despacho y ejecución en silicio.

O6   EFFECT ≠ OBSERVED OUTCOME
     El comando despachado no es idéntico a lo que el hardware o el mundo exterior terminan haciendo.

O7   RECEIPT ≠ TRUTH
     Un recibo atesta lo observado/registrado por el broker, no la infalibilidad ontológica del universo.

O8   EVIDENCE ≠ ASSERTION
     La evidencia es el registro físico medido; la aserción es la hipótesis formal sometida a falsación.

O9   ATTESTATION ≠ TRUTH
     Una firma certifica el vínculo sujeto-evidencia-entorno, no la verdad física de lo afirmado.

O10  UI ≠ AUTHORITY
     Ninguna interfaz gráfica o visualización puede emitir efectos; es mera proyección de evidencia.
```

### Ley Transversal Fundacional
$$\boxed{\text{No stochastic interpretation shall create authority by itself}}$$

---

## 4. Política de Versionado (SemVer)
- **v1.0.0 (Freeze Canónico):** Vocabulario, esquemas, tipos y leyes O1-O10 congelados.
- **v1.x.y (Cambios Compatibles):** Entidades auxiliares, campos de metadatos opcionales, extensiones de drivers.
- **v2.0.0 (Ruptura Semántica):** Alteración de las leyes O1-O10, cambio de tupla de autorización o ruptura del ciclo de vida de Receipts.
