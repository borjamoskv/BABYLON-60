# Specification: Finding Evidence Contract (FL-VERIFY-01)

**Status:** PROPOSED / UNTESTED  
**Scope:** nivel bloque. Modelo sin efectos; lectura del ledger de `VerificationGate` para validar autorizaciones.  
**Implementation:** `01_KISH_ENGINE/babylon60/verification/finding_contract.py`  
**Falsifiers:** `tests/test_finding_evidence_contract.py`

---

## 1. Propósito

Separar tres actos que hoy no tienen un objeto común:

| Acto | Objeto | Pregunta que responde |
| :--- | :--- | :--- |
| Generación | `Finding` | ¿Qué comportamiento prohibido se afirma sobre qué artefacto (por digest)? |
| Verificación | `ReproductionRun` | ¿Qué comportamiento se observó, sobre qué artefacto y quién lo observó? |
| Autorización | `Authorization` | ¿Qué efecto concreto se autorizó para ese hallazgo? |

Estado actual observado en el repositorio: `CausalSignOffReceipt` (`verification_gate.py`) registra autorizaciones encadenadas por SHA-256 sin referencia a un artefacto; `EvidenceRecord` (`kernel/grounding_interceptor.py`) exige digest no vacío para citas; `M0EvidencePackCompiler` exporta evidencia firmada. Ninguno modela hallazgos ni reproducciones.

## 2. Invariante

```text
VERIFIED(f) <=> existe run tal que
    run.finding_id == f.finding_id
    run.artifact_digest == f.inspected_artifact_digest
    run.observed_behavior_id == f.prohibited_behavior_id
    run.outcome == REPRODUCED
    run.verifier_id != f.producer_id
```

Un efecto sobre `f` exige `VERIFIED(f)` y una `Authorization` con el mismo `finding_id` y la misma `action`.

## 3. Reglas de rechazo (fail-closed)

- Digest vacío, mal formado o igual al SHA-256 de la cadena vacía.
- Reproducción sobre un artefacto con digest distinto al inspeccionado.
- Comportamiento observado distinto al prohibido afirmado. Una prueba válida de otra cosa no verifica el hallazgo.
- Productor igual a verificador.
- Efecto sin autorización para ese hallazgo y esa acción.

## 4. Límites declarados

- `ReproductionRun` es un dato declarado: ningún componente ejecuta aún la reproducción en sandbox ni demuestra que `artifact_digest` sea el hash real de lo ejecutado.
- `Authorization.signoff_receipt_digest` se contrasta con `audit_ledger` mediante `verify_authorization_in_ledger`: exige cadena SHA-256 íntegra y un recibo `APPROVED` con el mismo `execution_id` (= `finding_id`) y `action_name`. La cadena del ledger detecta alteraciones, pero no las impide ni constituye atestación hardware; la lectura usa la conexión interna de `VerificationGate`.
- Las garantías se limitan al modelo. No hay medición sobre vulnerabilidades reales.

## 5. Hipótesis experimental (no es un resultado)

Un verificador independiente con contexto entre repositorios y reproducción dinámica detecta más vulnerabilidades reales que un revisor limitado al diff, sin aumentar significativamente los falsos positivos.

Diseño propuesto: 200 cambios controlados; configuraciones A (revisión del diff), B (revisión independiente con grafo de dependencias) y C (B más reproducción aislada y atestación); mismo presupuesto de inferencia y conjunto de pruebas reservado.

Criterios de refutación para C: `false_verified_findings = 0`, `evidence_artifact_mismatches = 0`, `unauthorized_effects = 0`. Un solo hallazgo `VERIFIED` sin reproducción válida refuta el contrato.

Predicción: C mejora el recall en vulnerabilidades entre repositorios al menos 20 puntos porcentuales respecto a A, con un aumento de falsos positivos de como máximo 5 puntos.

Origen: informe de radar del 27/10/2026 (síntesis de terceros; las fuentes primarias no se han verificado directamente).

## 6. Pendiente

1. Hecho: vínculo de `Authorization` con el ledger de `VerificationGate`, sin modificar `verification_gate.py`.
2. Reproducción ejecutable en sandbox con digest calculado por el ejecutor, no declarado (diseño en la sección 7).
3. Arnés A/B/C, solo después del punto 2.

## 7. Diseño: ejecutor de reproducción (PROPOSED, sin implementar)

Base reutilizable: `kernel/mcp_sandbox_validator.py` ya ejecuta código bajo Seatbelt `(deny default)`, repite sondas de confinamiento (lectura/escritura externa, symlink, TCP, UDP, Unix, subprocess, `posix_spawn`, fork) antes de cada ejecución, fija la copia ejecutada por digest y usa testigos del proceso padre (canario, listeners). Su `_execute` acopla esas sondas al protocolo MCP; el ejecutor necesita extraerlas a una función reutilizable.

### 7.1 Decisiones

| Punto | Decisión | Motivo |
| :--- | :--- | :--- |
| Digest del artefacto | Lo calcula el ejecutor sobre los bytes fijados que ejecuta; `ReproductionRun.artifact_digest` deja de ser un dato de entrada. | Elimina el digest declarado. |
| Algoritmo | Etiquetar el digest (`sha256:` / `blake3:`). El validador usa BLAKE3 y el contrato SHA-256; ambos producen 64 hex y serían indistinguibles por longitud. | Evita una igualdad de digests entre algoritmos distintos. |
| Oráculo | Cada `prohibited_behavior_id` referencia un oráculo determinista (predicado sobre testigos observables), fijado antes de ejecutar e identificado por `oracle_digest` en `Finding` y en `ReproductionRun`. Lo define el verificador, no el productor. | Lección ETH: la reproducción debe acreditar el comportamiento afirmado, no otro. El oráculo es la formalización. |
| Testigo | El oráculo evalúa observaciones del proceso padre (canario alterado, conexión aceptada, archivo creado), nunca lo que el exploit informa de sí mismo. | `INV_C5_NEMESIS_EVIDENCE_CONTRACT`: DENY != Proof, observación independiente. |
| Resultado | `REPRODUCED` / `NOT_REPRODUCED` / `INCONCLUSIVE`. Fallo de sondas, timeout o plataforma sin backend produce `INCONCLUSIVE`, nunca `NOT_REPRODUCED`. | No confundir "no se pudo comprobar" con "no ocurre". |
| Plataforma | Solo macOS (Seatbelt). Otras plataformas: `INCONCLUSIVE`, sin ejecución sin confinar. | Fail-closed; el validador ya prohíbe recurrir a Python sin sandbox. |
| Registro | `log_digest` de stdout/stderr y versión del ejecutor en el `ReproductionRun`. | Reproducibilidad y auditoría. |

### 7.2 Invariante revisado

```text
VERIFIED(f) <=> existe run tal que
    run producido por el ejecutor (no declarado)
    run.artifact_digest == f.inspected_artifact_digest   (mismo algoritmo)
    run.oracle_digest   == f.oracle_digest
    run.outcome == REPRODUCED
    run.verifier_id != f.producer_id
```

### 7.3 Decisión abierta

Ejecutar código de explotación, incluso confinado, puede ser un efecto de runtime protegido según el contrato Ring-0 (atestación biométrica). Debe decidirse si cada ejecución de reproducción requiere autorización del operador o solo las reproducciones fuera del conjunto de pruebas.
