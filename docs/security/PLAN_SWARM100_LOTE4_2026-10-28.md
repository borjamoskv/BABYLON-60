# Lote 4 ejecutado: integridad de bundles y resultados — 28/10/2026

Estado: ejecutado bajo autorización posterior del operador; véase el
[informe de corrección](REMEDIATION_SWARM100_LOTE4_2026-10-28.md). La selección
inicial agrupó P1 CONFIRMED_STATIC/OPEN por afinidad. No quedan P1 OPEN con reproducción previa.
Los [hashes y observaciones de selección](evidence/swarm100-lot3-20261028/lot4-selection.json)
fijaron las tres fuentes antes de editar; la ejecución conservó ese límite.

| ID | Fuente prevista | Resultado exigido |
| --- | --- | --- |
| C0061 | `proof/bundles/attestation_bundle_v1/verify` | No afirmar integridad de metadata o artefactos sin recalcular sus bytes y comprobar el vínculo con la firma. |
| C0083 | `scripts/generate_attestation_bundle.py` | Sustituir PASS constantes y material firmado reutilizado por evidencia real identificada o NOT_EXECUTED/UNVERIFIED. |
| C0086 | `scripts/generate_attestation_bundle_v2.py` | Prohibir resultados de suites inventados en el digest conjunto; exigir procedencia de ejecuciones comprobables. |
| C0087 | Mismo generador v2 | El verificador generado debe calcular el digest del artefacto suministrado y rechazar ausencias o cambios. |

Antes del parche, reproducir en copias temporales: alterar claims/tests/environment
sin modificar la firma, cambiar el artefacto dejando el bundle intacto y generar
sin ejecutar suites. La observación será la salida/exit code del verificador y
el contenido exacto de los campos, sin aceptar una etiqueta como prueba.
No importar generadores con efectos de nivel superior sobre rutas reales.

Diseño: separar recolección de evidencia, serialización canónica y validación.
Una ejecución ausente o sin procedencia no puede producir PASS. La compatibilidad
con firmas heredadas deberá dar un resultado limitado explícito, o rechazo;
no se reinterpretan las firmas antiguas como una certificación nueva. Conservar
los materiales históricos firmados sin regenerarlos ni sobrescribirlos.

Aceptación: red/green por ID, mutaciones de cada campo/artefacto, rutas ausentes,
resultados caducados y estado NOT_EXECUTED; suites existentes pertinentes, Ruff,
MyPy de Python afectado, revisión independiente y registro reconciliado. Usar
solo claves de software de fixture para comprobar matemáticas, sin fabricar
ATTESTED ni dar por satisfecho hardware, identidad de confianza o despliegues.

La ejecución posterior se limitó a las tres fuentes y a fixtures temporales,
sin generar ni sobrescribir materiales firmados históricos. El soporte de hooks/LFS y la consolidación C0460 requieren
sus propios contratos y permanecen fuera de este lote propuesto.
