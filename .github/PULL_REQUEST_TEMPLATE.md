<!-- C5-REAL EXERGY CERTIFIED -->
---
name: C5-REAL Compliance PR
about: Plantilla para asegurar validación empírica y contención estocástica antes del Merge.
title: "[C5-REAL] - "
labels: ["compliance", "security"]
assignees: borjamoskv
---

## 🛑 Invariante de Falsación Empírica (INV-3)
Ninguna abstracción entra en el tronco principal sin una demostración de falsabilidad.

- [ ] He ejecutado los test de estrés empíricos.
- [ ] La métrica empírica de contención estocástica ha sido documentada.
- [ ] Los bloqueos del *Commit Gate* han funcionado como Fail-Stop determinista.

## ⚖️ Compliance y Cap Contractual (INV-2)
- [ ] He comprobado que los fallos estocásticos de la IA se resuelven en un cuelgue explícito (Fail-Stop) y NO en un comportamiento indefinido.
- [ ] Esta PR NO incluye terminología teórica o metafórica ("Límite de Landauer", "Consciencia") en la capa visible para el auditor/cliente (cumpliendo SOC 2, AI Act).

## 🔒 Zero-Residual y Fricción (Nivel 0)
- [ ] No se están trackeando cachés de Python, Rust (`.rmeta`, `.dylib`), ni bases de datos de sesión (`-shm`, `-wal`).
- [ ] He ejecutado el Protocolo de Apoptosis localmente antes del commit.

## Evidencia (Logs/Receipts SCITT)
*Pega aquí el Log del Kernel Rust o la salida de la atestación:*

```
[Output del BFT Kernel / C5-REAL]
```
