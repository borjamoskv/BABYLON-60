# 🛸 [C5-REAL] SWARM OPERATIONS & DEPLOYMENT MANUAL

**Dominio**: `babylon60.swarm`
**Exergía**: 100% (C5-REAL)
**Autor**: borjamoskv

---

## 1. DESPLIEGUE DEL ENJAMBRE (CENTAURO ENGINE)

El `CentauroEngine` es el orquestador principal. Todo despliegue debe utilizar las Formaciones definidas en `Formation` y evitar el *active polling*.

### A. Ejecución de Misiones (BFT Consensus)
```python
from babylon60.extensions.swarm.centauro_engine import CentauroEngine, Formation

async def deploy_bft_mission():
    engine = CentauroEngine(tolerance=0.67)

    # [P0] Despliegue con Consenso Bizantino (Formation.BLITZ -> 3 agentes)
    result = await engine.engage(
        mission="Falsificar hipótesis de escalabilidad en AsyncSignalBus",
        formation=Formation.BLITZ
    )

    if result["status"] == "success":
        print(f"Solución cristializada: {result['solution']}")
    else:
        print(f"ALEPH-Ω Leap Triggered: {result.get('reason')}")
```

### B. Ejecución de Escuadrones Dedicados (Ej: EpistemicSquadron)
```python
from babylon60.swarm.c5_epistemic_auditor import EpistemicSquadron

async def deploy_auditor():
    # El engine puede ser None si no requiere inyección de base de datos
    squadron = EpistemicSquadron(engine=None)

    # 1 Deploy -> 1 Ledger Entry (INV_ONE_MUTATION)
    report = await squadron.deploy(target_pattern=None) # Audita invariantes clave
    print(report)
```

---

## 2. MONITOREO Y ALERTAS TERMODINÁMICAS

Las violaciones termodinámicas disparan alertas `WARNING` o `CRITICAL` vía el módulo `logging`.

- **VOID BREACH**: Ocurre cuando `latency_ms` > 32.0ms. Esto activa el mecanismo de **Slashing Dinámico** sobre el nodo, reduciendo su reputación para evitar paradas térmicas en el enjambre.
- **LANDAUER Epistemic Filter**: Rechaza *payloads* que carezcan de entropía (ej. largos bloques de texto sin estructura o código puro). Evita la asimilación de "Anergía" y marca la señal como `FAILURE`.

---

## 3. ROLLBACK Y MITIGACIÓN (Σ8 WORKTREE ISOLATION)

Bajo la doctrina C5-REAL, la única mitigación válida para estado corrupto es criptográfica (Git Sentinel).

1. **Aborto Limpio**: Si el consenso BFT falla, la señal resultante activa la excepción y evita la escritura en la base de datos (SAGA-1).
2. **Rollback Físico**: Si el estado persistido está corrupto, usa Git.
   ```bash
   # NO edites manualmente los hashes. Destruye la anomalía con:
   git reset --hard HEAD
   git clean -fd
   ```
3. **Purgar Anergía Local**:
   Si el enjambre se estanca en inanición (SQLITE_BUSY), limpia el daemon:
   ```bash
   .venv/bin/python scripts/c5_exec.py "killall -9 python"
   ```

---

## 4. INVARIANTE P0: NO LLM SLOP

El enjambre **no** está diseñado para charlar. Los agentes virtuales DEBEN devolver hashes, AST diffs, diccionarios estructurados, o binarios codificados. Todo token de cortesía disminuye el *budget* termodinámico y activará el `LandauerGuard`.
