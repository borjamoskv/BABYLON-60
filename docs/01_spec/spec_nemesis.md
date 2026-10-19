---
title: NEMESIS Verified Security Domain Specification
status: Causal-Determinist
version: 5.0.0
---

# NEMESIS: Verified Security Domain Specification

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)
[![NEMESIS Invariants](https://img.shields.io/badge/NEMESIS-6--Invariants-00E676?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

**AI agents decide in milliseconds. BABYLON-60 controls whether those decisions become irreversible real-world effects.**

NEMESIS defines a verified security domain for agentic execution. It validates security invariants through bounded exhaustive model checking, adversarial kernel execution, and deterministic crash-recovery testing.

Formalmente:
$$
\forall e \in \mathcal{E}(M,B): I(e) \quad \not\Rightarrow \quad \forall e \in \mathcal{E}(\text{real world}): I(e)
$$
NEMESIS delimita el dominio estricto donde la equivalencia se preserva en silicio.

---

## 1. Core Definitions (The Four Public Pillars)

Internamente, el modelo formal evalúa seis propiedades matemáticas rigurosas. Públicamente, la arquitectura se proyecta en cuatro pilares fundamentales:

- **AUTHORITY:** ¿Quién está facultado para autorizar, bajo qué época de capacidad y en qué contexto transaccional?
- **IDENTITY:** ¿Cuál es la identidad localizadora exacta del recurso y cuál es su estado físico verificable?
- **EFFECT:** ¿Qué mutación u operación irreversible concreta está permitida sobre dicho recurso?
- **RECOVERY:** ¿Puede el sistema recuperarse ante caídas arbitrarias de forma estrictamente determinista e idempotente, permitiendo a terceros auditar la prueba inmutable de lo sucedido?

---

## 2. Invariants (The Six Canonical Invariants)

### NEM-I1: EFFECT_AUTHORIZATION
$$
\boxed{\neg Authorized(a, o, e, t) \Rightarrow \neg Effected(a, o, e, t)}
$$
Donde:
- $a$: autoridad / principal invocador.
- $o$: identidad localizadora del objeto (`ObjectLocatorIdentity`).
- $e$: tipo de efecto ($e \in \{\text{READ}, \text{MUTATE}, \text{DELETE}, \text{CHMOD}, \text{RENAME}\}$).
- $t$: época de autoridad / contexto transaccional (`authority_epoch`).

Ninguna operación destructiva o mutadora se ejecuta si la autorización no cubre exactamente el tipo de efecto solicitado sobre el inodo específico bajo la época activa.

### NEM-I2: VERIFIED_COMMIT
$$
\boxed{Committed(tx) \Rightarrow Verified(tx) \land EffectObserved(tx)}
$$
La verificación no es una etiqueta abstracta, sino un predicado conjuntivo cerrado:
$$
\begin{aligned}
Verified(tx) := \; & authority\_valid(tx) \\
& \land capability\_epoch\_valid(tx) \\
& \land identity\_match(tx) \\
& \land effect\_allowed(tx) \\
& \land quarantine\_isolated(tx) \\
& \land ledger\_precondition\_valid(tx)
\end{aligned}
$$
El commit exige simultáneamente que la verificación se satisfaga y que el efecto físico haya sido observado y confirmado en el descriptor del archivo.

### NEM-I3: PATH_OBLIVION
$$
\boxed{State(tx) \ge Quarantined \Rightarrow ResolveOriginalPath(tx) = Forbidden}
$$
A partir del instante en que el objeto ingresa en cuarentena mediante secuestro atómico, queda **terminantemente prohibido** volver a resolver `original_path` para re-abrir, re-inspeccionar (`stat`), computar hash o contrastar identidad.
$$
original\_path \in \text{AuditMetadataOnly}
$$
La única referencia válida al objeto es `(quarantine_dirfd, transaction_nonce)`.

### NEM-I4: CRASH_RECOVERABILITY
$$
\boxed{Crash(tx, s) \Rightarrow Recover(tx, s) \in \{Committed, Aborted, SecurityAbort\}}
$$
Cualquier caída del proceso o reinicio forzado durante el ciclo de vida de la transacción transiciona deterministamente a uno de los tres estados terminales canónicos. Ninguna transacción queda en estado indefinido o corrupto.

### NEM-I5: RECOVERY_IDEMPOTENCE
$$
\boxed{Recover(Recover(tx)) = Recover(tx)} \quad \iff \quad \boxed{R(R(s)) = R(s)}
$$
La rutina de recuperación ante fallos es matemáticamente idempotente. Si se inyecta un crash durante la propia ejecución del recovery, los reintentos sucesivos producen exactamente el mismo estado terminal sin provocar doble destrucción, fugas de descriptores ni estados huérfanos.

### NEM-I6: AUTHORITY_FRESHNESS
$$
\boxed{Committed(tx) \Rightarrow AuthorityEpoch_{commit} = AuthorityEpoch_{verified}}
$$
Cierra la ventana de carrera de revocación de capacidades: si la autoridad es revocada o su época caduca entre la autorización inicial y el commit del efecto, la transacción se aborta de inmediato (`SecurityAbort` / `AuthorityEpochRevoked`) y el objeto secuestrado se preserva intacto en cuarentena.

---

## 3. Object Identity Contract

Para erradicar contradicciones formales entre la destrucción de un archivo y su mutación, la identidad se desacopla estrictamente en dos estructuras ortogonales:

```rust
pub struct ObjectLocatorIdentity {
    pub fs: u32,
    pub dev: u64,
    pub ino: u64,
    pub file_type: u32,
    pub capability_root_id: [u8; 32],
}

pub struct ObjectState {
    pub hash: [u8; 32],
    pub size: u64,
    pub metadata: u32,
}
```

### Contrato para DELETE_FILE
El objeto eliminado debe coincidir en localizador y en estado previo:
```text
authorized_locator == verified_locator == destroyed_locator
authorized_state   == verified_pre_state
```

### Contrato para MUTATE_FILE
El localizador se mantiene invariante sobre el mismo descriptor, mientras el estado transiciona legítimamente:
```text
authorized_locator == verified_locator == effected_locator
pre_state ──[payload mutate on same fd]──> post_state
```

### Defensa Anti-TOCTOU
Si un atacante gana la carrera de symlinks o renames concurrentes:
```text
attacker wins race
→ wrong object quarantined
→ identity mismatch (locator or pre_state)
→ SECURITY_ABORT
→ wrong object NOT destroyed (preserved in quarantine for criminal forensics)
```

---

## 4. Fault Models

NEMESIS aísla los dominios de fallo para garantizar fronteras de recuperación inequívocas:

```text
NEMESIS-CRASH
├── PROCESS
│   └── deterministic SIGKILL injection at each state
│
└── DURABILITY
    └── persistence-order fault model (fsync / WAL boundary)
```

---

## 5. Scope & TCB Delimitation

```text
VERIFIED SECURITY DOMAIN
────────────────────────
✓ Local filesystem under tested threat model
✓ Broker-owned quarantine directory (mode 0700)
✓ Same mount / filesystem boundary (st_dev matching)
✓ Attacker cannot mutate quarantine directory contents
✓ Declared capability root
✓ Tested APFS backend (macOS ARM64)
✓ Tested Linux backend (renameat2 / O_TMPFILE)

OUT OF SCOPE / FAIL CLOSED (TCB Boundaries)
───────────────────────────────────────────
✗ Network filesystems (NFS, CIFS, SMB) → fail-closed
✗ Cross-device fallback (EXDEV) → fail-closed
✗ Attacker-controlled kernel / hypervisor
✗ Compromised broker process memory
✗ Compromised signing authority / Secure Enclave private key
✗ Compromised filesystem implementation / storage controller firmware
✗ DMA / physical memory bus extraction attacks
```

> **Nota de rigor epistemológico:** La designación de backend se mantiene como `tested APFS backend` y `tested Linux backend` hasta que la evidencia reproducible del pipeline emita el atestado formal firmado. "Verified" se reserva exclusivamente para los artefactos con certificación criptográfica en silicio.

---

## 6. Architecture

```text
                          NEMESIS
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
     MODEL                 KERNEL                CRASH
     loom                 real OS               recovery
       │                     │                     │
 protocol logic        syscall reality         durability
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                        INVARIANTS
                 (NEM-I1 through NEM-I6)
                             │
                             ▼
                        ATTESTATION
                             │
                   ┌─────────┼─────────┐
                   ▼         ▼         ▼
                AUDITOR    CISO    REPRODUCE
```

---

## 7. Evidence & Reproducibility

### Target Acceptance Criteria (Acceptance Profile)

El perfil objetivo de aceptación `NEMESIS-100` fija umbrales para una evaluación futura. La existencia o aprobación de la suite de tests no demuestra que esos umbrales se hayan alcanzado:

```text
NEMESIS-100 ACCEPTANCE PROFILE
──────────────────────────────────────────────────────────
REAL KERNEL ADVERSARIAL EXECUTION
  attack attempts target                         1,000,000
  security aborts (expected decoys caught)         >30,000
  unauthorized mutations                                 0
  unauthorized deletions                                 0
  capability root escapes                                0
  unverified commits                                     0
  ledger/effect divergences                              0
  ambiguous recoveries                                   0
  recovery idempotence failures                          0

MODEL CHECKING (LOOM)
  model executions explored                       >280,000
  invariant violations                                   0
```

### Formato de Reporte Automatizado (`nemesis-report/v2`)

El generador registra una invocación local de `adversarial_nemesis` como evidencia pendiente de auditoría. `PASS` se limita al resultado de esa suite y exige un resumen completo, contadores coherentes con los casos observados y al menos un test ejecutado. La cobertura de invariantes y la aceptación NEMESIS-100 quedan pendientes de evaluación.

`evidence_available` indica la presencia de salida o error del runner; `executed_test` indica que se observaron casos ejecutados. La salida original de stdout y stderr se conserva para revisión. `INCOMPLETE`, `NO_TESTS_EXECUTED`, `RUNNER_ERROR` y `FAIL` provocan código de salida 1 tras escribir el reporte. Los tests ignorados no cuentan como ejecutados. `--stdout` emite JSON en stdout y los diagnósticos van a stderr.

El plazo del runner incluye compilación y tests: 600 segundos por defecto, configurable con `--timeout-seconds` (valor finito y positivo). Un vencimiento registra `TIMEOUT`, conserva la salida parcial y devuelve código 1. En macOS/Linux se termina el grupo de procesos POSIX creado para el runner; en otras plataformas la terminación se limita al proceso directo. Los descendientes que abandonen ese grupo quedan fuera de esta frontera. Si las tuberías no se cierran, la fase de limpieza limita su espera a 5 segundos, cierra sus lectores y limita la espera del proceso padre a otros 5 segundos; `cleanup_complete: false` registra una limpieza incompleta.

La salida del proceso se recoge como bytes. Cuando una salida no es UTF-8 válida, se conserva completa en `stdout_raw_base64` o `stderr_raw_base64`, y la vista textual usa caracteres de reemplazo. `output_decoding_complete: false` impide un resultado `PASS` y deja la revisión de esa evidencia pendiente.

El reporte se escribe mediante reemplazo atómico en `reports/nemesis_evidence_report_v2.json`, conservando los informes históricos v1. El commit identifica HEAD; `working_tree_dirty` indica si el árbol tenía cambios al observarlo (`null` cuando Git no pudo consultarse). Las observaciones del sistema de archivos sin resultado se registran como `UNKNOWN`.

Los campos `evidence_payload_sha256` y `evidence_payload_sha3_256` son digests del payload. Para recalcularlos, se retiran ambos campos y se serializa el resto con `json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")`. Son sumas de comprobación sin autenticación: un tercero puede recomputarlas. Una firma verificable requeriría un firmante independiente. El generador no construye una raíz Merkle ni emite una firma COSE/Ed25519.

Ejemplo de estructura con un solo caso ilustrativo (no representa una ejecución publicada):

```json
{
  "schema": "nemesis-report/v2",
  "report_version": "2.1.0",
  "commit": "<git-commit-sha>",
  "working_tree_dirty": true,
  "timestamp_iso": "<utc-timestamp>",
  "status": "EVIDENCE_COLLECTED_PENDING_AUDIT",
  "evidence_assessment": {
    "evidence_available": true,
    "executed_test": true,
    "scope": "One local integration-suite invocation; invariant coverage and NEMESIS-100 acceptance remain unassessed."
  },
  "platform_observed": {
    "os": "<observed-os>",
    "arch": "<observed-architecture>",
    "filesystem": "<observed-filesystem-or-UNKNOWN>"
  },
  "test_suite": {
    "name": "adversarial_nemesis",
    "command": ["cargo", "test", "--test", "adversarial_nemesis", "--features", "cortex-persist"],
    "result": "PASS",
    "return_code": 0,
    "runner_error": null,
    "timeout_seconds": 600.0,
    "timed_out": false,
    "cleanup_complete": true,
    "termination_scope": "posix_process_group",
    "duration_s": 0.0,
    "tests_total": 1,
    "tests_executed": 1,
    "tests_passed": 1,
    "tests_failed": 0,
    "tests_ignored": 0,
    "cases": [{"name": "illustrative_case", "result": "OK"}],
    "parsing_complete": true,
    "reported_counts": {"passed": 1, "failed": 0, "ignored": 0, "measured": 0, "filtered_out": 0},
    "summary_result": "ok",
    "stdout": "running 1 test\ntest illustrative_case ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0s\n",
    "stderr": "",
    "output_decoding_complete": true,
    "stdout_raw_base64": null,
    "stderr_raw_base64": null
  },
  "evidence_payload_sha256": "sha256:<digest>",
  "evidence_payload_sha3_256": "sha3-256:<digest>"
}
```
