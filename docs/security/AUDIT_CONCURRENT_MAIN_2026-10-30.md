# Auditoría de cambios concurrentes en main — 30 de octubre de 2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

Aceptación local de una captura acotada, sobre `2aef1202a019daa36b3985f8e957e846c2400671`. Se consolidan
20 unidades funcionales, 22 fuentes productivas y sus regresiones en 33 rutas.
Candidato de código: `065da849438170720d0fb2a4938cc194ffb78aad`. No se ejecutó push.
El árbol principal conserva cambios concurrentes pendientes: la aceptación corresponde
al contenido de los commits, no a ejecutar el árbol sucio completo.

## Evidencia y reproducción

Resumen, hashes, comandos y commits (material no distribuido: `evidence/concurrent-main-audit-20261030/summary.json`).
Cada unidad se aplicó incrementalmente en un checkout aislado y pasó sus pruebas,
Ruff y MyPy cuando correspondían. El conjunto pasó **354 pruebas, sin fallos ni
omisiones**, más cuatro fixtures del Worker JavaScript. MyPy pasó sobre 30 fuentes.
Semántica, presupuesto local, topología y `git diff --check` pasaron.
Se comprobó además `--staged` antes de cada commit.

La primera suite Lote12 del candidato aún sin particionar tuvo 287 pases y una
omisión por no seleccionar Lean; no fue la suite completa del repositorio ni una prueba de HEAD base.
La suite formal original se repitió con el compilador fijado 4.34.0-rc2 y pasó
23 casos sin omisiones; esto no cierra el defecto CLI del catálogo excluido.
La revisión independiente encontró y corrigió el setup del caso Python 3.10:
`raising=False` permite simular la ausencia de `add_note`. No se ejecutó una suite
completa sobre un intérprete 3.10.

Los comandos exactos de la suite consolidada están en `acceptance.pytest.command`
del resumen. Reproducirlos sobre el candidato limpio, con `uv run --locked --extra dev
python -m pytest`, y ejecutar por separado:

```sh
node --experimental-vm-modules tests/test_swarm100_lot12_s3_worker.mjs
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
```

Las reglas globales y la telemetría de ghost listeners quedaron fuera del control local.
Los datos de las pruebas, firmas, KDF, SQLite y procesos son fixtures temporales;
no se consultaron claves privadas del operador ni se ejecutaron servicios o despliegues.

## Commits de código y pruebas

Los casos de archivos mixtos se incorporaron incrementalmente con su fuente.
Los casos dependientes de unidades rechazadas permanecen fuera del índice aceptado.

| Commit | Unidad |
| --- | --- |
| `a9b6c29db453` | snapshots |
| `40134392e577` | identity |
| `b199f5fd5b7f` | key-metadata |
| `c49805af7573` | licenses |
| `328a88736866` | ledger-queue |
| `cc6331965194` | bounty-admission |
| `f95fc46ee5fe` | dag-cleanup |
| `695b0a729c94` | email-delivery |
| `8aef497f045f` | native-queue |
| `d215dfbdfd4c` | git-preflight |
| `612f9ce8f30b` | instruction-install |
| `fe0a424ac63a` | dns-filter |
| `fb6c061a347b` | youtube-argv |
| `39197dbf89b9` | input-bounds |
| `788c4e90fca4` | routing-policy |
| `cc3b170a6cb9` | psd-firewall |
| `203c9a15aaf6` | formal-status |
| `9cd02cec9289` | m0-manifest |
| `f810a9a887f5` | honest-reports |
| `065da8494381` | swarm-simulation |

El emisor formal y su demostración se consolidan juntos: retiran elegibilidad
`PROVED` y declaran `NOT_VERIFIED`/`NOT_IMPLEMENTED`. No implementan un comprobador
Lean, no certifican Rust y no retiran automáticamente artefactos ya desplegados.
El sealer conserva los bytes de firma y la serialización v1; solo adelanta la
carga de identidad y permite creación exclusivamente ante `FileNotFoundError`.
M0 comprueba consistencia criptográfica interna: la clave pública viaja en el
paquete; esta mejora no añade un ancla externa de autoridad ni acredita su contenido.

## Bloques retenidos (Cerrados el 2026-11-06 en `bdaa454c`)

