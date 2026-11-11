---
title: Censo formal Lean 4 — declaraciones, modelos y alcance verificable
status: Evidencia documental derivada del inventario versionado
revision: V1-2026-11-08
---

# Censo Lean 4 de BABYLON-60: 144 declaraciones, alcance verificable

**Fuente de datos:** [inventario canónico JSON](evidence/lean-census-372-v511.json) (revisión de origen `60140d24ff44505d5ebb566324f1db6a9c2e51a1`, toolchain `leanprover/lean4:v4.34.0-rc2`). **Marco metodológico:** [AUDIT_LEAN_SCOPE_2026.md](AUDIT_LEAN_SCOPE_2026.md).

> **Regla de interpretación:** el nombre histórico de una declaración Lean no amplía lo que demuestra su firma. Las conclusiones sobre modelos discretos, registros, booleanos, secuencias y codecs **no son garantías físicas, analíticas ni de runtime Rust** salvo que exista un teorema de correspondencia independiente. Este documento conserva los nombres públicos para trazabilidad y añade la clasificación semántica, no renombra APIs.

> **Estado de verificación:** este documento está construido a partir del inventario JSON versionado y no implica una nueva compilación de Lean, comprobación de `#print axioms` ni cotejo byte a byte con el árbol de trabajo local al 8 de noviembre de 2026. Los hashes de fuente, dependencias y localizaciones son los contenidos en ese inventario.

## 1. Recuento y alcance

| Magnitud | Valor | Interpretación |
|:--|--:|:--|
| Módulos `.lean` propietarios | **26** | **22** con declaración `theorem`, **4** auxiliares sin teoremas |
| Declaraciones `theorem` | **144** | **142** en fuentes positivas del modelo y **2** fixtures negativos (`#060`, `#066`) |
| `def` + `inductive` | **228** | 205 `def` + 23 `inductive`; suman **372** con los 144 `theorem` |
| `structure` + `abbrev` | **47** | 34 `structure` + 13 `abbrev` |
| Declaraciones totales | **419** | 144 teoremas + 275 construcciones no-teorema |

### 1.1 Clasificación metodológica

| Clase | Recuento | Alcance |
|:--|--:|:--|
| `U-CODEC` | **37** | Leyes de representación, roundtrip e inyectividad bajo hipótesis de codec |
| `U-IND` | **9** | Propiedades inductivas sobre trazas y listas del modelo |
| `U-ALG` | **53** | Identidades, proyección de hipótesis, restricciones o resultados de un paso |
| `W-EX` | **6** | Testigos y estructuras de existencia; verificar obligaciones internas |
| `I-DEC` | **37** | Evaluación cerrada positiva de casos concretos |
| `NEG-FIXTURE` | **2** | Fuente negativa de rechazo esperado; no teorema aceptado como `= true` |
| **Total** | **144** | La categoría describe alcance, no complejidad ni cobertura de producción |

### 1.2 Los 26 módulos, sin confundir código auxiliar con pruebas

| Módulo | Declaraciones `theorem` | Rango | Estado de inventario |
|:--|--:|:--|:--|
| [`AX0.lean`](../../proof/lean/AX0.lean) | 7 | #001–#007 | Fuente con teoremas del modelo |
| [`AcsEnvelope.lean`](../../proof/lean/AcsEnvelope.lean) | 20 | #008–#027 | Fuente con teoremas del modelo |
| [`Babylon.lean`](../../proof/lean/Babylon.lean) | 26 | #028–#053 | Fuente con teoremas del modelo |
| [`BabylonAOTOracle.lean`](../../proof/lean/BabylonAOTOracle.lean) | 0 | — | Auxiliar: sin `theorem` |
| [`BabylonAeonChain.lean`](../../proof/lean/BabylonAeonChain.lean) | 5 | #054–#058 | Fuente con teoremas del modelo |
| [`BabylonAeonStress.lean`](../../proof/lean/BabylonAeonStress.lean) | 1 | #059 | Fuente con teoremas del modelo |
| [`BabylonAutoTrace.lean`](../../proof/lean/BabylonAutoTrace.lean) | 1 | #060 | Fixture negativo: rechazo esperado |
| [`BabylonL0Ledger.lean`](../../proof/lean/BabylonL0Ledger.lean) | 5 | #061–#065 | Fuente con teoremas del modelo |
| [`BabylonOracle.lean`](../../proof/lean/BabylonOracle.lean) | 0 | — | Auxiliar: sin `theorem` |
| [`BabylonStressCorrupt.lean`](../../proof/lean/BabylonStressCorrupt.lean) | 1 | #066 | Fixture negativo: rechazo esperado |
| [`BabylonStressTrace.lean`](../../proof/lean/BabylonStressTrace.lean) | 1 | #067 | Fuente con teoremas del modelo |
| [`BabylonTrace.lean`](../../proof/lean/BabylonTrace.lean) | 17 | #068–#084 | Fuente con teoremas del modelo |
| [`C5Affine.lean`](../../proof/lean/C5Affine.lean) | 1 | #085 | Fuente con teoremas del modelo |
| [`C5PortHamiltonian.lean`](../../proof/lean/C5PortHamiltonian.lean) | 3 | #086–#088 | Fuente con teoremas del modelo |
| [`CanonicalEnvelope.lean`](../../proof/lean/CanonicalEnvelope.lean) | 7 | #089–#095 | Fuente con teoremas del modelo |
| [`CanonicalHead.lean`](../../proof/lean/CanonicalHead.lean) | 4 | #096–#099 | Fuente con teoremas del modelo |
| [`Destiladora_838c463da193b48f.lean`](../../proof/lean/Destiladora_838c463da193b48f.lean) | 7 | #100–#106 | Fuente con teoremas del modelo |
| [`ExampleSeqlockTrace.lean`](../../proof/lean/ExampleSeqlockTrace.lean) | 1 | #107 | Fuente con teoremas del modelo |
| [`HolographicPoC.lean`](../../proof/lean/HolographicPoC.lean) | 0 | — | Auxiliar: sin `theorem` |
| [`LarsaEquivocationSafety.lean`](../../proof/lean/LarsaEquivocationSafety.lean) | 7 | #108–#114 | Fuente con teoremas del modelo |
| [`MolochLandauer.lean`](../../proof/lean/MolochLandauer.lean) | 5 | #115–#119 | Fuente con teoremas del modelo |
| [`NavierStokesBKM.lean`](../../proof/lean/NavierStokesBKM.lean) | 5 | #120–#124 | Fuente con teoremas del modelo |
| [`NavierStokesOracle.lean`](../../proof/lean/NavierStokesOracle.lean) | 0 | — | Auxiliar: sin `theorem` |
| [`NavierStokesSobolevKato.lean`](../../proof/lean/NavierStokesSobolevKato.lean) | 8 | #125–#132 | Fuente con teoremas del modelo |
| [`NemesisWave4.lean`](../../proof/lean/NemesisWave4.lean) | 6 | #133–#138 | Fuente con teoremas del modelo |
| [`TicketEnvelope.lean`](../../proof/lean/TicketEnvelope.lean) | 6 | #139–#144 | Fuente con teoremas del modelo |

## 2. Correcciones críticas de semántica

Los alias siguientes son **etiquetas editoriales de alcance**, no identificadores exportados por Lean. Las declaraciones originales permanecen enlazadas para no romper referencias, imports ni APIs.

| ID | Nombre público histórico | Etiqueta semántica de alcance | Límite no demostrado |
|:--|:--|:--|:--|
| `#044` | `theorem_chentsov_markov_monotonicity` | `chentsov_contraction_hypothesis_passthrough` | Conclusión idéntica a la hipótesis `h_contractive`; no demuestra Chentsov ni modela canal de Markov |
| `#064` | `merkle_root_uniqueness` | `append_entry_injective` | Inyectividad de inserción bajo `TriggerAllowsInsert`; no demuestra resistencia criptográfica a colisiones |
| `#071` | `no_torn_reads_universal` | `trace_reads_even_on_validation` | Paridad en eventos del modelo; no acredita atomicidad de payloads ni barreras de memoria del runtime |
| `#132` | `millennium_navier_stokes_regular_by_decide` | `bkm_monitor_flags_accepted_by_decide` | Tres campos booleanos ya puestos a `true`; no acredita regularidad PDE ni resuelve Navier-Stokes |

### 2.1 Otros límites de alcance que deben permanecer visibles

| Referencias | Qué se verifica | Qué no se sigue |
|:--|:--|:--|
| `#040–#043` | XOR, divisibilidad por 60 y aritmética sobre funciones discretas | Liouville, homotopía, geometría de Fisher o estructura MMR real |
| `#046–#047` | Desigualdad de división Nat y concordancia parcial de dos funciones Lean | Terminación del agente o equivalencia ABI/FFI con Rust/C |
| `#060`, `#066` | Fallo semántico esperado de fixtures negativos | Pruebas positivas compiladas |
| `#075–#081` | Predicados y rechazos de un estado de gate modelado | No interferencia de CPU, aislamiento host, autorización de todos los efectos reales |
| `#085`, `#087–#088` | Un constructor `consumed`, un descenso concreto, tres valores módulo 64 | Seguridad global de heap, disipación universal, alineamiento físico |
| `#108–#114` | Aritmética de umbrales y testigos de una estructura | Consenso BFT completo frente a equivocation o particiones adversarias |
| `#115–#119` | Comparaciones de función contable sobre `Nat` | Energía termodinámica medida o equilibrio estratégico general |
| `#120–#132` | Tests de monitores y algunos campos axiomáticamente exigidos en estructuras | Existencia, suavidad o regularidad analítica de soluciones Navier-Stokes |
| `#133–#138` | Evaluaciones concretas de trazas y verificadores | Comportamiento universal de un host o despliegue real |

### 2.2 Distinción formal entre monitor discreto y garantía analítica

Una declaración como `isMillenniumRegular cert = true` es una evaluación de una función booleana sobre un registro `cert`. Para inferir una propiedad PDE haría falta modelar soluciones (velocidad, presión, dominio, condiciones iniciales, regularidad funcional) y justificar la relación entre el monitor y tales soluciones. Ninguna de esas obligaciones aparece en la firma `#132` del inventario. La aceptación booleana **no constituye por sí misma un certificado de regularidad analítica**.

De forma análoga, `TraceReadsEven trace` se refiere a campos de eventos Lean. Para concluir ausencia de lecturas desgarradas en Rust serían necesarios un modelo de acceso y orden de memoria, hipótesis de concurrencia explícitas y una prueba de refinamiento del runtime al modelo.

## 3. Registro 1:1 de las 144 declaraciones `theorem`

En cada entrada se conservan el **nombre público**, la **firma inventariada**, la **clase de resultado** y las **dependencias axiomáticas reportadas**. El texto «alcance» procede del JSON y no amplía la proposición.

### [AX0.lean](../../proof/lean/AX0.lean)

**#001 · [`auth_001_valid_execution`](../../proof/lean/AX0.lean#L65)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem auth_001_valid_execution : validateTrace trace_happy .Proposed = true`
- **Alcance documentado:** Comprobación cerrada por rfl sobre la traza concreta trace_happy de 3 eventos en la FSM abstracta.

**#002 · [`auth_001_reject_double_dispatch`](../../proof/lean/AX0.lean#L70)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem auth_001_reject_double_dispatch : validateTrace trace_double_dispatch .Proposed = false`
- **Alcance documentado:** Comprobación cerrada por rfl que rechaza la traza concreta trace_double_dispatch en la FSM abstracta.

**#003 · [`auth_001_reject_illegal_dispatch`](../../proof/lean/AX0.lean#L75)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem auth_001_reject_illegal_dispatch : validateTrace trace_illegal_dispatch .Proposed = false`
- **Alcance documentado:** Comprobación cerrada por rfl que rechaza la traza concreta trace_illegal_dispatch en la FSM abstracta.

**#004 · [`auth_001_crash_recovery`](../../proof/lean/AX0.lean#L80)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem auth_001_crash_recovery : validateTrace trace_crash .Proposed = true`
- **Alcance documentado:** Comprobación cerrada por rfl de la traza concreta trace_crash ([.reserve, .dispatch, .ackCrash]); no demuestra recuperación general de estado persistido en disco ni reconciliación de efectos externos.

**#005 · [`max_dispatches_from_state`](../../proof/lean/AX0.lean#L98)** · Clase `U-IND` · Axiomas: `propext`

- **Firma:** `theorem max_dispatches_from_state (trace : List AuthEvent) (s : AuthState) : validateTrace trace s = true → countDispatches trace ≤ maxAllowedDispatches s`
- **Alcance documentado:** Lema inductivo universal sobre cualquier traza finita admitida desde el estado s en la FSM AuthState.

**#006 · [`auth_001_universal_inductive_safety`](../../proof/lean/AX0.lean#L144)** · Clase `U-IND` · Axiomas: `propext`

- **Firma:** `theorem auth_001_universal_inductive_safety (trace : List AuthEvent) : validateTrace trace .Proposed = true → countDispatches trace ≤ 1`
- **Alcance documentado:** Cota inductiva universal: toda traza aceptada desde Proposed contiene como máximo un evento dispatch (0 o 1) en el modelo FSM; no establece liveness, persistencia física ni correspondencia con syscalls del SO.

**#007 · [`verifiedAuthInvariant`](../../proof/lean/AX0.lean#L190)** · Clase `W-EX` · Axiomas: `propext`

