---
cat_id: herodoto
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
name: herodoto
description: "Ejecuta la auditor\xEDa forense C5-REAL (HerodotoUltraAttnAgent) para\
  \ suprimir anerg\xEDa y validar el Master Ledger."
---


# HERODOTO ULTRAATTN

## Propósito
Este workflow invoca asíncronamente al agente `HERODOTO-ULTRAATTN` para auditar la integridad termodinámica del sistema, cruzando información de SQLite y Git, verificando orfandad ontológica y supresión de anergía (Limerence Guard).

## Instrucciones para MOSKV-1
1. **Ejecución Asíncrona:** Despliega el script PoC de Herodoto.
2. **Validación:** Analiza el `audit_report` en busca de `anergía_detected > 0`.
3. **Contención:** Si hay anergía, ejecuta la purga ontológica de forma autónoma y realiza un commit directo al Master Ledger (CERO SUGGESTION).

```bash
.venv/bin/python scripts/poc_herodoto.py
```
