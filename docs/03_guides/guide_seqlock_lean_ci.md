# CI de integración Seqlock y Lean

El job `verify-seqlock` de [Verify Lean Proofs](../../.github/workflows/verify_lean.yml)
prepara un paquete Lake aislado, copia `BabylonTrace.lean` sin modificarlo e instala
el toolchain fijado por el proyecto. Ejecuta las dos regresiones Seqlock con
`--locked --exact --include-ignored`; exige una prueba aprobada y cero omitidas
por invocación. Un filtro sin coincidencias, una omisión o un fallo aborta el job.
El job es independiente del build Lean general y se activa con cambios del crate,
modelo, toolchain, configuración de Cargo, script o pruebas del gate.

Reproducción local (requiere `elan`, Cargo y Python 3; usar una salida nueva):

```sh
python3 scripts/c5_quality_gates/verify_seqlock_lean.py --output-dir /tmp/b60-seqlock-ci
```

El [script](../../scripts/c5_quality_gates/verify_seqlock_lean.py) conserva logs,
fuentes copiadas y `summary.json`; CI los sube incluso si falla. Las regresiones
siguen marcadas `ignore` para suites locales sin Lean, pero este job exige su
ejecución. Los errores Lean de las entradas deliberadamente falsas son rechazos
esperados; los controles válidos deben compilar. Esto comprueba la integración del
emisor con el modelo de eventos, no la concurrencia física del Seqlock Rust.
