# Muestra histórica saneada de rechazo de evidencia (BABYLON-60 v4.0)

**Estado actual de verificación:** NO_VERIFICADO. Esta copia no determina conformidad legal ni autoriza su publicación como certificación.

**Procedencia de la muestra ampliada:** commit 67d1476b1a33b827df79a341a6ace49fc323a56f, ruta auditoria_ai_act.md, blob 346ced1f3ad8e49efe344f75d5ddba0005b6d536.

**Antecedente histórico:** commit 2876357cabbcd9513b396b3c44c650252b64125d, misma ruta, blob c89879e4c685fae075d5ea97bd03a4305ff7394f. El antecedente contiene otra clave pública y una firma truncada; no acredita la firma completa de la muestra ampliada. Ambos blobs permiten recuperar los bytes de cada versión desde Git.

Los valores, firmas, hashes y resultados siguientes son declaraciones de la muestra histórica; no se han revalidado durante este saneamiento. La firma reproducida no cubre los bytes modificados de esta copia. No se ha emitido un sello ni una atestación nueva.

**Referencia normativa declarada en origen:** Reglamento UE 2024/1689 / AESIA.
**Autoridad mencionada en origen:** Agencia Española de Supervisión de Inteligencia Artificial (AESIA) / UE.
**ID histórico:** `EU-AIA-REPORT-3F748C89C881A80C`
**Sistema de muestra:** `SISTEMA_HIPOTECARIO_ALFA` | **Operador de muestra:** `CUATRECASAS_AUDIT`
**Emisión declarada en origen:** `2026-09-21T17:22:03Z` | **Estado de muestra:** `CUARENTENA_SELLADA_WORM`

> **CONTEXTO HISTÓRICO DE PRUEBA (VECTOR NEGATIVO FAIL-CLOSED)**
> La muestra registra una divergencia entre la raíz recomputada (`0000...0000`) y el `global_hash` del manifiesto (`Coincide = False`), con resultado declarado `EVIDENCE_MISMATCH_NON_COMPLIANT`. Este saneamiento no vuelve a ejecutar el verificador ni una evaluación de conformidad.

---

## Resumen de la muestra histórica

La fuente describe una ejecución de BABYLON-60 v4.0 y un ledger Merkle-Causal. Esa descripción histórica no acredita el estado del sistema actual.

- **Global Merkle Root:** `QUARANTINE_SEAL_07cfe8cff8971c3869086ade1a7d4dc24025ec1f0f29f46c5359ec8887508060`
- **Firma Digital (Fingerprint):** `3f748c89c881a80cddd6f9dabe7a358d66449e68e26ea33521863bb90f240946`

---

## Resultados criptográficos declarados en origen

| Parámetro | Valor |
| :--- | :--- |
| Ledger | `.cortex/causal_gate.db` |
| Cadena íntegra (verify_integrity) | `True` |
| Merkle root recomputado | `0000000000000000000000000000000000000000000000000000000000000000` |
| Coincide con global_hash del manifiesto | `False` |
| **Veredicto** | **EVIDENCE_MISMATCH_NON_COMPLIANT** |

---

## Hardware saneado y declaraciones históricas de ciclo de vida

| Parámetro | Valor |
| :--- | :--- |
| Enclave de Hardware | `SOFTWARE_ONLY_UNATTESTED` |
| Estado de Atestación Hardware | `SOFTWARE_ONLY_UNATTESTED` |
| Verificado en Hardware | `False` |
| Hardware UUID | No reproducido |
| Plataforma / Modelo | `Darwin_arm64` |
| Expiración declarada en origen, sin revalidar | `2026-12-20T17:22:03Z` |
| Estado de revocación actual | NO_VERIFICADO |
| Estado de revocación declarado en origen | `ACTIVE` |
| Hash de revocación copiado del origen, sin revalidar | `6b27bf53961ddec206ead55584ad410adc75b4a728f7d808af58d2716992688b` |
| Autoridad de revocación declarada en origen | `urn:babylon60:revocation:CUATRECASAS_AUDIT` |

---

## Firma Ed25519 histórica reproducida, sin revalidar

- **Algoritmo:** `Ed25519` | **Clave efímera:** `False`
- **Clave pública:** `3b6a27bcceb6a42d62a3a8d02a6f0d73653215771de243a63ac048a18b59da29`
- **Firma:** `ea670d0af686abb83de344450329dd0152dc1d074fd78b14b04e0b1ace8104233cec5e6f79bae7ba30822a9d1066de0a9c80b7441c038fa684bc8392fa662802`
- **SHA-256 del payload firmado:** `e51092cd77c2d88e57c04ae343de82ccf803238bcc343d4adcae40d32dfc6942`

---

## Matriz histórica de la muestra de rechazo

| Requisito / Artículo | Mecanismo Técnico BABYLON-60 v4.0 | Estado | Hash de Evidencia |
| :--- | :--- | :--- | :--- |
| **Art. 9: Sistema de Gestión de Riesgos** | Podador Termodinámico de AST + Motor de Auto-Falsación (Interruptor de Hombre Muerto) | EVIDENCE_MISMATCH_NON_COMPLIANT | `00524247c9332048cad531358f7cc3c02e5e7f6292d13593c237af9f31566955` |
| **Art. 10: Gobernanza de Datos y Linaje** | Memoria Tipada Sexagesimal F60 + Linaje DAG Merkle-Causal | EVIDENCE_MISMATCH_NON_COMPLIANT | `31c2143639fc7b8dcb7bb2aa314a22a6ebd42826774e301b9428fb762a83f875` |
| **Art. 11: Documentación Técnica y Demostración Lean 4** | Exportación Automática de Proof IR a Lemas de Teorema Lean 4 | EVIDENCE_MISMATCH_NON_COMPLIANT | `6dd49c3e1a47034b3350abbe28e1d81f1e237e89ec0dc5caa1fa8071e5be1fd7` |
| **Art. 12: Conservación de Registros / Logging WORM** | Ledger DAG Merkle-Causal + Sello Criptográfico de Cuarentena WORM | EVIDENCE_MISMATCH_NON_COMPLIANT | `e524452453d984d2d681c715cdada561e9e0170297ea106c3a39d1927ecb31e8` |
| **Art. 14: Control y Supervisión Humana** | Visualizador Armónico Tonnetz + Inspección de Trazas Causal IR | EVIDENCE_MISMATCH_NON_COMPLIANT | `4212ed7b516c89c81a5122a8248a346811f4a98921efa8b3e0b4f97a2fc34dc8` |

---

<sub>BABYLON-60 v4.0 — muestra histórica saneada, sin nuevo sello.</sub>
