# Contrato — Lote 7 (29/10/2026, Europe/Madrid)

C0556/C0557: única fuente productiva editable scripts/c5_verifiers/fast_smt_gate.py.
Reproducir primero en copia temporal; conservar cambios ajenos y materiales
históricos. Tests/evidencia/registro y plan Lote 8 permitidos; Lote 8 no aplicado.

Ring-0 (frontera de atestación/digest), Ring-1 (falsación de afirmaciones),
Ring-2 (gate/consumidor/Git) y Ring-3 (JSON/CLI/documentos). Ningún PASS sin
checker soportado, inventario completo, estados explícitos sin bool legacy.
Observaciones de rutas separadas de invariantes; UNKNOWN/NOT_EXECUTED/FAIL
impiden éxito en todos los modos y con/sin --strict.

Exportación versionada UNSIGNED, sin pseudo-Ed25519/SCITT/legal/hardware;
BLAKE3 de contenido/configuración completos con dominio y JSON canónico.
Sin checkers implementados no se certifican las 25 invariantes. Preservar
nombre API/flag --scitt solo como alias legado con contrato nuevo explícito.

Fixtures con HOME/cwd/root propios. No ejecutar mantenimiento completo,
solvers/procesos nativos protegidos, red, claves/ledgers del operador, hardware,
publicación o ATTESTED. Consumidor por inspección y doble de subprocess.
Grafo no expuesto: exploración acotada. Pruebas, Ruff/MyPy, revisión
independiente, reconciliación y controles documentales antes de cerrar.
