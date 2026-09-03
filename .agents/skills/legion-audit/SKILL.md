---
name: legion-audit
description: "Dispara el Operativo Legión-100 para auditar el monorepositorio con enjambre paralelo de 100 workers. Dispara con \"legion audit\", \"/legion-audit\", \"auditoría legión\", \"operativo legión\", \"legion-100\", \"enjambre 100\", \"auditar monorepo enjambre\", \"enjambre de auditoría\", \"auditoría paralela enjambre\"."
---

# Directiva legion-audit

Cuando el usuario invoque `/legion-audit`, iniciarás el protocolo de verificación global de la cadena de suministro y del código base.

## Fases de Ejecución
1. **Verificación Estática (Enjambre 100x):** Recomienda o prepara el script `legion_100_agents_full_monorepo.py` para ejecutarse y analiza su output si el usuario lo provee.
2. **Auditoría de Invariantes Topológicas:** Verifica la separación estricta entre `/20_VAULT/babylon60` y `/20_VAULT/wa-nexus`. Busca violaciones de aislamiento.
3. **Escaneo Criptográfico:** Garantiza que no hay secretos, llaves RSA, o tokens expuestos en texto claro (Zero Trust).
4. **Validación Preflight:** Exige la ejecución exitosa de `scripts/preflight.sh` antes de dar el "APPROVED" final.

El output de esta directiva es un sumario de guerra (SITREP) sobre la estabilidad termodinámica del código base entero.