| ID | Nivel | Estado | Resolución verificada (`bdaa454c`) |
| --- | --- | --- | --- |
| AC-01 | P1 | **CERRADO** | `cortex_purge_anergy.py`: `_assert_confined_path` rechaza symlinks en `PROJECT_ROOT` y destinos de archivo (`ARCHIVE_*`, `AUDIT_YAML`), y `_git_tracked_root_files` preserva archivos rastreados por Git y manifiestos de raíz (`test_swarm100_lot12_s4_regressions.py`). |
| AC-02 | P1 | **CERRADO** | `sandbox.py`: bloqueados atributos de introspección de generadores/frames (`gi_frame`, `gi_code`, `cr_frame`, `ag_frame`, `f_locals`, `f_builtins`, `tb_frame`) y transporte acotado en el padre vía `_run_bounded_subprocess` con `start_new_session=True` y `os.killpg` (`test_swarm100_lot12_s5_regressions.py`). |
| AC-03 | P2 | **CERRADO** | `moskv_kernel.py`: registro `_claim_status` (`QUEUED`, `COMMITTED`, `FAILED`, `UNKNOWN` ante `CancelledError`), `get_claim_status(claim_id)` y cierre de admisión en `finally` de `bft_state_loop` (`test_swarm100_lot12_s3_regressions.py`). |
| AC-04 | P2 | **CERRADO (v1 Congelado)** | `ledger_snapshot_engine.py`: mantenido contrato `v1` (firma Ed25519 sobre los 32 bytes crudos del Merkle root) en paridad estricta con el verificador Rust (`test_ledger_snapshot_engine.py`). |
| AC-05 | P2 | **CERRADO** | `sharur_100_full_spectrum_auditor.py`: añadida `_strict_json_equal` recursiva sensible a tipos (`type(left) is type(right)`) distinguiendo `True`/`False` de `1`/`0` (`test_swarm100_lot12_s6_reports_regressions.py`). |
| AC-06 | P2 | **CERRADO** | `gen_oncology_primitives.py`: validación de cardinalidad (`len(primitives) == 300`) previa a escritura y escritura atómica (`_atomic_write_text`) en `export_json`, `export_lean4` y `main()` (`test_swarm100_lot12_s6_formal_regressions.py`). |

Las siete fuentes completas correspondientes, el fragmento v2 del sealer y las
regresiones dependientes se preservan como trabajo pendiente. Las rutas concretas y
el tipo de evidencia de cada observación constan en `blocked` del resumen.

El nuevo Ring-0 se conserva conjuntamente con su inclusión, tests, SQL, Lean y
cambio Cargo. Está **NO_VERIFICADO**: no se amplía esta consolidación a tres backends
hardware. La revisión estática señaló recepción TPM incompleta, divergencia SQL/Lean
en génesis y un teorema de unicidad que no demuestra identidad de entradas. Las pruebas
con hardware simulado no acreditan dispositivos reales ni enlace de la FFI Apple.

Los cambios posteriores de compliance, políticas regulatorias, CI y reconciliación
Lote12/Lote13 también permanecen fuera. Sus informes no sustituyen esta aceptación.

## Preservación y límites

La captura inicial conserva 116 rutas con hashes, permisos y symlinks.
Antes de integrar había 205 rutas pendientes; se respaldaron íntegramente fuera
de Git. La integración preservó bytes y permisos de 202 rutas.
Solo se ajustaron tres archivos completos, comprobando primero sus hashes:

- `scripts/c5_l1_ledger/ledger_snapshot_engine.py`: compatibilidad de notas de excepción.
- `tests/test_swarm100_lot12_s1_regressions.py`: tipos y regresión de limpieza.
- `tests/test_swarm100_lot12_s3_regressions.py`: tipos de fixtures y sustitución de métodos.

El avance de `main` no modificó ningún archivo del árbol de trabajo. Su índice quedó
limpio tras integrar; los fragmentos excluidos continúan como cambios pendientes.
La copia privada verificable está en
`/Users/borjafernandezangulo/.codex/local-core-evidence/concurrent-main-audit-20261030T014607Z`.
No contiene material privado de claves de operador ni deliberaciones del modelo.

Los dos límites heredados en informes y reescritura Git quedaron cerrados el
2026-11-06: `rewrite_commits.py` deshabilita el `git push --force` automático y
`sharur_100_conversation_reporters.py` escapa los campos interpolados en HTML (`html.escape`).
No se certifican persistencia del keyring del sistema, cortes físicos de alimentación,
autenticidad del contenido M0 ni aislamiento universal. La atomicidad JSON es por archivo.
