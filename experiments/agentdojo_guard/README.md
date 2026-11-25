# P0 — BABYLON GUARD en AgentDojo

Campaña para medir el ASR dirigido y la utilidad de `McpCapabilityBroker` frente a inyección indirecta de prompts.
Proyecto aislado: su `uv.lock` no toca el lock raíz.

## Estado

| Fase | Estado |
| --- | --- |
| F1 subproyecto + lock fijado (`agentdojo==0.1.35`, MIT) | hecho |
| F2 binding PyO3: 10 efectos, alcance explícito, `commit_once`, `blake3_digest` | hecho; G1 en verde |
| F3 adaptador sobre el ejecutor de herramientas de AgentDojo (`src/b60_guard/`) + 74 herramientas selladas (`policy/tool_effects.yaml`) | hecho; sellado en Git (`dbdb54a2`) |
| F3.5 runner completo (`run.py` + `analysis.py`: Wilson, McNemar, Holm, frontera SVG, `--max-cases`, gate `--confirm-budget-usd`) | hecho; validado sin API |
| F4 piloto (`banking`, 1 modelo, A0/A1/A2c/A2-strict) | pendiente; requiere modelo y `--confirm-budget-usd` |

## Construcción del broker

```bash
cargo build --locked -p babylon60_root --lib --features python --target-dir target/py
export BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/py/debug/libbabylon60.dylib"   # .so en Linux
```

## Entorno del experimento

```bash
cd experiments/agentdojo_guard
uv sync --locked
uv run --locked python -c "import agentdojo, importlib.metadata as m; print(m.version('agentdojo'))"
```

El protocolo, los brazos, las métricas y el criterio de afirmación prerregistrado están en el plan aprobado de la campaña.
Ningún resultado de este directorio constituye una afirmación SOTA hasta cumplir ese criterio.
