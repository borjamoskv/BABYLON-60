---
title: Modelo de Seguridad BABYLON-60
status: Causal-Determinist
version: 4.3.0
---

# MODELO DE SEGURIDAD — Ledger Asíncrono-persist

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

> **Régimen Causal-Determinist**
> Este documento define el **modelo de amenazas**, **fronteras de seguridad**, y las **garantías explícitas** del ledger.

---

## 1. Garantías del Ledger

| Propiedad | Mecanismo | Qué Demuestra |
|:---|:---|:---|
| **Integridad** | Cadena hash BLAKE3 | El contenido de la entrada no fue alterado tras su escritura |
| **Procedencia (Provenance)** | Taint causal + `agent_id` | Quién escribió la entrada y bajo qué contexto |
| **Ordenamiento** | Reloj de Lamport + WAL journal | Las escrituras están serializadas y son reproducibles |
| **No-duplicación** | Clave de idempotencia UUID v5 | La misma escritura lógica no puede insertarse dos veces |
| **Anclaje Temporal** | Git Sentinel (local) | La entrada existía antes de la marca de tiempo de un commit dado |

## 2. Lo que el Ledger NO Garantiza

| Propiedad | Razón |
|:---|:---|
| **Corrección Semántica** | Un hash demuestra que el contenido no cambió, no que su semántica sea correcta. |
| **Autorización** | El ledger registra *quién* escribió; no fuerza *quién tiene permiso* sin una capa externa. |
| **Almacenamiento Tamper-proof** | Un atacante con acceso OS al filesystem puede borrar la BD. La cadena de hash solo lo detecta post-mortem. |
| **Consenso Global** | Los niveles L1–L3 proveen consistencia local únicamente. BFT (L4) no está listo para producción. |
| **Cumplimiento Regulatorio** | Este no es un registro auditado certificado para GDPR, SOC2 o PCI-DSS. |

---

## 3. Modelo de Amenazas (Threat Model)

### 3.1 Amenazas en Alcance (In-Scope)

| Amenaza | Mitigación |
|:---|:---|
| Bit-rot silente o modificación accidental histórica | La cadena BLAKE3 se rompe en lectura — detectado en verificación. |
| Inyección de escritura duplicada por un agente | Clave de idempotencia UUID v5 rechaza duplicados. |
| Condición de carrera entre escritores concurrentes | Cola `asyncio.Queue` single-writer + WAL journal serializa todo. |
| Contención de lock en SQLite | Pragma de concurrencia WAL (ver [Especificación Técnica](spec_technical.md)). |
| Escritura parcial por aniquilación de proceso | Journal WAL hace rollback automático al reiniciar. |
| Escrituras sin atribución | `causal_taint` + `agent_id` obligatorios en toda entrada. |

### 3.2 Amenazas Fuera de Alcance (Out-of-Scope)

| Amenaza | Razón |
|:---|:---|
| Atacante con acceso a OS/Filesystem | El reemplazo total de BD esquiva la detección de hash-chain in situ. |
| Compromiso de primitivas (BLAKE3 / SHA3-256) | Fuera del alcance del Dominio C5-REAL. |
| Agentes Bizantinos en enjambre distribuido | Requiere BFT L4 — solo prototipo. |
| Compromiso de cadena de suministro (Supply-chain) | Riesgos estándar de empaquetado Python/Rust aplican. |

---

## 4. Primitivas Criptográficas

| Uso | Algoritmo | Estado |
|:---|:---|:---|
| Hash-chain de Entradas | BLAKE3 | Activo (Python `blake3` o Rust `strike_rs`) |
| Hash de Recibo / Auditoría | SHA3-256 | Activo |
| Firmado Opcional | Ed25519 vía `pynacl` | Opcional (extra `[crypto]`) |
| Derivación Clave/Password | Argon2 vía `argon2-cffi` | Opcional (extra `[crypto]`) |
| Testigo Temporal L1 | OTS / BTC OP_RETURN | Investigación — no implementado |

---

## 5. Verificación de Integridad

Para verificar la cadena completa de cualquier ledger almacenado:

```python
from babylon60.bft.ledger_actor import verify_chain

result = verify_chain(db_path="master_ledger.db")
print(result)  # {"valid": True, "entries": 4821, "broken_at": None}
```

Una cadena rota devuelve el índice exacto de la entrada y tanto el hash esperado como el actual.

---

## 6. Separación de Datos

- Cada inquilino/workspace utiliza un archivo `.db` aislado.
- No existen tablas compartidas entre inquilinos.
- La base central `Ledger Asíncrono.db` es de **solo-lectura** y no debe ser escrita por el SDK. Use bases sidecar (`nexus_anchors.db`, `master_ledger.db`).