- **Firma:** `theorem verifiedAuthInvariant : VerifiedAuthInvariant`
- **Alcance documentado:** Empaqueta la cota inductiva universal (#006) con el testigo no vacío trace_happy (patrón AP-10 VerifiedAuthInvariant).

### [AcsEnvelope.lean](../../proof/lean/AcsEnvelope.lean)

**#008 · [`B60.ACS.typedCose_decode_encode`](../../proof/lean/AcsEnvelope.lean#L169)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedCose_decode_encode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (x : α × Bytes) (h : (typedCose alg c).valid x) : decodeChecked (typedCose alg c) ((typedCose alg c).encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`typedCose_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#009 · [`B60.ACS.typedCose_encode_decode`](../../proof/lean/AcsEnvelope.lean#L174)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedCose_encode_decode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (wire : Bytes) (x : α × Bytes) (h : decodeChecked (typedCose alg c) wire = some x) : (typedCose alg c).encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`typedCose_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#010 · [`B60.ACS.typedCose_decode_valid`](../../proof/lean/AcsEnvelope.lean#L178)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedCose_decode_valid (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (wire : Bytes) (x : α × Bytes) (h : decodeChecked (typedCose alg c) wire = some x) : (typedCose alg c).valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `AcsEnvelope.lean` (`typedCose_decode_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#011 · [`B60.ACS.typedSignature_decode_encode`](../../proof/lean/AcsEnvelope.lean#L182)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedSignature_decode_encode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (x : α) (h : (typedSignatureStructure alg c).valid x) : decodeChecked (typedSignatureStructure alg c) ((typedSignatureStructure alg c).encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`typedSignature_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#012 · [`B60.ACS.typedSignature_encode_decode`](../../proof/lean/AcsEnvelope.lean#L187)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedSignature_encode_decode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (wire : Bytes) (x : α) (h : decodeChecked (typedSignatureStructure alg c) wire = some x) : (typedSignatureStructure alg c).encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`typedSignature_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#013 · [`B60.ACS.typedSignature_decode_valid`](../../proof/lean/AcsEnvelope.lean#L191)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem typedSignature_decode_valid (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] (wire : Bytes) (x : α) (h : decodeChecked (typedSignatureStructure alg c) wire = some x) : (typedSignatureStructure alg c).valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `AcsEnvelope.lean` (`typedSignature_decode_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#014 · [`B60.ACS.call_decoded_valid`](../../proof/lean/AcsEnvelope.lean#L200)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem call_decoded_valid (wire : Bytes) (x : Call) (h : decodeCall wire = some x) : callCodec.valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `AcsEnvelope.lean` (`call_decoded_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#015 · [`B60.ACS.grant_decoded_valid`](../../proof/lean/AcsEnvelope.lean#L203)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem grant_decoded_valid (wire : Bytes) (x : Grant) (h : decodeGrant wire = some x) : grantCodec.valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `AcsEnvelope.lean` (`grant_decoded_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#016 · [`B60.ACS.forensic_decoded_valid`](../../proof/lean/AcsEnvelope.lean#L206)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem forensic_decoded_valid (wire : Bytes) (x : Forensic) (h : decodeForensic wire = some x) : forensicCodec.valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `AcsEnvelope.lean` (`forensic_decoded_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#017 · [`B60.ACS.call_decode_encode`](../../proof/lean/AcsEnvelope.lean#L210)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem call_decode_encode (x : Call) (h : callCodec.valid x) : decodeCall (callCodec.encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`call_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#018 · [`B60.ACS.grant_decode_encode`](../../proof/lean/AcsEnvelope.lean#L213)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem grant_decode_encode (x : Grant) (h : grantCodec.valid x) : decodeGrant (grantCodec.encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`grant_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#019 · [`B60.ACS.forensic_decode_encode`](../../proof/lean/AcsEnvelope.lean#L216)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem forensic_decode_encode (x : Forensic) (h : forensicCodec.valid x) : decodeForensic (forensicCodec.encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`forensic_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#020 · [`B60.ACS.call_encode_decode`](../../proof/lean/AcsEnvelope.lean#L219)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem call_encode_decode (wire : Bytes) (x : Call) (h : decodeCall wire = some x) : callCodec.encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`call_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#021 · [`B60.ACS.grant_encode_decode`](../../proof/lean/AcsEnvelope.lean#L222)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem grant_encode_decode (wire : Bytes) (x : Grant) (h : decodeGrant wire = some x) : grantCodec.encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`grant_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#022 · [`B60.ACS.forensic_encode_decode`](../../proof/lean/AcsEnvelope.lean#L225)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem forensic_encode_decode (wire : Bytes) (x : Forensic) (h : decodeForensic wire = some x) : forensicCodec.encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`forensic_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#023 · [`B60.ACS.call_injective`](../../proof/lean/AcsEnvelope.lean#L228)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem call_injective (x y : Call) (hx : callCodec.valid x) (hy : callCodec.valid y) (h : callCodec.encode x = callCodec.encode y) : x = y`
- **Alcance documentado:** Inyectividad universal del codificador sobre el subconjunto de entradas que satisfacen el predicado `.valid` en `AcsEnvelope.lean` (`call_injective`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#024 · [`B60.ACS.cose_decode_encode`](../../proof/lean/AcsEnvelope.lean#L231)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem cose_decode_encode (alg : Algorithm) (x : Bytes × Bytes) (h : (coseSign1 alg).valid x) : decode (coseSign1 alg) ((coseSign1 alg).encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`cose_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#025 · [`B60.ACS.cose_encode_decode`](../../proof/lean/AcsEnvelope.lean#L234)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem cose_encode_decode (alg : Algorithm) (wire : Bytes) (x : Bytes × Bytes) (h : decode (coseSign1 alg) wire = some x) : (coseSign1 alg).encode x = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`cose_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#026 · [`B60.ACS.signature_decode_encode`](../../proof/lean/AcsEnvelope.lean#L237)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem signature_decode_encode (alg : Algorithm) (payload : Bytes) (h : (signatureStructure alg).valid payload) : decode (signatureStructure alg) ((signatureStructure alg).encode payload) = some payload`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `AcsEnvelope.lean` (`signature_decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#027 · [`B60.ACS.signature_encode_decode`](../../proof/lean/AcsEnvelope.lean#L240)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem signature_encode_decode (alg : Algorithm) (wire payload : Bytes) (h : decode (signatureStructure alg) wire = some payload) : (signatureStructure alg).encode payload = wire`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `AcsEnvelope.lean` (`signature_encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

### [Babylon.lean](../../proof/lean/Babylon.lean)

**#028 · [`Babylon.extincion_origen_espurio`](../../proof/lean/Babylon.lean#L38)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem extincion_origen_espurio {X Y : Type} {p : ProbDist X} {f : Morphism X Y} (bd : BayesianDisintegration p f) (x_fake : X) (y : Y) (h : p x_fake = 0) : bd.f_dag_p y x_fake = 0`
- **Alcance documentado:** Proyecta el campo h_no_hallucination exigido al construir BayesianDisintegration: conserva p x_fake = 0 en f_dag_p; no identifica falsedad de origen ni modela adversarios.

**#029 · [`Babylon.extincion_origen_espurio_constructiva`](../../proof/lean/Babylon.lean#L44)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem extincion_origen_espurio_constructiva {X Y : Type} (prior : ProbDist X) (f : Morphism X Y) (pushforward : Y → Nat) (x : X) (y : Y) (h_prior : prior x = 0) : bayesian_inverse prior f pushforward y x = 0`
- **Alcance documentado:** Rama cero por definición de bayesian_inverse sobre Nat cuando prior x = 0; cociente entero truncado sin normalización probabilística.

**#030 · [`Babylon.circuit_breaker_activado`](../../proof/lean/Babylon.lean#L52)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem circuit_breaker_activado {X Y : Type} {p : ProbDist X} {f : Morphism X Y} (bd : BayesianDisintegration p f) (x : X) (y_unseen : Y) (h : bd.pushforward y_unseen = 0) : bd.f_dag_p y_unseen x = 0`
- **Alcance documentado:** Proyecta el campo h_circuit_breaker de BayesianDisintegration cuando pushforward y_unseen = 0; fila cero por convención de subprobabilidad/rechazo, no aborto físico.

**#031 · [`Babylon.circuit_breaker_activado_constructiva`](../../proof/lean/Babylon.lean#L58)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem circuit_breaker_activado_constructiva {X Y : Type} (prior : ProbDist X) (f : Morphism X Y) (pushforward : Y → Nat) (x : X) (y_unseen : Y) (h : pushforward y_unseen = 0) : bayesian_inverse prior f pushforward y_unseen x = 0`
- **Alcance documentado:** Rama de denominador cero en bayesian_inverse sobre Nat (devuelve 0 para todo x cuando pushforward y_unseen = 0); no construye un posterior normalizado en el sentido de Markov/Fritz.

**#032 · [`Babylon.resiliencia_bft_inyeccion`](../../proof/lean/Babylon.lean#L67)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem resiliencia_bft_inyeccion {X Y : Type} {p : ProbDist X} {f : Morphism X Y} (bd : BayesianDisintegration p f) (x_fake : X) (y : Y) (h_prior : p x_fake = 0) : bd.f_dag_p y x_fake = 0`
- **Alcance documentado:** Proposición idéntica a #028 (proyecta bd.h_no_hallucination bajo p x_fake = 0); el nombre histórico no añade protocolo BFT ni modelo de prompt injection.

**#033 · [`Babylon.homeostasis_tonnetz_garantizada`](../../proof/lean/Babylon.lean#L97)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem homeostasis_tonnetz_garantizada (m : TonnetzMonitor) : m.phi 0 0 = (TonnetzState.HomeostaticPure, 0)`
- **Alcance documentado:** Extrae el campo h_homeostasis del registro TonnetzMonitor en (0, 0); no mide percepción acústica ni límites físicos.

**#034 · [`Babylon.lemma_monotonic_entropy_growth`](../../proof/lean/Babylon.lean#L129)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem lemma_monotonic_entropy_growth (s1 s2 : AeonState) (_h_same : s1.aeon_id = s2.aeon_id) (_h_p1 : s1.phase = AeonPhase.Expansion) (_h_p2 : s2.phase = AeonPhase.Expansion) (h_growth : s1.tick ≤ s2.tick → s1.entropy ≤ s2.entropy) (h_t : s1.tick ≤ s2.tick) : s1.entropy ≤ s2.entropy`
- **Alcance documentado:** Aplica la implicación hipótética h_growth : s1.tick ≤ s2.tick → s1.entropy ≤ s2.entropy a h_t; la monotonía se recibe como hipótesis y no se deriva de termodinámica.

**#035 · [`Babylon.lemma_hot_memory_invariance`](../../proof/lean/Babylon.lean#L139)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem lemma_hot_memory_invariance (s : AeonState) : s.hot_memory_bytes ≤ HOT_MEMORY_LIMIT`
- **Alcance documentado:** Reescribe el campo h_bounded : s.hot_memory_bytes = 64 del registro AeonState; acota un campo Nat, no mide layout ni heap real.

**#036 · [`Babylon.lemma_conformal_hot_dissipation_zero`](../../proof/lean/Babylon.lean#L156)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem lemma_conformal_hot_dissipation_zero (s_sat : AeonState) (next_id : Nat) (merkle : Nat) : let s_next := conformal_reset s_sat next_id merkle s_next.entropy = 0 ∧ s_next.exergy = s_sat.exergy ∧ s_next.hot_memory_bytes = HOT_MEMORY_LIMIT`
- **Alcance documentado:** Igualdades definicionales de los campos de conformal_reset por reducción (entropy = 0, exergy conservada, hot_memory_bytes = 64); no contiene magnitud física de calor.

**#037 · [`Babylon.theorem_penrose_landauer_cycle_stability`](../../proof/lean/Babylon.lean#L163)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_penrose_landauer_cycle_stability (s_sat : AeonState) (next_id : Nat) (merkle : Nat) : let s_next := conformal_reset s_sat next_id merkle s_next.entropy = 0 ∧ s_next.hot_memory_bytes ≤ HOT_MEMORY_LIMIT ∧ s_next.phase = AeonPhase.Expansion`
- **Alcance documentado:** Valores y cota de campos del registro construido por conformal_reset; no demuestra estabilidad cíclica física ni cosmológica.

**#038 · [`Babylon.theorem_landauer_cache_bypass`](../../proof/lean/Babylon.lean#L172)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_landauer_cache_bypass (s_sat : AeonState) : let s_next := conformal_reset s_sat (s_sat.aeon_id + 1) s_sat.merkle_root s_next.entropy = 0 ∧ s_next.exergy = s_sat.exergy ∧ s_next.hot_memory_bytes = HOT_MEMORY_LIMIT ∧ s_next.aeon_id = s_sat.aeon_id + 1`
- **Alcance documentado:** Igualdades definicionales sobre el registro devuelto por conformal_reset; el nombre histórico no demuestra un bypass físico del límite de Landauer.

**#039 · [`Babylon.theorem_sexa_fraction_exact`](../../proof/lean/Babylon.lean#L199)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_sexa_fraction_exact (a b : Tick60) : (add_tick60 a b).sexa_fraction = (add_tick60 b a).sexa_fraction`
- **Alcance documentado:** Conmutatividad de la coordenada fraccionaria (add_tick60 a b).sexa_fraction = (add_tick60 b a).sexa_fraction; no prueba por sí sola exactitud de representación del valor completo con acarreo.

**#040 · [`Babylon.theorem_liouville_involution`](../../proof/lean/Babylon.lean#L205)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem theorem_liouville_involution (x y : Nat) : (x ^^^ y) ^^^ y = x`
- **Alcance documentado:** Identidad algebraica involutiva de XOR sobre Nat ((x ^^^ y) ^^^ y = x); el nombre histórico no formaliza conservación de volumen en espacio de fases (Liouville).

**#041 · [`Babylon.theorem_homotopy_closed_path`](../../proof/lean/Babylon.lean#L210)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem theorem_homotopy_closed_path (winding_phase : Int) (h : winding_phase % 60 = 0) : ∃ (k : Int), winding_phase = 60 * k`
- **Alcance documentado:** Existencia de cociente entero k tal que winding_phase = 60 * k cuando winding_phase % 60 = 0; propiedad de divisibilidad en Int, no grupo fundamental ni homotopía topológica.

**#042 · [`Babylon.theorem_mmr_logarithmic_bound`](../../proof/lean/Babylon.lean#L218)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_mmr_logarithmic_bound (n : Nat) : mmr_peaks_bound n ≤ n.log2 + 1`
- **Alcance documentado:** Reflexividad sobre la función mmr_peaks_bound n definida como n.log2 + 1; no cuenta picos de una estructura Merkle Mountain Range real.

**#043 · [`Babylon.theorem_fisher_pythagorean_divergence`](../../proof/lean/Babylon.lean#L241)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_fisher_pythagorean_divergence (d_pq d_qr : Nat) (cross_term : Nat) (h_ortho : cross_term = 0) : d_pq + d_qr + cross_term = d_pq + d_qr`
- **Alcance documentado:** Identidad aditiva en Nat cuando el término cruzado se supone cero (cross_term = 0); no define divergencia KL ni variedad de Fisher.

**#044 · [`Babylon.theorem_chentsov_markov_monotonicity`](../../proof/lean/Babylon.lean#L247)** · Clase `U-ALG` · Axiomas: `ninguno registrado` · **Alias editorial:** `chentsov_contraction_hypothesis_passthrough`

- **Firma:** `theorem theorem_chentsov_markov_monotonicity (fisher_in fisher_out : Nat) (h_contractive : fisher_out ≤ fisher_in) : fisher_out ≤ fisher_in`
- **Alcance documentado:** Implicación identidad: recibe h_contractive : fisher_out ≤ fisher_in como hipótesis y la devuelve directamente (exact h_contractive); no define un canal de Markov ni demuestra el teorema de Chentsov.

**#045 · [`Babylon.theorem_agent_cheap_talk_rejection`](../../proof/lean/Babylon.lean#L273)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem theorem_agent_cheap_talk_rejection (reasoning_len payload_len ratio_max budget budget_max : Nat) (h_budget : ¬ (budget > budget_max)) (h_cheap : (reasoning_len > 100 && (reasoning_len / effective_payload payload_len > ratio_max)) = true) : evaluate_agent_intent reasoning_len payload_len ratio_max budget budget_max = AgentIntentVerdict.RejectedCheapTalk (reasoning_len / effective_payload payload_len)`
- **Alcance documentado:** Selecciona la rama RejectedCheapTalk de evaluate_agent_intent bajo las guardas booleanas de presupuesto y ratio; clasificador aritmético de longitudes, no detector semántico de confabulación.

**#046 · [`Babylon.theorem_agent_finite_horizon`](../../proof/lean/Babylon.lean#L282)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem theorem_agent_finite_horizon (total_energy step_cost : Nat) : (total_energy / step_cost) * step_cost ≤ total_energy`
- **Alcance documentado:** Desigualdad estándar de división entera en Nat ((total_energy / step_cost) * step_cost ≤ total_energy), válida incluso para step_cost = 0; no modela una relación de paso ni demuestra terminación.

**#047 · [`Babylon.theorem_ffi_semantic_isomorphism`](../../proof/lean/Babylon.lean#L296)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_ffi_semantic_isomorphism (s1 f1 s2 f2 : Nat) (h_f1 : f1 < FRACTION_BASE) (h_f2 : f2 < FRACTION_BASE) : (ffi_sexa_add_model s1 f1 s2 f2).2 = (add_tick60 ⟨s1, f1, h_f1⟩ ⟨s2, f2, h_f2⟩).sexa_fraction`
- **Alcance documentado:** Igualdad de la segunda componente entre dos funciones puras en Lean (ffi_sexa_add_model y add_tick60); no invoca código C externo ni verifica ABI o punteros FFI.

**#048 · [`Babylon.theorem_repl_closure`](../../proof/lean/Babylon.lean#L320)** · Clase `U-IND` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_repl_closure (steps : Nat) (s : ReplSession) : (run_repl_steps steps s).hot_manifest_bytes = HOT_MEMORY_LIMIT`
- **Alcance documentado:** Inducción sobre N pasos de run_repl_steps mostrando que el campo hot_manifest_bytes del registro ReplSession permanece igual a la constante 64.

**#049 · [`Babylon.theorem_causal_light_cone_preservation`](../../proof/lean/Babylon.lean#L341)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_causal_light_cone_preservation (e : CausalEdge) : e.from_ts < e.to_ts`
- **Alcance documentado:** Extrae el campo de orden estricto h_causal : from_ts < to_ts exigido al construir CausalEdge.

**#050 · [`Babylon.theorem_concurrent_wave_independence`](../../proof/lean/Babylon.lean#L346)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_concurrent_wave_independence (stage_u stage_v : Nat) (h_same_wave : stage_u = stage_v) (h_interfering : stage_u < stage_v) : False`
- **Alcance documentado:** Contradicción aritmética elemental entre las hipótesis simultáneas stage_u = stage_v y stage_u < stage_v; no modela memoria compartida ni ausencia de carreras en hilos reales.

**#051 · [`Babylon.b60_small_step_confluence`](../../proof/lean/Babylon.lean#L375)** · Clase `U-IND` · Axiomas: `ninguno registrado`

- **Firma:** `theorem b60_small_step_confluence (s s1 s2 : ReplSession) (h1 : SmallStep s s1) (h2 : SmallStep s s2) : s1 = s2 ∨ (∃ s3, SmallStep s1 s3 ∧ SmallStep s2 s3)`
- **Alcance documentado:** Propiedad de confluencia (diamante) para la relación funcional determinista SmallStep (cuyo paso es único por construcción sobre ReplSession).

**#052 · [`Babylon.theorem_toponym_stratum_retraction`](../../proof/lean/Babylon.lean#L437)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_toponym_stratum_retraction (lvl : EscalationStratum) : toponymToStratum (stratumToToponym lvl) = some lvl`
- **Alcance documentado:** Retracción finita por casos sobre los 4 constructores de EscalationStratum (toponymToStratum ∘ stratumToToponym = some).

**#053 · [`Babylon.theorem_parasitic_dir_quotient_invariance`](../../proof/lean/Babylon.lean#L451)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem theorem_parasitic_dir_quotient_invariance (lvl : EscalationStratum) (r : PrivilegeRing) (d1 d2 : Nat) : triadCausalQuotient ⟨lvl, r, d1⟩ = triadCausalQuotient ⟨lvl, r, d2⟩`
- **Alcance documentado:** Invarianza por proyección: triadCausalQuotient ignora el tercer campo parasitic_dirs_count del registro TriadTopologyState.

### [BabylonAeonChain.lean](../../proof/lean/BabylonAeonChain.lean)

**#054 · [`B60.Ledger.aeon_0_step`](../../proof/lean/BabylonAeonChain.lean#L1520)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_0_step : runAeon (some { seq := 0, writer := none }) aeon_0_events = some { seq := 1000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre el fragmento literal aeon_0_events (1.500 eventos, seq 0 → 1000).

**#055 · [`B60.Ledger.aeon_1_step`](../../proof/lean/BabylonAeonChain.lean#L3027)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_1_step : runAeon (some { seq := 1000, writer := none }) aeon_1_events = some { seq := 2000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre el fragmento literal aeon_1_events (1.500 eventos, seq 1000 → 2000).

**#056 · [`B60.Ledger.aeon_2_step`](../../proof/lean/BabylonAeonChain.lean#L4534)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_2_step : runAeon (some { seq := 2000, writer := none }) aeon_2_events = some { seq := 3000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre el fragmento literal aeon_2_events (1.500 eventos, seq 2000 → 3000).

**#057 · [`B60.Ledger.aeon_3_step`](../../proof/lean/BabylonAeonChain.lean#L6041)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_3_step : runAeon (some { seq := 3000, writer := none }) aeon_3_events = some { seq := 4000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre el fragmento literal aeon_3_events (1.500 eventos, seq 3000 → 4000).

**#058 · [`B60.Ledger.aeon_4_step`](../../proof/lean/BabylonAeonChain.lean#L7548)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_4_step : runAeon (some { seq := 4000, writer := none }) aeon_4_events = some { seq := 5000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre el fragmento literal aeon_4_events (1.500 eventos, seq 4000 → 5000).

### [BabylonAeonStress.lean](../../proof/lean/BabylonAeonStress.lean)

**#059 · [`B60.Ledger.aeon_valid`](../../proof/lean/BabylonAeonStress.lean#L1518)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem aeon_valid : runAeon (some { seq := 49000, writer := none }) aeon_events = some { seq := 50000, writer := none }`
- **Alcance documentado:** Comprobación cerrada sobre la lista literal aeon_events de 1.500 eventos (seq 49000 → 50000).

### [BabylonAutoTrace.lean](../../proof/lean/BabylonAutoTrace.lean)

**#060 · [`B60.Ledger.trace_is_paradox_free_auto`](../../proof/lean/BabylonAutoTrace.lean#L21)** · Clase `NEG-FIXTURE` · Axiomas: `N/A (negative fixture: expected decide rejection)`

- **Firma:** `theorem trace_is_paradox_free_auto : validateTrace auto_execution_trace = true`
- **Alcance documentado:** Fixture negativo de rechazo semántico esperado (AUDIT_LEAN_SCOPE_2026 §8): la lista auto_execution_trace contiene una transición inválida y decide refuta la igualdad = true.

### [BabylonL0Ledger.lean](../../proof/lean/BabylonL0Ledger.lean)

**#061 · [`Babylon60.L0Ledger.genesis_satisfies_invariant`](../../proof/lean/BabylonL0Ledger.lean#L90)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem genesis_satisfies_invariant (initialFacts : List AnchoredFact) : L0StateInvariant { facts := initialFacts, entries := [], headTick := 0, headMerkle := 0 }`
- **Alcance documentado:** El estado inicial con entries = [] satisface vacuamente L0StateInvariant por ausencia de elementos en la lista.

**#062 · [`Babylon60.L0Ledger.append_preserves_l0_invariant`](../../proof/lean/BabylonL0Ledger.lean#L100)** · Clase `U-IND` · Axiomas: `propext`

- **Firma:** `theorem append_preserves_l0_invariant (db : L0Database) (newEntry : LedgerEntry) (h_inv : L0StateInvariant db) (h_trig : TriggerAllowsInsert db newEntry) : L0StateInvariant (appendEntry db newEntry)`
- **Alcance documentado:** Preservación de L0StateInvariant al prepender una entrada que cumple TriggerAllowsInsert sobre una lista que ya cumplía el invariante.

**#063 · [`Babylon60.L0Ledger.append_strictly_increases_tick`](../../proof/lean/BabylonL0Ledger.lean#L117)** · Clase `U-ALG` · Axiomas: `propext, Classical.choice, Quot.sound`

- **Firma:** `theorem append_strictly_increases_tick (db : L0Database) (newEntry : LedgerEntry) (h_trig : TriggerAllowsInsert db newEntry) : db.headTick < (appendEntry db newEntry).headTick`
- **Alcance documentado:** Incremento estricto de headTick (db.headTick < (appendEntry db newEntry).headTick) bajo la precondición newEntry.logicalTick = db.headTick + 1 de TriggerAllowsInsert.

**#064 · [`Babylon60.L0Ledger.merkle_root_uniqueness`](../../proof/lean/BabylonL0Ledger.lean#L132)** · Clase `U-ALG` · Axiomas: `ninguno registrado` · **Alias editorial:** `append_entry_injective`

- **Firma:** `theorem merkle_root_uniqueness (db : L0Database) (e1 e2 : LedgerEntry) (h1 : TriggerAllowsInsert db e1) (h2 : TriggerAllowsInsert db e2) (h_eq : (appendEntry db e1).entries = (appendEntry db e2).entries) : e1.logicalTick = e2.logicalTick ∧ e1.prevMerkleRoot = e2.prevMerkleRoot ∧ e1 = e2`
- **Alcance documentado:** Inyectividad de inserción y alineación de paso bajo TriggerAllowsInsert: deduce e1.logicalTick = e2.logicalTick, e1.prevMerkleRoot = e2.prevMerkleRoot y e1 = e2 cuando (appendEntry db e1).entries = (appendEntry db e2).entries; no modela funciones hash criptográficas ni resistencia a colisiones.

**#065 · [`Babylon60.L0Ledger.l0_trigger_inhabited`](../../proof/lean/BabylonL0Ledger.lean#L173)** · Clase `W-EX` · Axiomas: `ninguno registrado`

- **Firma:** `theorem l0_trigger_inhabited : ∃ (db : L0Database) (e : LedgerEntry), TriggerAllowsInsert db e`
- **Alcance documentado:** Testigo constructivo de habitabilidad (AP-10) para TriggerAllowsInsert sobre witnessDbL0 y witnessEntryL0.

### [BabylonStressCorrupt.lean](../../proof/lean/BabylonStressCorrupt.lean)

**#066 · [`B60.Ledger.trace_is_paradox_free_auto`](../../proof/lean/BabylonStressCorrupt.lean#L1522)** · Clase `NEG-FIXTURE` · Axiomas: `N/A (negative fixture: expected decide rejection)`

- **Firma:** `theorem trace_is_paradox_free_auto : validateTrace auto_execution_trace = true`
- **Alcance documentado:** Fixture negativo de rechazo semántico esperado (AUDIT_LEAN_SCOPE_2026 §8): lista de 1.501 eventos con lectura impar final donde decide rechaza la igualdad = true.

### [BabylonStressTrace.lean](../../proof/lean/BabylonStressTrace.lean)

**#067 · [`B60.Ledger.trace_is_paradox_free_auto`](../../proof/lean/BabylonStressTrace.lean#L6019)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem trace_is_paradox_free_auto : validateTrace auto_execution_trace = true`
- **Alcance documentado:** Comprobación cerrada por decide sobre una traza literal válida de 6.000 eventos en BabylonStressTrace.lean.

### [BabylonTrace.lean](../../proof/lean/BabylonTrace.lean)

**#068 · [`B60.Ledger.trace_is_paradox_free`](../../proof/lean/BabylonTrace.lean#L91)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem trace_is_paradox_free : validateTrace trace_perfect = true`
- **Alcance documentado:** Comprobación cerrada por decide sobre la traza literal trace_perfect de 5 eventos en BabylonTrace.lean.

**#069 · [`B60.Ledger.step_read_even`](../../proof/lean/BabylonTrace.lean#L109)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem step_read_even (s : LockState) (ev : Event) (next : LockState) : step s ev = some next → (ev.action = Action.read → ev.seq % 2 = 0)`
- **Alcance documentado:** Lema de un paso: si step s ev = some next y ev.action = Action.read, la secuencia declarada en el evento es par (ev.seq % 2 = 0).

**#070 · [`B60.Ledger.runAeon_reads_even`](../../proof/lean/BabylonTrace.lean#L129)** · Clase `U-IND` · Axiomas: `propext`

- **Firma:** `theorem runAeon_reads_even (s : LockState) (trace : List Event) (finalState : LockState) : runAeon (some s) trace = some finalState → TraceReadsEven trace`
- **Alcance documentado:** Lema inductivo sobre listas de eventos: si runAeon (some s) trace = some finalState, todo evento de lectura en trace declara secuencia par (TraceReadsEven trace).

**#071 · [`B60.Ledger.no_torn_reads_universal`](../../proof/lean/BabylonTrace.lean#L156)** · Clase `U-IND` · Axiomas: `propext` · **Alias editorial:** `trace_reads_even_on_validation`

- **Firma:** `theorem no_torn_reads_universal (trace : List Event) : validateTrace trace = true → TraceReadsEven trace`
- **Alcance documentado:** Propiedad inductiva universal sobre el modelo de eventos: validateTrace trace = true → TraceReadsEven trace. Certifica paridad de las secuencias declaradas en eventos read; no modela el payload leído ni orden de memoria físico en Rust.

**#072 · [`B60.Ledger.no_heuristic_override_on_veto`](../../proof/lean/BabylonTrace.lean#L223)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem no_heuristic_override_on_veto (e : BabylonEvent) (h_veto : e.formalVeto = true) : ¬ ValidBabylonTransition e`
- **Alcance documentado:** Rechazo de transición en BabylonEvent cuando el campo booleano formalVeto = true.

**#073 · [`B60.Ledger.no_commit_without_witness`](../../proof/lean/BabylonTrace.lean#L231)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem no_commit_without_witness (e : BabylonEvent) (h_nw : e.formalWitnessOk = false) : ¬ ValidBabylonTransition e`
- **Alcance documentado:** Rechazo de transición en BabylonEvent cuando el campo booleano formalWitnessOk = false.

**#074 · [`B60.Ledger.expired_lease_rejected`](../../proof/lean/BabylonTrace.lean#L239)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem expired_lease_rejected (e : BabylonEvent) (h_exp : e.leaseEpoch < e.kernelEpoch) : ¬ ValidBabylonTransition e`
- **Alcance documentado:** Rechazo de transición en BabylonEvent cuando leaseEpoch < kernelEpoch.

**#075 · [`B60.Ledger.fl011_seqlock_integrity`](../../proof/lean/BabylonTrace.lean#L246)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl011_seqlock_integrity (e : BabylonEvent) (h_valid : ValidBabylonTransition e) : e.seqStart % 2 = 0 ∧ e.seqStart = e.seqEnd`
- **Alcance documentado:** Extrae las conjunciones e.seqStart % 2 = 0 y e.seqStart = e.seqEnd de ValidBabylonTransition e.

**#076 · [`B60.Ledger.torn_seq_rejected`](../../proof/lean/BabylonTrace.lean#L252)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem torn_seq_rejected (e : BabylonEvent) (h_torn : e.seqStart ≠ e.seqEnd) : ¬ ValidBabylonTransition e`
- **Alcance documentado:** Rechazo de transición en BabylonEvent cuando seqStart ≠ seqEnd (corolario directo de #075).

**#077 · [`B60.Ledger.trace_step_ok_valid`](../../proof/lean/BabylonTrace.lean#L262)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem trace_step_ok_valid : ValidBabylonTransition trace_step_ok`
- **Alcance documentado:** Comprobación cerrada por decide de ValidBabylonTransition sobre el registro concreto trace_step_ok.

**#078 · [`B60.Ledger.fl018_missing_critical_check_rejected`](../../proof/lean/BabylonTrace.lean#L307)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem fl018_missing_critical_check_rejected (s : CompositeGateState) (h_incomplete : (s.verifiedCriticalMask &&& s.requiredCriticalMask) ≠ s.requiredCriticalMask) : ¬ ValidCompositeAcceptance s`
- **Alcance documentado:** Rechazo en CompositeGateState (BitVec 64) cuando (verifiedCriticalMask &&& requiredCriticalMask) ≠ requiredCriticalMask.

**#079 · [`B60.Ledger.fl018_artifact_hash_mismatch_rejected`](../../proof/lean/BabylonTrace.lean#L313)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem fl018_artifact_hash_mismatch_rejected (s : CompositeGateState) (h_diff : s.acceptedArtifactHash ≠ s.verifiedArtifactHash) : ¬ ValidCompositeAcceptance s`
- **Alcance documentado:** Rechazo en CompositeGateState cuando acceptedArtifactHash ≠ verifiedArtifactHash.

**#080 · [`B60.Ledger.fl018_stale_epoch_rejected`](../../proof/lean/BabylonTrace.lean#L319)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem fl018_stale_epoch_rejected (s : CompositeGateState) (h_stale : ¬ (s.minPolicyEpoch ≤ s.evidenceEpoch)) : ¬ ValidCompositeAcceptance s`
- **Alcance documentado:** Rechazo en CompositeGateState cuando ¬(minPolicyEpoch ≤ evidenceEpoch).

**#081 · [`B60.Ledger.fl026_zero_threshold_rejected`](../../proof/lean/BabylonTrace.lean#L325)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem fl026_zero_threshold_rejected (s : CompositeGateState) (h_zero : s.quorumThreshold = 0#64) : ¬ ValidCompositeAcceptance s`
- **Alcance documentado:** Rechazo en CompositeGateState cuando quorumThreshold = 0#64.

**#082 · [`B60.Ledger.composite_gate_ok_valid`](../../proof/lean/BabylonTrace.lean#L344)** · Clase `I-DEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem composite_gate_ok_valid : ValidCompositeAcceptance composite_gate_ok`
- **Alcance documentado:** Comprobación cerrada por decide de ValidCompositeAcceptance sobre el estado concreto composite_gate_ok.

**#083 · [`B60.Ledger.fl018_composite_acceptance_inhabited`](../../proof/lean/BabylonTrace.lean#L347)** · Clase `W-EX` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem fl018_composite_acceptance_inhabited : ∃ s : CompositeGateState, ValidCompositeAcceptance s`
- **Alcance documentado:** Testigo de habitabilidad (AP-10) para ValidCompositeAcceptance usando composite_gate_ok.

**#084 · [`B60.Ledger.composite_gate_ple_91pct_rejected`](../../proof/lean/BabylonTrace.lean#L354)** · Clase `I-DEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem composite_gate_ple_91pct_rejected : ¬ ValidCompositeAcceptance composite_gate_ple_91pct_fail`
- **Alcance documentado:** Comprobación cerrada por decide que rechaza el estado concreto composite_gate_ple_91pct_fail (máscara 0x3FF vs 0x7FF).

### [C5Affine.lean](../../proof/lean/C5Affine.lean)

**#085 · [`no_double_free`](../../proof/lean/C5Affine.lean#L21)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem no_double_free (r : AffineResource) (h : r = AffineResource.consumed) : consume r = none`
- **Alcance documentado:** Evaluación de consume sobre el constructor AffineResource.consumed devolviendo none; tipo inductivo puro y duplicable en Lean, no sistema de tipos lineales ni verificador de heap/aliasing.

### [C5PortHamiltonian.lean](../../proof/lean/C5PortHamiltonian.lean)

**#086 · [`C5REAL.Proof.skew_symmetric_circulation_zero`](../../proof/lean/C5PortHamiltonian.lean#L31)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem skew_symmetric_circulation_zero (x y : Int) : x * (-y) + y * x = 0`
- **Alcance documentado:** Identidad algebraica en el anillo Int: x * (-y) + y * x = 0.

**#087 · [`C5REAL.Proof.lyapunov_monotonic_dissipation_verified`](../../proof/lean/C5PortHamiltonian.lean#L39)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem lyapunov_monotonic_dissipation_verified : let s0 : LatentFixed2D := { x := 1000, y := 1000 } let s1 := stepPHLD s0 20 doubleHamiltonian s1 ≤ doubleHamiltonian s0`
- **Alcance documentado:** Comprobación cerrada por decide de un único paso discreto stepPHLD desde s0 = (1000, 1000) con r_percent = 20; no demuestra monotonía global de Lyapunov (existe contraejemplo en (0, 1) documentado en AUDIT_LEAN_SCOPE_2026 §5).

**#088 · [`C5REAL.Proof.kudurru_64_alignment_verified`](../../proof/lean/C5PortHamiltonian.lean#L49)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem kudurru_64_alignment_verified : isAligned64 0 = true ∧ isAligned64 64 = true ∧ isAligned64 128 = true`
- **Alcance documentado:** Comprobación cerrada por decide de que 0, 64 y 128 tienen resto 0 módulo 64; no verifica alineamiento físico del asignador en Rust.

### [CanonicalEnvelope.lean](../../proof/lean/CanonicalEnvelope.lean)

**#089 · [`B60.CBOR.decode_encode`](../../proof/lean/CanonicalEnvelope.lean#L56)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem decode_encode (c : Codec α) (x : α) (h : c.valid x) : decode c (c.encode x) = some x`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `CanonicalEnvelope.lean` (`decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#090 · [`B60.CBOR.encode_decode`](../../proof/lean/CanonicalEnvelope.lean#L62)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem encode_decode (c : Codec α) (input : Bytes) (x : α) (h : decode c input = some x) : c.encode x = input`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `CanonicalEnvelope.lean` (`encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#091 · [`B60.CBOR.encode_injective`](../../proof/lean/CanonicalEnvelope.lean#L72)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem encode_injective (c : Codec α) (x y : α) (hx : c.valid x) (hy : c.valid y) (he : c.encode x = c.encode y) : x = y`
- **Alcance documentado:** Inyectividad universal del codificador sobre el subconjunto de entradas que satisfacen el predicado `.valid` en `CanonicalEnvelope.lean` (`encode_injective`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#092 · [`B60.CBOR.decodeChecked_encode`](../../proof/lean/CanonicalEnvelope.lean#L83)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem decodeChecked_encode (c : Codec α) [DecidablePred c.valid] (x : α) (h : c.valid x) : decodeChecked c (c.encode x) = some x`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalEnvelope.lean` (`decodeChecked_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#093 · [`B60.CBOR.decodeChecked_valid`](../../proof/lean/CanonicalEnvelope.lean#L87)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem decodeChecked_valid (c : Codec α) [DecidablePred c.valid] (input : Bytes) (x : α) (h : decodeChecked c input = some x) : c.valid x`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `CanonicalEnvelope.lean` (`decodeChecked_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#094 · [`B60.CBOR.encode_decodeChecked`](../../proof/lean/CanonicalEnvelope.lean#L99)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem encode_decodeChecked (c : Codec α) [DecidablePred c.valid] (input : Bytes) (x : α) (h : decodeChecked c input = some x) : c.encode x = input`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `CanonicalEnvelope.lean` (`encode_decodeChecked`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#095 · [`B60.CBOR.parseMany_encodeMany`](../../proof/lean/CanonicalEnvelope.lean#L185)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem parseMany_encodeMany (c : Codec α) (xs : List α) (h : ∀ x ∈ xs, c.valid x) (suffix : Bytes) : parseMany c xs.length (encodeMany c xs ++ suffix) = some (xs, suffix)`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalEnvelope.lean` (`parseMany_encodeMany`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

### [CanonicalHead.lean](../../proof/lean/CanonicalHead.lean)

**#096 · [`B60.CBOR.decodeBE_encodeBE_suffix`](../../proof/lean/CanonicalHead.lean#L24)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem decodeBE_encodeBE_suffix (k n : Nat) (suffix : List UInt8) (hn : n < 256^k) : decodeBE k (encodeBE k n ++ suffix) = some (n, suffix)`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalHead.lean` (`decodeBE_encodeBE_suffix`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#097 · [`B60.CBOR.decodePayload_encodeBE`](../../proof/lean/CanonicalHead.lean#L60)** · Clase `U-CODEC` · Axiomas: `propext`

- **Firma:** `theorem decodePayload_encodeBE (major width minimum n : Nat) (suffix : List UInt8) (hn : n < 256^width) (hmin : ¬ n < minimum) : decodePayload major width minimum (encodeBE width n ++ suffix) = some (major, n, suffix)`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalHead.lean` (`decodePayload_encodeBE`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#098 · [`B60.CBOR.headByte_parts`](../../proof/lean/CanonicalHead.lean#L79)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem headByte_parts (major info : Nat) (hm : major < 8) (hi : info < 32) : (headByte major info).toNat / 32 = major ∧ (headByte major info).toNat % 32 = info`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalHead.lean` (`headByte_parts`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#099 · [`B60.CBOR.decodeHead_encodeHead_suffix`](../../proof/lean/CanonicalHead.lean#L89)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem decodeHead_encodeHead_suffix (major n : Nat) (suffix : List UInt8) (hm : major < 8) (hn : n < 2^64) : decodeHead (encodeHead major n ++ suffix) = some (major, n, suffix)`
- **Alcance documentado:** Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos en `CanonicalHead.lean` (`decodeHead_encodeHead_suffix`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

### [Destiladora_838c463da193b48f.lean](../../proof/lean/Destiladora_838c463da193b48f.lean)

**#100 · [`B60.Destiladora.C_838c463da193b48f.thm_seqlock_mutation_odd`](../../proof/lean/Destiladora_838c463da193b48f.lean#L22)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem thm_seqlock_mutation_odd (k : Nat) : (seqlock_write_begin (2 * k)) % 2 = 1`
- **Alcance documentado:** Paridad impar ((2 * k + 1) % 2 = 1) de la función aritmética seqlock_write_begin sobre Nat.

**#101 · [`B60.Destiladora.C_838c463da193b48f.thm_seqlock_commit_even`](../../proof/lean/Destiladora_838c463da193b48f.lean#L27)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem thm_seqlock_commit_even (k : Nat) : (seqlock_write_commit (2 * k)) % 2 = 0`
- **Alcance documentado:** Paridad par ((2 * k + 2) % 2 = 0) de la función aritmética seqlock_write_commit sobre Nat.

**#102 · [`B60.Destiladora.C_838c463da193b48f.thm_reject_poisoned`](../../proof/lean/Destiladora_838c463da193b48f.lean#L63)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem thm_reject_poisoned (seq : Nat) (w : Option Nat) (ctx : FastPathContext) : evalFastPath { poisoned := true, seq := seq, writer := w } ctx = FastPathVerdict.Miss`
- **Alcance documentado:** Si el campo booleano poisoned = true en SystemState, evalFastPath devuelve FastPathVerdict.Miss.

**#103 · [`B60.Destiladora.C_838c463da193b48f.thm_hit_exact_signature`](../../proof/lean/Destiladora_838c463da193b48f.lean#L67)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem thm_hit_exact_signature : evalFastPath { poisoned := false, seq := 0, writer := none } { astPrefix := expectedAstPrefix, filesCount := expectedFilesCount } = FastPathVerdict.Hit`
- **Alcance documentado:** Comprobación cerrada de evalFastPath devolviendo Hit cuando astPrefix y filesCount coinciden con las constantes esperadas en estado no envenenado.

**#104 · [`B60.Destiladora.C_838c463da193b48f.thm_miss_bitflip_signature`](../../proof/lean/Destiladora_838c463da193b48f.lean#L72)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem thm_miss_bitflip_signature : evalFastPath { poisoned := false, seq := 0, writer := none } { astPrefix := expectedAstPrefix + 1, filesCount := expectedFilesCount } = FastPathVerdict.Miss`
- **Alcance documentado:** Comprobación cerrada de evalFastPath devolviendo Miss cuando astPrefix difiere en +1 de la constante esperada.

**#105 · [`B60.Destiladora.C_838c463da193b48f.thm_invariant_838c463da193b48f_step`](../../proof/lean/Destiladora_838c463da193b48f.lean#L93)** · Clase `U-ALG` · Axiomas: `propext`

- **Firma:** `theorem thm_invariant_838c463da193b48f_step (s : SystemState) (a : Action) (h_inv : invariant s) : invariant (transition s a)`
- **Alcance documentado:** Preservación en un paso del predicado invariant (s.poisoned = true ∨ s.seq % 2 = 0) por la función transition.

**#106 · [`B60.Destiladora.C_838c463da193b48f.thm_invariant_838c463da193b48f`](../../proof/lean/Destiladora_838c463da193b48f.lean#L111)** · Clase `U-IND` · Axiomas: `propext`

- **Firma:** `theorem thm_invariant_838c463da193b48f (s : SystemState) (trace : List Action) (h_inv : invariant s) : invariant (runTrace s trace)`
- **Alcance documentado:** Preservación inductiva del predicado invariant a lo largo de cualquier lista finita de acciones en runTrace.

### [ExampleSeqlockTrace.lean](../../proof/lean/ExampleSeqlockTrace.lean)

**#107 · [`B60.ExampleSeqlockTrace.inv_inhabited`](../../proof/lean/ExampleSeqlockTrace.lean#L46)** · Clase `W-EX` · Axiomas: `propext`

- **Firma:** `theorem inv_inhabited : ∃ trace, trace ≠ [] ∧ isValidTrace trace 0 = true`
- **Alcance documentado:** Testigo constructivo de existencia de una traza no vacía validCycle aceptada por isValidTrace en aritmética BitVec 64/32.

### [LarsaEquivocationSafety.lean](../../proof/lean/LarsaEquivocationSafety.lean)

**#108 · [`LarsaEquivocationSafety.canonical_quorum_intersection`](../../proof/lean/LarsaEquivocationSafety.lean#L25)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem canonical_quorum_intersection (f : Nat) : let q := quorum_threshold f let n := total_nodes f q + q - n = f + 1`
- **Alcance documentado:** Identidad aritmética en Nat: (2*f + 1) + (2*f + 1) - (3*f + 1) = f + 1; ingrediente aritmético de intersección de quórum, no prueba por sí sola cardinalidad de conjuntos finitos de votantes ni protocolo BFT completo.

**#109 · [`LarsaEquivocationSafety.unilateral_expulsion_weakens_intersection`](../../proof/lean/LarsaEquivocationSafety.lean#L39)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem unilateral_expulsion_weakens_intersection (f : Nat) (h_f : f ≥ 1) : let q_prime := 2 * f let n_prime := 3 * f q_prime + q_prime - n_prime = f`
- **Alcance documentado:** Identidad aritmética en Nat para f ≥ 1: 2*f + 2*f - 3*f = f.

**#110 · [`LarsaEquivocationSafety.instance_inhabited`](../../proof/lean/LarsaEquivocationSafety.lean#L67)** · Clase `W-EX` · Axiomas: `ninguno registrado`

- **Firma:** `theorem instance_inhabited : ∃ inst : ConsensusInstance, inst.n = 4 ∧ inst.q = 3`
- **Alcance documentado:** Testigo de existencia de ConsensusInstance con n = 4 y q = 3 (para f = 1).

**#111 · [`LarsaEquivocationSafety.total_nodes_no_u64_overflow`](../../proof/lean/LarsaEquivocationSafety.lean#L78)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem total_nodes_no_u64_overflow (f : Nat) (h_bound : f < 2 ^ 62) : 3 * f + 1 < 2 ^ 64`
- **Alcance documentado:** Cota aritmética universal sin overflow en 64 bits: para todo f < 2^62, 3 * f + 1 < 2^64.

**#112 · [`LarsaEquivocationSafety.quorum_threshold_no_u64_overflow`](../../proof/lean/LarsaEquivocationSafety.lean#L86)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem quorum_threshold_no_u64_overflow (f : Nat) (h_bound : f < 2 ^ 62) : 2 * f + 1 < 2 ^ 64`
- **Alcance documentado:** Cota aritmética universal sin overflow en 64 bits: para todo f < 2^62, 2 * f + 1 < 2^64.

**#113 · [`LarsaEquivocationSafety.bounded_arithmetic_f1`](../../proof/lean/LarsaEquivocationSafety.lean#L94)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem bounded_arithmetic_f1 : total_nodes 1 < 2 ^ 64 ∧ quorum_threshold 1 < 2 ^ 64`
- **Alcance documentado:** Comprobación cerrada por decide de las cotas < 2^64 para f = 1.

**#114 · [`LarsaEquivocationSafety.verifiedQuorumInvariant`](../../proof/lean/LarsaEquivocationSafety.lean#L110)** · Clase `W-EX` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem verifiedQuorumInvariant : VerifiedQuorumInvariant`
- **Alcance documentado:** Empaqueta la identidad aritmética #108 y el testigo #110 en la estructura VerifiedQuorumInvariant.

### [MolochLandauer.lean](../../proof/lean/MolochLandauer.lean)

**#115 · [`Babylon.MolochLandauer.moloch_payoff_is_zero`](../../proof/lean/MolochLandauer.lean#L59)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem moloch_payoff_is_zero (a : AgentAction) (h_moloch : is_moloch_extraction a = true) : net_exergy_payoff a = 0`
- **Alcance documentado:** En la función de puntuación truncada en Nat (net_exergy_payoff), si is_moloch_extraction a = true entonces la resta truncada produce 0.

**#116 · [`Babylon.MolochLandauer.constructive_action_positive_payoff`](../../proof/lean/MolochLandauer.lean#L68)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem constructive_action_positive_payoff (a : AgentAction) (h_class : a.action_class = .Constructive) (h_ext : a.externalized_entropy = 0) (h_ben : a.claimed_benefit > a.internal_dissipation) : net_exergy_payoff a > 0`
- **Alcance documentado:** Para una acción con action_class = .Constructive, externalized_entropy = 0 y claimed_benefit > internal_dissipation, la fórmula net_exergy_payoff devuelve un valor > 0.

**#117 · [`Babylon.MolochLandauer.cooperation_dominates_moloch`](../../proof/lean/MolochLandauer.lean#L82)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem cooperation_dominates_moloch (a_coop a_ext : AgentAction) (h_coop_class : a_coop.action_class = .Constructive) (h_coop_ext : a_coop.externalized_entropy = 0) (h_coop_ben : a_coop.claimed_benefit > a_coop.internal_dissipation) (h_moloch : is_moloch_extraction a_ext = true) : net_exergy_payoff a_coop > net_exergy_payoff a_ext`
- **Alcance documentado:** Combina #115 y #116 para dos registros AgentAction que satisfacen esas hipótesis; compara la función de puntuación sobre ambos registros, sin demostrar equilibrio de Nash ni dominancia estratégica en un juego multi-agente.

**#118 · [`Babylon.MolochLandauer.landauer_compensates_entropy`](../../proof/lean/MolochLandauer.lean#L95)** · Clase `U-ALG` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem landauer_compensates_entropy (a : AgentAction) : landauer_penalty a ≥ a.externalized_entropy`
- **Alcance documentado:** Por definición de landauer_penalty en Nat, su valor es ≥ a.externalized_entropy.

**#119 · [`Babylon.MolochLandauer.trace_entropy_solvency_universal`](../../proof/lean/MolochLandauer.lean#L115)** · Clase `U-IND` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem trace_entropy_solvency_universal (trace : List AgentAction) : total_landauer_penalties trace ≥ total_externalized_entropy trace`
- **Alcance documentado:** Inducción sobre listas finitas de AgentAction: la suma de landauer_penalty es ≥ la suma de externalized_entropy.

### [NavierStokesBKM.lean](../../proof/lean/NavierStokesBKM.lean)

**#120 · [`B60.NavierStokes.constantin_fefferman_depletion_holds`](../../proof/lean/NavierStokesBKM.lean#L95)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem constantin_fefferman_depletion_holds : auditTrace trace_depleted = AuditResult.SmoothDepleted`
- **Alcance documentado:** Comprobación cerrada por decide de auditTrace sobre la lista concreta trace_depleted de 3 pasos.

**#121 · [`B60.NavierStokes.genuine_blowup_candidate_isolated`](../../proof/lean/NavierStokesBKM.lean#L108)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem genuine_blowup_candidate_isolated : auditTrace trace_singular_candidate = AuditResult.FiniteTimeBlowupCandidate`
- **Alcance documentado:** Comprobación cerrada por decide de auditTrace sobre la lista concreta trace_singular_candidate de 3 pasos.

**#122 · [`B60.NavierStokes.discrete_curl_grad_nilpotent`](../../proof/lean/NavierStokesBKM.lean#L126)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem discrete_curl_grad_nilpotent (c : DiscreteChainComplex) (phi : Nat) : c.d1_eval (c.d0_eval phi) = 0`
- **Alcance documentado:** Extrae la hipótesis de campo h_curl_grad : d1_eval (d0_eval phi) = 0 suministrada dentro del registro DiscreteChainComplex.

**#123 · [`B60.NavierStokes.discrete_div_curl_nilpotent`](../../proof/lean/NavierStokesBKM.lean#L131)** · Clase `U-ALG` · Axiomas: `ninguno registrado`

- **Firma:** `theorem discrete_div_curl_nilpotent (c : DiscreteChainComplex) (u : Nat) : c.d2_eval (c.d1_eval u) = 0`
- **Alcance documentado:** Extrae la hipótesis de campo h_div_curl : d2_eval (d1_eval u) = 0 suministrada dentro del registro DiscreteChainComplex.

**#124 · [`B60.NavierStokes.coexact_field_is_solenoidal`](../../proof/lean/NavierStokesBKM.lean#L146)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem coexact_field_is_solenoidal : isStrictlySolenoidal 0 = true`
- **Alcance documentado:** Comprobación cerrada por decide de isStrictlySolenoidal 0 = true (comprueba 0 == 0).

### [NavierStokesSobolevKato.lean](../../proof/lean/NavierStokesSobolevKato.lean)

**#125 · [`B60.NavierStokes.SobolevKato.sobolev_embedding_h2_in_c0`](../../proof/lean/NavierStokesSobolevKato.lean#L27)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem sobolev_embedding_h2_in_c0 : isSobolevContinuousEmbedding 120 0 = true`
- **Alcance documentado:** Comprobación aritmética cerrada por decide: 120 > 0 * 60 + 90 en isSobolevContinuousEmbedding; no construye espacios funcionales H^2 ni C^0.

**#126 · [`B60.NavierStokes.SobolevKato.sobolev_embedding_h3_in_c1`](../../proof/lean/NavierStokesSobolevKato.lean#L32)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem sobolev_embedding_h3_in_c1 : isSobolevContinuousEmbedding 180 1 = true`
- **Alcance documentado:** Comprobación aritmética cerrada por decide: 180 > 1 * 60 + 90 en isSobolevContinuousEmbedding; no construye espacios funcionales H^3 ni C^1.

**#127 · [`B60.NavierStokes.SobolevKato.kato_local_existence_h3`](../../proof/lean/NavierStokesSobolevKato.lean#L44)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem kato_local_existence_h3 : isKatoLocalWellPosed 180 = true`
- **Alcance documentado:** Comprobación aritmética cerrada por decide: 180 > 150 en isKatoLocalWellPosed; no demuestra existencia local de soluciones PDE.

**#128 · [`B60.NavierStokes.SobolevKato.curry_howard_taylor_green_step`](../../proof/lean/NavierStokesSobolevKato.lean#L55)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem curry_howard_taylor_green_step : verifyDissipationCurryHoward 1000 980 10 1 1 = true`
- **Alcance documentado:** Comprobación aritmética cerrada por decide: 980 + 2 * 1 * 10 * 1 ≤ 1000 en verifyDissipationCurryHoward.

**#129 · [`B60.NavierStokes.SobolevKato.interval_containment_reflection`](../../proof/lean/NavierStokesSobolevKato.lean#L71)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem interval_containment_reflection : intervalContains { lower := 10, upper := 100 } { lower := 20, upper := 80 } = true`
- **Alcance documentado:** Comprobación cerrada por decide de inclusión entre dos intervalos concretos [20, 80] ⊆ [10, 100].

**#130 · [`B60.NavierStokes.SobolevKato.gronwall_bkm_regularity_certified`](../../proof/lean/NavierStokesSobolevKato.lean#L86)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem gronwall_bkm_regularity_certified : isGronwallBounded 150 (gronwallBound 100 [1, 0, 0]) = true`
- **Alcance documentado:** Comprobación cerrada por decide: 150 ≤ 200 evaluando gronwallBound 100 [1, 0, 0].

**#131 · [`B60.NavierStokes.SobolevKato.causal_monotonicity_trace_proof`](../../proof/lean/NavierStokesSobolevKato.lean#L110)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem causal_monotonicity_trace_proof : verifyCausalTrace [1, 2, 3, 4, 5, 10, 20, 50, 60] = true`
- **Alcance documentado:** Comprobación cerrada por decide de que la lista concreta [1, 2, 3, 4, 5, 10, 20, 50, 60] es estrictamente creciente en verifyCausalTrace.

**#132 · [`B60.NavierStokes.SobolevKato.millennium_navier_stokes_regular_by_decide`](../../proof/lean/NavierStokesSobolevKato.lean#L141)** · Clase `I-DEC` · Axiomas: `ninguno registrado` · **Alias editorial:** `bkm_monitor_flags_accepted_by_decide`

- **Firma:** `theorem millennium_navier_stokes_regular_by_decide : isMillenniumRegular { bkmIntegralBounded := true, constantinFeffermanSmooth := true, sobolevH3Controlled := true } = true`
- **Alcance documentado:** Aceptación de tres indicadores booleanos fijados en true (isMillenniumRegular { bkmIntegralBounded := true, constantinFeffermanSmooth := true, sobolevH3Controlled := true } = true); no define campos de velocidad/presión ni demuestra regularidad analítica de las ecuaciones de Navier-Stokes.

### [NemesisWave4.lean](../../proof/lean/NemesisWave4.lean)

**#133 · [`NemesisWave4.ecp_v2_valid_trace_certified`](../../proof/lean/NemesisWave4.lean#L164)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem ecp_v2_valid_trace_certified : validateEcpTrace initialMonitor validWave4Trace = true`
- **Alcance documentado:** Comprobación cerrada por decide de validateEcpTrace sobre la traza concreta validWave4Trace de 3 eventos.

**#134 · [`NemesisWave4.fl014_fencing_race_rejected`](../../proof/lean/NemesisWave4.lean#L168)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl014_fencing_race_rejected : validateEcpTrace initialMonitor corruptFencingRaceTrace = false`
- **Alcance documentado:** Comprobación cerrada por decide que rechaza la traza concreta corruptFencingRaceTrace en validateEcpTrace.

**#135 · [`NemesisWave4.fl014_blind_retry_rejected`](../../proof/lean/NemesisWave4.lean#L172)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl014_blind_retry_rejected : validateEcpTrace initialMonitor corruptBlindRetryTrace = false`
- **Alcance documentado:** Comprobación cerrada por decide que rechaza la traza concreta corruptBlindRetryTrace en validateEcpTrace.

**#136 · [`NemesisWave4.fl014_budget_composition_rejected`](../../proof/lean/NemesisWave4.lean#L176)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl014_budget_composition_rejected : validateEcpTrace initialMonitor corruptBudgetCompositionTrace = false`
- **Alcance documentado:** Comprobación cerrada por decide que rechaza la traza concreta corruptBudgetCompositionTrace en validateEcpTrace.

**#137 · [`NemesisWave4.fl013_darwin_uf_immutable_degraded`](../../proof/lean/NemesisWave4.lean#L180)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl013_darwin_uf_immutable_degraded : evaluateSealStrength false true false true = some IsolationStrength.degradedSameUidOrInProcess`
- **Alcance documentado:** Comprobación cerrada por decide de evaluateSealStrength false true false true = some .degradedSameUidOrInProcess.

**#138 · [`NemesisWave4.fl015_transitive_drift_rejected`](../../proof/lean/NemesisWave4.lean#L184)** · Clase `I-DEC` · Axiomas: `ninguno registrado`

- **Firma:** `theorem fl015_transitive_drift_rejected : validateDeploymentPermit 0xAAA1 0xBBB2 5 5 100 500 = false`
- **Alcance documentado:** Comprobación cerrada por decide de validateDeploymentPermit 0xAAA1 0xBBB2 5 5 100 500 = false.

### [TicketEnvelope.lean](../../proof/lean/TicketEnvelope.lean)

**#139 · [`B60.Ticket.decode_encode`](../../proof/lean/TicketEnvelope.lean#L81)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem decode_encode (t : Ticket) : decode (encode t) = some t`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `TicketEnvelope.lean` (`decode_encode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#140 · [`B60.Ticket.encode_decode`](../../proof/lean/TicketEnvelope.lean#L84)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem encode_decode (input : Bytes) (t : Ticket) (h : decode input = some t) : encode t = input`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `TicketEnvelope.lean` (`encode_decode`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#141 · [`B60.Ticket.encode_injective`](../../proof/lean/TicketEnvelope.lean#L98)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem encode_injective (a b : Ticket) (h : encode a = encode b) : a = b`
- **Alcance documentado:** Inyectividad universal del codificador sobre el subconjunto de entradas que satisfacen el predicado `.valid` en `TicketEnvelope.lean` (`encode_injective`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#142 · [`B60.Ticket.decoded_valid`](../../proof/lean/TicketEnvelope.lean#L103)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem decoded_valid (input : Bytes) (t : Ticket) (_ : decode input = some t) : payloadCodec.valid t.val ∧ shape t.val = true`
- **Alcance documentado:** Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec en `TicketEnvelope.lean` (`decoded_valid`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#143 · [`B60.Ticket.decode_encode_external`](../../proof/lean/TicketEnvelope.lean#L113)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem decode_encode_external (s : SignedTicket) : decodeExternal (encodeExternal s) = some s`
- **Alcance documentado:** Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x` en `TicketEnvelope.lean` (`decode_encode_external`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

**#144 · [`B60.Ticket.encode_decode_external`](../../proof/lean/TicketEnvelope.lean#L117)** · Clase `U-CODEC` · Axiomas: `propext, Quot.sound`

- **Firma:** `theorem encode_decode_external (fields : Bytes × Bytes) (s : SignedTicket) (h : decodeExternal fields = some s) : encodeExternal s = fields`
- **Alcance documentado:** Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo en `TicketEnvelope.lean` (`encode_decode_external`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.

## 4. Inventario 1:1 de construcciones no-teorema

El registro incluye todas las 275 declaraciones `def`, `inductive`, `structure` y `abbrev` del inventario de origen, para hacer reconciliables las cifras de 228, 372 y 419.

| ID | Referencia | Clase | Nombre cualificado |
|:--|:--|:--|:--|
| `#C001` | [`AX0.lean:11`](../../proof/lean/AX0.lean#L11) | `inductive` | `AuthState` |
| `#C002` | [`AX0.lean:20`](../../proof/lean/AX0.lean#L20) | `inductive` | `AuthEvent` |
| `#C003` | [`AX0.lean:28`](../../proof/lean/AX0.lean#L28) | `def` | `step` |
| `#C004` | [`AX0.lean:51`](../../proof/lean/AX0.lean#L51) | `def` | `validateTrace` |
| `#C005` | [`AX0.lean:63`](../../proof/lean/AX0.lean#L63) | `def` | `trace_happy` |
| `#C006` | [`AX0.lean:68`](../../proof/lean/AX0.lean#L68) | `def` | `trace_double_dispatch` |
| `#C007` | [`AX0.lean:73`](../../proof/lean/AX0.lean#L73) | `def` | `trace_illegal_dispatch` |
| `#C008` | [`AX0.lean:78`](../../proof/lean/AX0.lean#L78) | `def` | `trace_crash` |
| `#C009` | [`AX0.lean:86`](../../proof/lean/AX0.lean#L86) | `def` | `countDispatches` |
| `#C010` | [`AX0.lean:91`](../../proof/lean/AX0.lean#L91) | `def` | `maxAllowedDispatches` |
| — | [`AX0.lean:151`](../../proof/lean/AX0.lean#L151) | `abbrev` | `Auth001SafetyProp` |
| — | [`AX0.lean:185`](../../proof/lean/AX0.lean#L185) | `structure` | `VerifiedAuthInvariant` |
| `#C011` | [`AcsEnvelope.lean:21`](../../proof/lean/AcsEnvelope.lean#L21) | `def` | `B60.ACS.restrict` |
| `#C012` | [`AcsEnvelope.lean:31`](../../proof/lean/AcsEnvelope.lean#L31) | `def` | `B60.ACS.utf8` |
| `#C013` | [`AcsEnvelope.lean:33`](../../proof/lean/AcsEnvelope.lean#L33) | `def` | `B60.ACS.text` |
| `#C014` | [`AcsEnvelope.lean:34`](../../proof/lean/AcsEnvelope.lean#L34) | `def` | `B60.ACS.digest` |
| `#C015` | [`AcsEnvelope.lean:35`](../../proof/lean/AcsEnvelope.lean#L35) | `def` | `B60.ACS.u32` |
| `#C016` | [`AcsEnvelope.lean:36`](../../proof/lean/AcsEnvelope.lean#L36) | `def` | `B60.ACS.principal` |
| `#C017` | [`AcsEnvelope.lean:37`](../../proof/lean/AcsEnvelope.lean#L37) | `def` | `B60.ACS.effect` |
| `#C018` | [`AcsEnvelope.lean:38`](../../proof/lean/AcsEnvelope.lean#L38) | `def` | `B60.ACS.enforcement` |
| — | [`AcsEnvelope.lean:41`](../../proof/lean/AcsEnvelope.lean#L41) | `abbrev` | `B60.ACS.Context` |
| `#C019` | [`AcsEnvelope.lean:44`](../../proof/lean/AcsEnvelope.lean#L44) | `def` | `B60.ACS.contextCodec` |
| — | [`AcsEnvelope.lean:49`](../../proof/lean/AcsEnvelope.lean#L49) | `abbrev` | `B60.ACS.Key` |
| `#C020` | [`AcsEnvelope.lean:50`](../../proof/lean/AcsEnvelope.lean#L50) | `def` | `B60.ACS.keyCodec` |
| — | [`AcsEnvelope.lean:53`](../../proof/lean/AcsEnvelope.lean#L53) | `abbrev` | `B60.ACS.Grant` |
| `#C021` | [`AcsEnvelope.lean:54`](../../proof/lean/AcsEnvelope.lean#L54) | `def` | `B60.ACS.grantCodec` |
| — | [`AcsEnvelope.lean:59`](../../proof/lean/AcsEnvelope.lean#L59) | `abbrev` | `B60.ACS.Call` |
| `#C022` | [`AcsEnvelope.lean:62`](../../proof/lean/AcsEnvelope.lean#L62) | `def` | `B60.ACS.callCodec` |
| `#C023` | [`AcsEnvelope.lean:67`](../../proof/lean/AcsEnvelope.lean#L67) | `inductive` | `B60.ACS.Outcome` |
| `#C024` | [`AcsEnvelope.lean:73`](../../proof/lean/AcsEnvelope.lean#L73) | `def` | `B60.ACS.rejectedCodec` |
| `#C025` | [`AcsEnvelope.lean:74`](../../proof/lean/AcsEnvelope.lean#L74) | `def` | `B60.ACS.unknownCodec` |
| `#C026` | [`AcsEnvelope.lean:75`](../../proof/lean/AcsEnvelope.lean#L75) | `def` | `B60.ACS.verifiedCodec` |
| `#C027` | [`AcsEnvelope.lean:77`](../../proof/lean/AcsEnvelope.lean#L77) | `def` | `B60.ACS.outcomeCodec` |
| — | [`AcsEnvelope.lean:104`](../../proof/lean/AcsEnvelope.lean#L104) | `abbrev` | `B60.ACS.Forensic` |
| `#C028` | [`AcsEnvelope.lean:107`](../../proof/lean/AcsEnvelope.lean#L107) | `def` | `B60.ACS.forensicCodec` |
| `#C029` | [`AcsEnvelope.lean:111`](../../proof/lean/AcsEnvelope.lean#L111) | `inductive` | `B60.ACS.Algorithm` |
| `#C030` | [`AcsEnvelope.lean:114`](../../proof/lean/AcsEnvelope.lean#L114) | `def` | `B60.ACS.protectedHeader` |
| `#C031` | [`AcsEnvelope.lean:119`](../../proof/lean/AcsEnvelope.lean#L119) | `def` | `B60.ACS.signatureStructure` |
| `#C032` | [`AcsEnvelope.lean:124`](../../proof/lean/AcsEnvelope.lean#L124) | `def` | `B60.ACS.coseSign1` |
| `#C033` | [`AcsEnvelope.lean:139`](../../proof/lean/AcsEnvelope.lean#L139) | `def` | `B60.ACS.wrapped` |
| `#C034` | [`AcsEnvelope.lean:151`](../../proof/lean/AcsEnvelope.lean#L151) | `def` | `B60.ACS.typedCose` |
| `#C035` | [`AcsEnvelope.lean:160`](../../proof/lean/AcsEnvelope.lean#L160) | `def` | `B60.ACS.typedSignatureStructure` |
| `#C036` | [`AcsEnvelope.lean:196`](../../proof/lean/AcsEnvelope.lean#L196) | `def` | `B60.ACS.decodeCall` |
| `#C037` | [`AcsEnvelope.lean:197`](../../proof/lean/AcsEnvelope.lean#L197) | `def` | `B60.ACS.decodeGrant` |
| `#C038` | [`AcsEnvelope.lean:198`](../../proof/lean/AcsEnvelope.lean#L198) | `def` | `B60.ACS.decodeForensic` |
| `#C039` | [`AcsEnvelope.lean:281`](../../proof/lean/AcsEnvelope.lean#L281) | `def` | `B60.ACS.nibble` |
| `#C040` | [`AcsEnvelope.lean:282`](../../proof/lean/AcsEnvelope.lean#L282) | `def` | `B60.ACS.unhex` |
| `#C041` | [`AcsEnvelope.lean:285`](../../proof/lean/AcsEnvelope.lean#L285) | `def` | `B60.ACS.hex` |
| `#C042` | [`AcsEnvelope.lean:287`](../../proof/lean/AcsEnvelope.lean#L287) | `def` | `B60.ACS.fill32` |
| `#C043` | [`AcsEnvelope.lean:290`](../../proof/lean/AcsEnvelope.lean#L290) | `def` | `B60.ACS.golden_root` |
| `#C044` | [`AcsEnvelope.lean:291`](../../proof/lean/AcsEnvelope.lean#L291) | `def` | `B60.ACS.golden_delegated` |
| `#C045` | [`AcsEnvelope.lean:292`](../../proof/lean/AcsEnvelope.lean#L292) | `def` | `B60.ACS.golden_grant` |
| `#C046` | [`AcsEnvelope.lean:293`](../../proof/lean/AcsEnvelope.lean#L293) | `def` | `B60.ACS.golden_call` |
| `#C047` | [`AcsEnvelope.lean:294`](../../proof/lean/AcsEnvelope.lean#L294) | `def` | `B60.ACS.golden_call_signing` |
| `#C048` | [`AcsEnvelope.lean:295`](../../proof/lean/AcsEnvelope.lean#L295) | `def` | `B60.ACS.golden_forensic` |
| `#C049` | [`AcsEnvelope.lean:296`](../../proof/lean/AcsEnvelope.lean#L296) | `def` | `B60.ACS.golden_forensic_signing` |
| `#C050` | [`AcsEnvelope.lean:297`](../../proof/lean/AcsEnvelope.lean#L297) | `def` | `B60.ACS.golden_cose_ed` |
| `#C051` | [`AcsEnvelope.lean:298`](../../proof/lean/AcsEnvelope.lean#L298) | `def` | `B60.ACS.golden_cose_p256` |
| `#C052` | [`AcsEnvelope.lean:300`](../../proof/lean/AcsEnvelope.lean#L300) | `def` | `B60.ACS.fixtureContext` |
| `#C053` | [`AcsEnvelope.lean:304`](../../proof/lean/AcsEnvelope.lean#L304) | `def` | `B60.ACS.fixtureGrant` |
| `#C054` | [`AcsEnvelope.lean:305`](../../proof/lean/AcsEnvelope.lean#L305) | `def` | `B60.ACS.fixtureCall` |
| `#C055` | [`AcsEnvelope.lean:309`](../../proof/lean/AcsEnvelope.lean#L309) | `def` | `B60.ACS.fixtureForensic` |
| `#C056` | [`AcsEnvelope.lean:338`](../../proof/lean/AcsEnvelope.lean#L338) | `def` | `B60.ACS.toHex` |
| `#C057` | [`AcsEnvelope.lean:342`](../../proof/lean/AcsEnvelope.lean#L342) | `def` | `B60.ACS.runtimeVectors` |
| `#C058` | [`AcsEnvelope.lean:352`](../../proof/lean/AcsEnvelope.lean#L352) | `def` | `B60.ACS.run` |
| `#C059` | [`AcsEnvelope.lean:370`](../../proof/lean/AcsEnvelope.lean#L370) | `def` | `main` |
| `#C060` | [`Babylon.lean:14`](../../proof/lean/Babylon.lean#L14) | `def` | `Babylon.ProbDist` |
| `#C061` | [`Babylon.lean:15`](../../proof/lean/Babylon.lean#L15) | `def` | `Babylon.Morphism` |
| `#C062` | [`Babylon.lean:18`](../../proof/lean/Babylon.lean#L18) | `def` | `Babylon.bayesian_inverse` |
| — | [`Babylon.lean:28`](../../proof/lean/Babylon.lean#L28) | `structure` | `Babylon.BayesianDisintegration` |
| `#C063` | [`Babylon.lean:74`](../../proof/lean/Babylon.lean#L74) | `inductive` | `Babylon.TonnetzState` |
| `#C064` | [`Babylon.lean:81`](../../proof/lean/Babylon.lean#L81) | `def` | `Babylon.canonical_tonnetz_monitor` |
| — | [`Babylon.lean:90`](../../proof/lean/Babylon.lean#L90) | `structure` | `Babylon.TonnetzMonitor` |
| `#C065` | [`Babylon.lean:104`](../../proof/lean/Babylon.lean#L104) | `inductive` | `Babylon.AeonPhase` |
| `#C066` | [`Babylon.lean:111`](../../proof/lean/Babylon.lean#L111) | `def` | `Babylon.HOT_MEMORY_LIMIT` |
| `#C067` | [`Babylon.lean:114`](../../proof/lean/Babylon.lean#L114) | `def` | `Babylon.LANDAUER_FLOOR_AJ` |
| — | [`Babylon.lean:117`](../../proof/lean/Babylon.lean#L117) | `structure` | `Babylon.AeonState` |
| `#C068` | [`Babylon.lean:145`](../../proof/lean/Babylon.lean#L145) | `def` | `Babylon.conformal_reset` |
| `#C069` | [`Babylon.lean:183`](../../proof/lean/Babylon.lean#L183) | `def` | `Babylon.FRACTION_BASE` |
| — | [`Babylon.lean:185`](../../proof/lean/Babylon.lean#L185) | `structure` | `Babylon.Tick60` |
| `#C070` | [`Babylon.lean:190`](../../proof/lean/Babylon.lean#L190) | `def` | `Babylon.add_tick60` |
| `#C071` | [`Babylon.lean:215`](../../proof/lean/Babylon.lean#L215) | `def` | `Babylon.mmr_peaks_bound` |
| — | [`Babylon.lean:225`](../../proof/lean/Babylon.lean#L225) | `structure` | `Babylon.TransductionTensor60` |
| — | [`Babylon.lean:232`](../../proof/lean/Babylon.lean#L232) | `structure` | `Babylon.BeliefDistribution` |
| `#C072` | [`Babylon.lean:237`](../../proof/lean/Babylon.lean#L237) | `def` | `Babylon.fisher_metric_action` |
| `#C073` | [`Babylon.lean:255`](../../proof/lean/Babylon.lean#L255) | `inductive` | `Babylon.AgentIntentVerdict` |
| `#C074` | [`Babylon.lean:261`](../../proof/lean/Babylon.lean#L261) | `def` | `Babylon.effective_payload` |
| `#C075` | [`Babylon.lean:264`](../../proof/lean/Babylon.lean#L264) | `def` | `Babylon.evaluate_agent_intent` |
| `#C076` | [`Babylon.lean:289`](../../proof/lean/Babylon.lean#L289) | `def` | `Babylon.ffi_sexa_add_model` |
| — | [`Babylon.lean:302`](../../proof/lean/Babylon.lean#L302) | `structure` | `Babylon.ReplSession` |
| `#C077` | [`Babylon.lean:309`](../../proof/lean/Babylon.lean#L309) | `def` | `Babylon.eval_repl_step` |
| `#C078` | [`Babylon.lean:315`](../../proof/lean/Babylon.lean#L315) | `def` | `Babylon.run_repl_steps` |
| — | [`Babylon.lean:333`](../../proof/lean/Babylon.lean#L333) | `structure` | `Babylon.CausalEdge` |
| `#C079` | [`Babylon.lean:371`](../../proof/lean/Babylon.lean#L371) | `inductive` | `Babylon.SmallStep` |
| `#C080` | [`Babylon.lean:390`](../../proof/lean/Babylon.lean#L390) | `inductive` | `Babylon.PrivilegeRing` |
| `#C081` | [`Babylon.lean:398`](../../proof/lean/Babylon.lean#L398) | `inductive` | `Babylon.SumerianToponym` |
| `#C082` | [`Babylon.lean:408`](../../proof/lean/Babylon.lean#L408) | `inductive` | `Babylon.EscalationStratum` |
| `#C083` | [`Babylon.lean:417`](../../proof/lean/Babylon.lean#L417) | `def` | `Babylon.stratumToToponym` |
| `#C084` | [`Babylon.lean:426`](../../proof/lean/Babylon.lean#L426) | `def` | `Babylon.toponymToStratum` |
| — | [`Babylon.lean:441`](../../proof/lean/Babylon.lean#L441) | `structure` | `Babylon.WorkspaceModuleNode` |
| `#C085` | [`Babylon.lean:447`](../../proof/lean/Babylon.lean#L447) | `def` | `Babylon.triadCausalQuotient` |
| `#C086` | [`BabylonAOTOracle.lean:15`](../../proof/lean/BabylonAOTOracle.lean#L15) | `def` | `B60.AOTOracle.decodePacked` |
| `#C087` | [`BabylonAOTOracle.lean:26`](../../proof/lean/BabylonAOTOracle.lean#L26) | `def` | `B60.AOTOracle.readUInt64LE` |
| `#C088` | [`BabylonAOTOracle.lean:79`](../../proof/lean/BabylonAOTOracle.lean#L79) | `def` | `B60.AOTOracle.main` |
| `#C089` | [`BabylonAOTOracle.lean:91`](../../proof/lean/BabylonAOTOracle.lean#L91) | `def` | `main` |
| `#C090` | [`BabylonAeonChain.lean:17`](../../proof/lean/BabylonAeonChain.lean#L17) | `def` | `B60.Ledger.aeon_0_events` |
| `#C091` | [`BabylonAeonChain.lean:1524`](../../proof/lean/BabylonAeonChain.lean#L1524) | `def` | `B60.Ledger.aeon_1_events` |
| `#C092` | [`BabylonAeonChain.lean:3031`](../../proof/lean/BabylonAeonChain.lean#L3031) | `def` | `B60.Ledger.aeon_2_events` |
| `#C093` | [`BabylonAeonChain.lean:4538`](../../proof/lean/BabylonAeonChain.lean#L4538) | `def` | `B60.Ledger.aeon_3_events` |
| `#C094` | [`BabylonAeonChain.lean:6045`](../../proof/lean/BabylonAeonChain.lean#L6045) | `def` | `B60.Ledger.aeon_4_events` |
| `#C095` | [`BabylonAeonStress.lean:15`](../../proof/lean/BabylonAeonStress.lean#L15) | `def` | `B60.Ledger.aeon_events` |
| `#C096` | [`BabylonAutoTrace.lean:14`](../../proof/lean/BabylonAutoTrace.lean#L14) | `def` | `B60.Ledger.auto_execution_trace` |
| — | [`BabylonL0Ledger.lean:11`](../../proof/lean/BabylonL0Ledger.lean#L11) | `abbrev` | `Babylon60.L0Ledger.Hash32` |
| `#C097` | [`BabylonL0Ledger.lean:14`](../../proof/lean/BabylonL0Ledger.lean#L14) | `inductive` | `Babylon60.L0Ledger.AttestationTier` |
| — | [`BabylonL0Ledger.lean:22`](../../proof/lean/BabylonL0Ledger.lean#L22) | `structure` | `Babylon60.L0Ledger.AnchoredFact` |
| — | [`BabylonL0Ledger.lean:28`](../../proof/lean/BabylonL0Ledger.lean#L28) | `structure` | `Babylon60.L0Ledger.LedgerEntry` |
| — | [`BabylonL0Ledger.lean:40`](../../proof/lean/BabylonL0Ledger.lean#L40) | `structure` | `Babylon60.L0Ledger.L0Database` |
| `#C098` | [`BabylonL0Ledger.lean:56`](../../proof/lean/BabylonL0Ledger.lean#L56) | `def` | `Babylon60.L0Ledger.EntryWellFormed` |
| `#C099` | [`BabylonL0Ledger.lean:61`](../../proof/lean/BabylonL0Ledger.lean#L61) | `def` | `Babylon60.L0Ledger.L0StateInvariant` |
| `#C100` | [`BabylonL0Ledger.lean:70`](../../proof/lean/BabylonL0Ledger.lean#L70) | `def` | `Babylon60.L0Ledger.TriggerAllowsInsert` |
| `#C101` | [`BabylonL0Ledger.lean:80`](../../proof/lean/BabylonL0Ledger.lean#L80) | `def` | `Babylon60.L0Ledger.appendEntry` |
| `#C102` | [`BabylonL0Ledger.lean:148`](../../proof/lean/BabylonL0Ledger.lean#L148) | `def` | `Babylon60.L0Ledger.witnessFactL0` |
| `#C103` | [`BabylonL0Ledger.lean:151`](../../proof/lean/BabylonL0Ledger.lean#L151) | `def` | `Babylon60.L0Ledger.witnessEntryL0` |
| `#C104` | [`BabylonL0Ledger.lean:161`](../../proof/lean/BabylonL0Ledger.lean#L161) | `def` | `Babylon60.L0Ledger.witnessDbL0` |
| `#C105` | [`BabylonOracle.lean:15`](../../proof/lean/BabylonOracle.lean#L15) | `def` | `B60.Oracle.parseLine` |
| `#C106` | [`BabylonOracle.lean:54`](../../proof/lean/BabylonOracle.lean#L54) | `def` | `main` |
| `#C107` | [`BabylonStressCorrupt.lean:18`](../../proof/lean/BabylonStressCorrupt.lean#L18) | `def` | `B60.Ledger.auto_execution_trace` |
| `#C108` | [`BabylonStressTrace.lean:16`](../../proof/lean/BabylonStressTrace.lean#L16) | `def` | `B60.Ledger.auto_execution_trace` |
| `#C109` | [`BabylonTrace.lean:15`](../../proof/lean/BabylonTrace.lean#L15) | `inductive` | `B60.Ledger.Action` |
| — | [`BabylonTrace.lean:21`](../../proof/lean/BabylonTrace.lean#L21) | `structure` | `B60.Ledger.Event` |
| — | [`BabylonTrace.lean:27`](../../proof/lean/BabylonTrace.lean#L27) | `structure` | `B60.Ledger.LockState` |
| `#C110` | [`BabylonTrace.lean:35`](../../proof/lean/BabylonTrace.lean#L35) | `def` | `B60.Ledger.step` |
| `#C111` | [`BabylonTrace.lean:61`](../../proof/lean/BabylonTrace.lean#L61) | `def` | `B60.Ledger.runAeon` |
| `#C112` | [`BabylonTrace.lean:66`](../../proof/lean/BabylonTrace.lean#L66) | `def` | `B60.Ledger.validateTraceRecursive` |
| `#C113` | [`BabylonTrace.lean:71`](../../proof/lean/BabylonTrace.lean#L71) | `def` | `B60.Ledger.validateTrace` |
| `#C114` | [`BabylonTrace.lean:79`](../../proof/lean/BabylonTrace.lean#L79) | `def` | `B60.Ledger.trace_perfect` |
| `#C115` | [`BabylonTrace.lean:95`](../../proof/lean/BabylonTrace.lean#L95) | `def` | `B60.Ledger.trace_corrupt` |
| `#C116` | [`BabylonTrace.lean:105`](../../proof/lean/BabylonTrace.lean#L105) | `def` | `B60.Ledger.TraceReadsEven` |
| — | [`BabylonTrace.lean:168`](../../proof/lean/BabylonTrace.lean#L168) | `abbrev` | `B60.Ledger.NoTornReadsProp` |
| — | [`BabylonTrace.lean:197`](../../proof/lean/BabylonTrace.lean#L197) | `structure` | `B60.Ledger.BabylonEvent` |
| `#C117` | [`BabylonTrace.lean:210`](../../proof/lean/BabylonTrace.lean#L210) | `def` | `B60.Ledger.ValidBabylonTransition` |
| `#C118` | [`BabylonTrace.lean:258`](../../proof/lean/BabylonTrace.lean#L258) | `def` | `B60.Ledger.trace_step_ok` |
| — | [`BabylonTrace.lean:281`](../../proof/lean/BabylonTrace.lean#L281) | `structure` | `B60.Ledger.CompositeGateState` |
| `#C119` | [`BabylonTrace.lean:293`](../../proof/lean/BabylonTrace.lean#L293) | `def` | `B60.Ledger.ValidCompositeAcceptance` |
| `#C120` | [`BabylonTrace.lean:334`](../../proof/lean/BabylonTrace.lean#L334) | `def` | `B60.Ledger.composite_gate_ok` |
| `#C121` | [`BabylonTrace.lean:351`](../../proof/lean/BabylonTrace.lean#L351) | `def` | `B60.Ledger.composite_gate_ple_91pct_fail` |
| `#C122` | [`C5Affine.lean:8`](../../proof/lean/C5Affine.lean#L8) | `inductive` | `AffineResource` |
| `#C123` | [`C5Affine.lean:14`](../../proof/lean/C5Affine.lean#L14) | `def` | `consume` |
| — | [`C5PortHamiltonian.lean:11`](../../proof/lean/C5PortHamiltonian.lean#L11) | `structure` | `C5REAL.Proof.LatentFixed2D` |
| `#C124` | [`C5PortHamiltonian.lean:17`](../../proof/lean/C5PortHamiltonian.lean#L17) | `def` | `C5REAL.Proof.doubleHamiltonian` |
| `#C125` | [`C5PortHamiltonian.lean:21`](../../proof/lean/C5PortHamiltonian.lean#L21) | `def` | `C5REAL.Proof.stepPHLD` |
| `#C126` | [`C5PortHamiltonian.lean:46`](../../proof/lean/C5PortHamiltonian.lean#L46) | `def` | `C5REAL.Proof.isAligned64` |
| — | [`CanonicalEnvelope.lean:14`](../../proof/lean/CanonicalEnvelope.lean#L14) | `abbrev` | `B60.CBOR.Bytes` |
| `#C127` | [`CanonicalEnvelope.lean:16`](../../proof/lean/CanonicalEnvelope.lean#L16) | `def` | `B60.CBOR.between` |
| `#C128` | [`CanonicalEnvelope.lean:20`](../../proof/lean/CanonicalEnvelope.lean#L20) | `def` | `B60.CBOR.validUtf8` |
| — | [`CanonicalEnvelope.lean:44`](../../proof/lean/CanonicalEnvelope.lean#L44) | `structure` | `B60.CBOR.Codec` |
| `#C129` | [`CanonicalEnvelope.lean:51`](../../proof/lean/CanonicalEnvelope.lean#L51) | `def` | `B60.CBOR.decode` |
| `#C130` | [`CanonicalEnvelope.lean:79`](../../proof/lean/CanonicalEnvelope.lean#L79) | `def` | `B60.CBOR.decodeChecked` |
| `#C131` | [`CanonicalEnvelope.lean:111`](../../proof/lean/CanonicalEnvelope.lean#L111) | `def` | `B60.CBOR.pair` |
| `#C132` | [`CanonicalEnvelope.lean:122`](../../proof/lean/CanonicalEnvelope.lean#L122) | `def` | `B60.CBOR.«prefix»` |
| `#C133` | [`CanonicalEnvelope.lean:130`](../../proof/lean/CanonicalEnvelope.lean#L130) | `def` | `B60.CBOR.uint` |
| `#C134` | [`CanonicalEnvelope.lean:140`](../../proof/lean/CanonicalEnvelope.lean#L140) | `def` | `B60.CBOR.blob` |
| `#C135` | [`CanonicalEnvelope.lean:150`](../../proof/lean/CanonicalEnvelope.lean#L150) | `def` | `B60.CBOR.bstr` |
| `#C136` | [`CanonicalEnvelope.lean:154`](../../proof/lean/CanonicalEnvelope.lean#L154) | `def` | `B60.CBOR.tstr` |
| `#C137` | [`CanonicalEnvelope.lean:156`](../../proof/lean/CanonicalEnvelope.lean#L156) | `def` | `B60.CBOR.boolean` |
| `#C138` | [`CanonicalEnvelope.lean:165`](../../proof/lean/CanonicalEnvelope.lean#L165) | `def` | `B60.CBOR.null` |
| `#C139` | [`CanonicalEnvelope.lean:174`](../../proof/lean/CanonicalEnvelope.lean#L174) | `def` | `B60.CBOR.parseMany` |
| `#C140` | [`CanonicalEnvelope.lean:181`](../../proof/lean/CanonicalEnvelope.lean#L181) | `def` | `B60.CBOR.encodeMany` |
| `#C141` | [`CanonicalEnvelope.lean:195`](../../proof/lean/CanonicalEnvelope.lean#L195) | `def` | `B60.CBOR.arrayOf` |
| `#C142` | [`CanonicalHead.lean:13`](../../proof/lean/CanonicalHead.lean#L13) | `def` | `B60.CBOR.encodeBE` |
| `#C143` | [`CanonicalHead.lean:17`](../../proof/lean/CanonicalHead.lean#L17) | `def` | `B60.CBOR.decodeBE` |
| `#C144` | [`CanonicalHead.lean:47`](../../proof/lean/CanonicalHead.lean#L47) | `def` | `B60.CBOR.headByte` |
| `#C145` | [`CanonicalHead.lean:49`](../../proof/lean/CanonicalHead.lean#L49) | `def` | `B60.CBOR.encodeHead` |
| `#C146` | [`CanonicalHead.lean:56`](../../proof/lean/CanonicalHead.lean#L56) | `def` | `B60.CBOR.decodePayload` |
| `#C147` | [`CanonicalHead.lean:67`](../../proof/lean/CanonicalHead.lean#L67) | `def` | `B60.CBOR.decodeHead` |
| `#C148` | [`Destiladora_838c463da193b48f.lean:15`](../../proof/lean/Destiladora_838c463da193b48f.lean#L15) | `def` | `B60.Destiladora.C_838c463da193b48f.expectedAstPrefix` |
| `#C149` | [`Destiladora_838c463da193b48f.lean:16`](../../proof/lean/Destiladora_838c463da193b48f.lean#L16) | `def` | `B60.Destiladora.C_838c463da193b48f.expectedFilesCount` |
| `#C150` | [`Destiladora_838c463da193b48f.lean:19`](../../proof/lean/Destiladora_838c463da193b48f.lean#L19) | `def` | `B60.Destiladora.C_838c463da193b48f.seqlock_write_begin` |
| `#C151` | [`Destiladora_838c463da193b48f.lean:20`](../../proof/lean/Destiladora_838c463da193b48f.lean#L20) | `def` | `B60.Destiladora.C_838c463da193b48f.seqlock_write_commit` |
| — | [`Destiladora_838c463da193b48f.lean:33`](../../proof/lean/Destiladora_838c463da193b48f.lean#L33) | `structure` | `B60.Destiladora.C_838c463da193b48f.SystemState` |
| — | [`Destiladora_838c463da193b48f.lean:39`](../../proof/lean/Destiladora_838c463da193b48f.lean#L39) | `structure` | `B60.Destiladora.C_838c463da193b48f.FastPathContext` |
| `#C152` | [`Destiladora_838c463da193b48f.lean:44`](../../proof/lean/Destiladora_838c463da193b48f.lean#L44) | `inductive` | `B60.Destiladora.C_838c463da193b48f.FastPathVerdict` |
| `#C153` | [`Destiladora_838c463da193b48f.lean:49`](../../proof/lean/Destiladora_838c463da193b48f.lean#L49) | `inductive` | `B60.Destiladora.C_838c463da193b48f.Action` |
| `#C154` | [`Destiladora_838c463da193b48f.lean:55`](../../proof/lean/Destiladora_838c463da193b48f.lean#L55) | `def` | `B60.Destiladora.C_838c463da193b48f.evalFastPath` |
| `#C155` | [`Destiladora_838c463da193b48f.lean:78`](../../proof/lean/Destiladora_838c463da193b48f.lean#L78) | `def` | `B60.Destiladora.C_838c463da193b48f.transition` |
| `#C156` | [`Destiladora_838c463da193b48f.lean:86`](../../proof/lean/Destiladora_838c463da193b48f.lean#L86) | `def` | `B60.Destiladora.C_838c463da193b48f.runTrace` |
| `#C157` | [`Destiladora_838c463da193b48f.lean:90`](../../proof/lean/Destiladora_838c463da193b48f.lean#L90) | `def` | `B60.Destiladora.C_838c463da193b48f.invariant` |
| `#C158` | [`ExampleSeqlockTrace.lean:7`](../../proof/lean/ExampleSeqlockTrace.lean#L7) | `inductive` | `B60.ExampleSeqlockTrace.Action` |
| — | [`ExampleSeqlockTrace.lean:10`](../../proof/lean/ExampleSeqlockTrace.lean#L10) | `structure` | `B60.ExampleSeqlockTrace.SeqlockEvent` |
| `#C159` | [`ExampleSeqlockTrace.lean:15`](../../proof/lean/ExampleSeqlockTrace.lean#L15) | `def` | `B60.ExampleSeqlockTrace.validateTransition` |
| `#C160` | [`ExampleSeqlockTrace.lean:31`](../../proof/lean/ExampleSeqlockTrace.lean#L31) | `def` | `B60.ExampleSeqlockTrace.isValidTrace` |
| `#C161` | [`ExampleSeqlockTrace.lean:40`](../../proof/lean/ExampleSeqlockTrace.lean#L40) | `def` | `B60.ExampleSeqlockTrace.validCycle` |
| `#C162` | [`HolographicPoC.lean:16`](../../proof/lean/HolographicPoC.lean#L16) | `def` | `AlertaColapso` |
| `#C163` | [`LarsaEquivocationSafety.lean:14`](../../proof/lean/LarsaEquivocationSafety.lean#L14) | `def` | `LarsaEquivocationSafety.quorum_threshold` |
| `#C164` | [`LarsaEquivocationSafety.lean:17`](../../proof/lean/LarsaEquivocationSafety.lean#L17) | `def` | `LarsaEquivocationSafety.total_nodes` |
| — | [`LarsaEquivocationSafety.lean:47`](../../proof/lean/LarsaEquivocationSafety.lean#L47) | `structure` | `LarsaEquivocationSafety.ConsensusInstance` |
| `#C165` | [`LarsaEquivocationSafety.lean:55`](../../proof/lean/LarsaEquivocationSafety.lean#L55) | `def` | `LarsaEquivocationSafety.instance_f1` |
| — | [`LarsaEquivocationSafety.lean:104`](../../proof/lean/LarsaEquivocationSafety.lean#L104) | `structure` | `LarsaEquivocationSafety.VerifiedQuorumInvariant` |
| `#C166` | [`MolochLandauer.lean:14`](../../proof/lean/MolochLandauer.lean#L14) | `inductive` | `Babylon.MolochLandauer.ActionClass` |
| — | [`MolochLandauer.lean:22`](../../proof/lean/MolochLandauer.lean#L22) | `structure` | `Babylon.MolochLandauer.AgentAction` |
| `#C167` | [`MolochLandauer.lean:33`](../../proof/lean/MolochLandauer.lean#L33) | `def` | `Babylon.MolochLandauer.is_moloch_extraction` |
| `#C168` | [`MolochLandauer.lean:42`](../../proof/lean/MolochLandauer.lean#L42) | `def` | `Babylon.MolochLandauer.landauer_penalty` |
| `#C169` | [`MolochLandauer.lean:49`](../../proof/lean/MolochLandauer.lean#L49) | `def` | `Babylon.MolochLandauer.net_exergy_payoff` |
| `#C170` | [`MolochLandauer.lean:53`](../../proof/lean/MolochLandauer.lean#L53) | `def` | `Babylon.MolochLandauer.is_admissible` |
| `#C171` | [`MolochLandauer.lean:105`](../../proof/lean/MolochLandauer.lean#L105) | `def` | `Babylon.MolochLandauer.total_externalized_entropy` |
| `#C172` | [`MolochLandauer.lean:110`](../../proof/lean/MolochLandauer.lean#L110) | `def` | `Babylon.MolochLandauer.total_landauer_penalties` |
| `#C173` | [`NavierStokesBKM.lean:11`](../../proof/lean/NavierStokesBKM.lean#L11) | `inductive` | `B60.NavierStokes.VortexAction` |
| — | [`NavierStokesBKM.lean:19`](../../proof/lean/NavierStokesBKM.lean#L19) | `structure` | `B60.NavierStokes.FluidEvent` |
| — | [`NavierStokesBKM.lean:25`](../../proof/lean/NavierStokesBKM.lean#L25) | `structure` | `B60.NavierStokes.FluidState` |
| `#C174` | [`NavierStokesBKM.lean:35`](../../proof/lean/NavierStokesBKM.lean#L35) | `def` | `B60.NavierStokes.BKM_CRITICAL_THRESHOLD` |
| `#C175` | [`NavierStokesBKM.lean:38`](../../proof/lean/NavierStokesBKM.lean#L38) | `def` | `B60.NavierStokes.CONSTANTIN_FEFFERMAN_SMOOTH_FLOOR` |
| `#C176` | [`NavierStokesBKM.lean:41`](../../proof/lean/NavierStokesBKM.lean#L41) | `def` | `B60.NavierStokes.step` |
| `#C177` | [`NavierStokesBKM.lean:59`](../../proof/lean/NavierStokesBKM.lean#L59) | `def` | `B60.NavierStokes.runTrace` |
| `#C178` | [`NavierStokesBKM.lean:63`](../../proof/lean/NavierStokesBKM.lean#L63) | `def` | `B60.NavierStokes.initialState` |
| `#C179` | [`NavierStokesBKM.lean:67`](../../proof/lean/NavierStokesBKM.lean#L67) | `inductive` | `B60.NavierStokes.AuditResult` |
| `#C180` | [`NavierStokesBKM.lean:73`](../../proof/lean/NavierStokesBKM.lean#L73) | `def` | `B60.NavierStokes.auditTrace` |
| `#C181` | [`NavierStokesBKM.lean:87`](../../proof/lean/NavierStokesBKM.lean#L87) | `def` | `B60.NavierStokes.trace_depleted` |
| `#C182` | [`NavierStokesBKM.lean:100`](../../proof/lean/NavierStokesBKM.lean#L100) | `def` | `B60.NavierStokes.trace_singular_candidate` |
| — | [`NavierStokesBKM.lean:117`](../../proof/lean/NavierStokesBKM.lean#L117) | `structure` | `B60.NavierStokes.DiscreteChainComplex` |
| — | [`NavierStokesBKM.lean:136`](../../proof/lean/NavierStokesBKM.lean#L136) | `structure` | `B60.NavierStokes.HelmholtzHodgeComponents` |
| `#C183` | [`NavierStokesBKM.lean:142`](../../proof/lean/NavierStokesBKM.lean#L142) | `def` | `B60.NavierStokes.isStrictlySolenoidal` |
| `#C184` | [`NavierStokesOracle.lean:15`](../../proof/lean/NavierStokesOracle.lean#L15) | `def` | `B60.NavierStokes.Oracle.parseLine` |
| `#C185` | [`NavierStokesOracle.lean:57`](../../proof/lean/NavierStokesOracle.lean#L57) | `def` | `main` |
| — | [`NavierStokesSobolevKato.lean:13`](../../proof/lean/NavierStokesSobolevKato.lean#L13) | `structure` | `B60.NavierStokes.SobolevKato.DiscreteHilbertSpace` |
| `#C186` | [`NavierStokesSobolevKato.lean:23`](../../proof/lean/NavierStokesSobolevKato.lean#L23) | `def` | `B60.NavierStokes.SobolevKato.isSobolevContinuousEmbedding` |
| `#C187` | [`NavierStokesSobolevKato.lean:40`](../../proof/lean/NavierStokesSobolevKato.lean#L40) | `def` | `B60.NavierStokes.SobolevKato.isKatoLocalWellPosed` |
| `#C188` | [`NavierStokesSobolevKato.lean:51`](../../proof/lean/NavierStokesSobolevKato.lean#L51) | `def` | `B60.NavierStokes.SobolevKato.verifyDissipationCurryHoward` |
| — | [`NavierStokesSobolevKato.lean:62`](../../proof/lean/NavierStokesSobolevKato.lean#L62) | `structure` | `B60.NavierStokes.SobolevKato.SexagesimalInterval` |
| `#C189` | [`NavierStokesSobolevKato.lean:67`](../../proof/lean/NavierStokesSobolevKato.lean#L67) | `def` | `B60.NavierStokes.SobolevKato.intervalContains` |
| `#C190` | [`NavierStokesSobolevKato.lean:79`](../../proof/lean/NavierStokesSobolevKato.lean#L79) | `def` | `B60.NavierStokes.SobolevKato.gronwallBound` |
| `#C191` | [`NavierStokesSobolevKato.lean:82`](../../proof/lean/NavierStokesSobolevKato.lean#L82) | `def` | `B60.NavierStokes.SobolevKato.isGronwallBounded` |
| — | [`NavierStokesSobolevKato.lean:93`](../../proof/lean/NavierStokesSobolevKato.lean#L93) | `structure` | `B60.NavierStokes.SobolevKato.CausalStepState` |
| `#C192` | [`NavierStokesSobolevKato.lean:99`](../../proof/lean/NavierStokesSobolevKato.lean#L99) | `def` | `B60.NavierStokes.SobolevKato.transitionCausalStep` |
| `#C193` | [`NavierStokesSobolevKato.lean:105`](../../proof/lean/NavierStokesSobolevKato.lean#L105) | `def` | `B60.NavierStokes.SobolevKato.verifyCausalTrace` |
| `#C194` | [`NavierStokesSobolevKato.lean:117`](../../proof/lean/NavierStokesSobolevKato.lean#L117) | `def` | `B60.NavierStokes.SobolevKato.AXIOM_ID_SOBOLEV_EMBEDDING` |
| `#C195` | [`NavierStokesSobolevKato.lean:118`](../../proof/lean/NavierStokesSobolevKato.lean#L118) | `def` | `B60.NavierStokes.SobolevKato.AXIOM_ID_KATO_LOCAL_EXISTENCE` |
| `#C196` | [`NavierStokesSobolevKato.lean:119`](../../proof/lean/NavierStokesSobolevKato.lean#L119) | `def` | `B60.NavierStokes.SobolevKato.AXIOM_ID_BKM_CRITERION` |
| `#C197` | [`NavierStokesSobolevKato.lean:120`](../../proof/lean/NavierStokesSobolevKato.lean#L120) | `def` | `B60.NavierStokes.SobolevKato.AXIOM_ID_GRONWALL_LEMMA` |
| — | [`NavierStokesSobolevKato.lean:131`](../../proof/lean/NavierStokesSobolevKato.lean#L131) | `structure` | `B60.NavierStokes.SobolevKato.RegularityCertificate` |
| `#C198` | [`NavierStokesSobolevKato.lean:137`](../../proof/lean/NavierStokesSobolevKato.lean#L137) | `def` | `B60.NavierStokes.SobolevKato.isMillenniumRegular` |
| `#C199` | [`NemesisWave4.lean:15`](../../proof/lean/NemesisWave4.lean#L15) | `inductive` | `NemesisWave4.WalState` |
| `#C200` | [`NemesisWave4.lean:23`](../../proof/lean/NemesisWave4.lean#L23) | `inductive` | `NemesisWave4.IsolationStrength` |
| — | [`NemesisWave4.lean:30`](../../proof/lean/NemesisWave4.lean#L30) | `structure` | `NemesisWave4.ResourceMonitorState` |
| `#C201` | [`NemesisWave4.lean:41`](../../proof/lean/NemesisWave4.lean#L41) | `inductive` | `NemesisWave4.EcpEvent` |
| `#C202` | [`NemesisWave4.lean:50`](../../proof/lean/NemesisWave4.lean#L50) | `def` | `NemesisWave4.stepEcp` |
| `#C203` | [`NemesisWave4.lean:91`](../../proof/lean/NemesisWave4.lean#L91) | `def` | `NemesisWave4.validateEcpTrace` |
| `#C204` | [`NemesisWave4.lean:99`](../../proof/lean/NemesisWave4.lean#L99) | `def` | `NemesisWave4.evaluateSealStrength` |
| `#C205` | [`NemesisWave4.lean:112`](../../proof/lean/NemesisWave4.lean#L112) | `def` | `NemesisWave4.validateDeploymentPermit` |
| `#C206` | [`NemesisWave4.lean:121`](../../proof/lean/NemesisWave4.lean#L121) | `def` | `NemesisWave4.initialMonitor` |
| `#C207` | [`NemesisWave4.lean:132`](../../proof/lean/NemesisWave4.lean#L132) | `def` | `NemesisWave4.validWave4Trace` |
| `#C208` | [`NemesisWave4.lean:141`](../../proof/lean/NemesisWave4.lean#L141) | `def` | `NemesisWave4.corruptFencingRaceTrace` |
| `#C209` | [`NemesisWave4.lean:149`](../../proof/lean/NemesisWave4.lean#L149) | `def` | `NemesisWave4.corruptBlindRetryTrace` |
| `#C210` | [`NemesisWave4.lean:156`](../../proof/lean/NemesisWave4.lean#L156) | `def` | `NemesisWave4.corruptBudgetCompositionTrace` |
| — | [`TicketEnvelope.lean:19`](../../proof/lean/TicketEnvelope.lean#L19) | `abbrev` | `B60.Ticket.Control` |
| `#C211` | [`TicketEnvelope.lean:20`](../../proof/lean/TicketEnvelope.lean#L20) | `def` | `B60.Ticket.controlTriple` |
| `#C212` | [`TicketEnvelope.lean:22`](../../proof/lean/TicketEnvelope.lean#L22) | `def` | `B60.Ticket.controlCodec` |
| — | [`TicketEnvelope.lean:46`](../../proof/lean/TicketEnvelope.lean#L46) | `abbrev` | `B60.Ticket.Payload` |
| `#C213` | [`TicketEnvelope.lean:49`](../../proof/lean/TicketEnvelope.lean#L49) | `def` | `B60.Ticket.payloadCodec` |
| `#C214` | [`TicketEnvelope.lean:54`](../../proof/lean/TicketEnvelope.lean#L54) | `def` | `B60.Ticket.utf8` |
| `#C215` | [`TicketEnvelope.lean:55`](../../proof/lean/TicketEnvelope.lean#L55) | `def` | `B60.Ticket.text` |
| `#C216` | [`TicketEnvelope.lean:58`](../../proof/lean/TicketEnvelope.lean#L58) | `def` | `B60.Ticket.shape` |
| — | [`TicketEnvelope.lean:74`](../../proof/lean/TicketEnvelope.lean#L74) | `abbrev` | `B60.Ticket.Ticket` |
| `#C217` | [`TicketEnvelope.lean:76`](../../proof/lean/TicketEnvelope.lean#L76) | `def` | `B60.Ticket.encode` |
| `#C218` | [`TicketEnvelope.lean:77`](../../proof/lean/TicketEnvelope.lean#L77) | `def` | `B60.Ticket.decode` |
| — | [`TicketEnvelope.lean:107`](../../proof/lean/TicketEnvelope.lean#L107) | `abbrev` | `B60.Ticket.SignedTicket` |
| `#C219` | [`TicketEnvelope.lean:108`](../../proof/lean/TicketEnvelope.lean#L108) | `def` | `B60.Ticket.encodeExternal` |
| `#C220` | [`TicketEnvelope.lean:109`](../../proof/lean/TicketEnvelope.lean#L109) | `def` | `B60.Ticket.decodeExternal` |
| `#C221` | [`TicketEnvelope.lean:129`](../../proof/lean/TicketEnvelope.lean#L129) | `def` | `B60.Ticket.hexDigit` |
| `#C222` | [`TicketEnvelope.lean:135`](../../proof/lean/TicketEnvelope.lean#L135) | `def` | `B60.Ticket.parseHexChars` |
| `#C223` | [`TicketEnvelope.lean:144`](../../proof/lean/TicketEnvelope.lean#L144) | `def` | `B60.Ticket.parseHex` |
| `#C224` | [`TicketEnvelope.lean:145`](../../proof/lean/TicketEnvelope.lean#L145) | `def` | `B60.Ticket.hex` |
| `#C225` | [`TicketEnvelope.lean:150`](../../proof/lean/TicketEnvelope.lean#L150) | `def` | `B60.Ticket.generatorKey` |
| `#C226` | [`TicketEnvelope.lean:154`](../../proof/lean/TicketEnvelope.lean#L154) | `def` | `B60.Ticket.fixturePayload` |
| `#C227` | [`TicketEnvelope.lean:161`](../../proof/lean/TicketEnvelope.lean#L161) | `def` | `B60.Ticket.fixture` |
| `#C228` | [`TicketEnvelope.lean:200`](../../proof/lean/TicketEnvelope.lean#L200) | `def` | `main` |

## 5. Criterios de aceptación

La fuente de verdad es el código Lean y sus tipos elaborados. El JSON es un índice versionado; el presente Markdown es una vista documental. Antes de promover una garantía a material ejecutivo o contractual, exigir: (i) declaración completa, (ii) compilación en la toolchain fijada, (iii) `#print axioms` y tratamiento correcto de fixtures negativos, (iv) hipótesis locales y campos obligatorios no ocultos, y (v) evidencia independiente de refinamiento si se menciona Rust, CPU, red, entropía física o ecuaciones diferenciales.

El exportador del repositorio es [`scripts/c5_quality_gates/export_lean_census.py`](../../scripts/c5_quality_gates/export_lean_census.py). Su opción `--verify` valida cardinales e inventario bajo el árbol local; no demuestra correspondencia con software de producción ni reemplaza la compilación Lean y la revalidación axiomática.

**No modificar ni renombrar declaraciones Lean para limpiar el marketing. La honestidad se aplica al censo, las etiquetas y los contratos de evidencia.**

