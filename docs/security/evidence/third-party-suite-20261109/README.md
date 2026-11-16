# Suite adversarial reproducible por terceros (2026-11-09)
Comando exacto: `uv run --locked python scripts/guards/c5_third_party_adversarial_suite.py --repeat 30 --output docs/security/evidence/third-party-suite-20261109/report.json`
Observado: `PASS` en 5,49 s (Darwin arm64, Python 3.14.7). Informe [report.json](report.json), SHA-256 `8c9de22495ec8004e9ad663c5a7f58e2b273a4544316ec94716b46b74ae39c88` (comprobar con `shasum -a 256 report.json`).
Cubre: `SIGKILL` real, symlink/inodo TOCTOU, replay con 16 hilos, bypass y lockfile ausente, benchmark ×30 (media, desviación, IC95) y ledger + certificado Ed25519 verificados con `standalone_verify`.
Reproducible en estructura y veredicto, no en valores: el rendimiento varía por ejecución. Compara intervalos IC95; el p99 tiene colas anchas y no sustenta una diferencia.
Límite, host único: una máquina y una sesión; ningún tercero lo ha ejecutado aún.
Límite, baseline propio: el motor sin mediación lo escribe este mismo script, no es un producto externo.
Límite, sin pérdida de alimentación: solo `SIGKILL`; corte eléctrico y caché NVMe siguen `NO_VERIFICADO`.
Límite, alcance: los motores Python imitan la lógica de `AUTH_006` y no ejercitan el ejecutor Rust.
Límite, firma: la clave Ed25519 es efímera por ejecución; el recibo prueba integridad, no autoría.
