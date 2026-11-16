# Contrato de tarea — Lote 4

Resultado: corregir C0061/C0083/C0086/C0087, con reproducción previa; evaluar
C0060/C0088 solo por compartir las mismas rutas y con evidencia propia.
Únicas fuentes productivas: proof/bundles/attestation_bundle_v1/verify,
scripts/generate_attestation_bundle.py y scripts/generate_attestation_bundle_v2.py.

Aplican Ring-0 (hashes/firmas/rutas/persistencia), Ring-1 (PoC y evidencia),
Ring-2 (Git/evidencia) y Ring-3 (CLI/documentación). No tocar dependencias ni
lockfiles, producir ATTESTED, leer claves reales, ejecutar hardware o publicar.
Generadores originales solo se ejecutan copiados a fixtures con HOME/PATH/root
propios y Git inerte; cualquier clave de software generada allí es temporal.

Aceptación: red/green por ID, importación sin efectos, resultados NOT_EXECUTED,
recalcular artefacto y metadata, firma ligada a cuerpo completo y clave externa,
rechazos de ausencia/caducidad/rutas/JSON inválidos y legacy no vinculante;
pytest relacionado, Ruff/MyPy, revisión independiente y controles documentales.
Preservar materiales históricos firmados. La copia histórica v2/verify y sus
C0135/C0136 OPEN quedan fuera de las tres fuentes. Lote 5 solo planificación.
Grafo no expuesto: búsqueda acotada de rutas/consumidores.
