# Auditoría BABYLON-60 — continuación validada — 28/10/2026

Esta ronda añade reproducciones a la [auditoría de 100 agentes](AUDIT_SWARM100_2026-10-28.md). Los cuatro coordinadores existentes validaron casos acotados y el coordinador principal repitió los cuatro arneses con fixtures nuevas. Se conservaron intactos el informe y el paquete de evidencia de la primera ronda.

**Resultado:** 13 escenarios corroborados, agrupados en 11 familias de hallazgos. Además se confirmaron 5 pares de candidatos duplicados. Las 59 pruebas existentes seleccionadas pasaron; esos resultados no cubren los contraejemplos que siguen.

## Hallazgos reproducidos

|ID|Candidato original|Prioridad adjudicada|Resultado observado|
|---|---|---|---|
|V01|SW100-C0071|P1|[Observaciones NEMESIS emitidas sin ejecutar campañas — línea 599](../../01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py)|
|V02|SW100-C0072|P1|[Salida existente eliminada antes de validar entradas — línea 585](../../01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py)|
|V03|SW100-C0172|P1|[CRL malformada deja pasar certificado revocado — línea 78](../../01_KISH_ENGINE/babylon60/verifier/cli.py)|
|V04|SW100-C0177|P1|[Payload del ledger JSON alterado mantiene el resultado válido — línea 450](../../01_KISH_ENGINE/babylon60/verifier/standalone_verify.py)|
|V05|SW100-C0184|P1|[Revocación intercalada permite hijo activo de padre revocado — línea 468](../../01_KISH_ENGINE/babylon60/memory/governance.py)|
|V06|SW100-C0291|P1|[Cristal con contenido alterado conserva INTEGRITY_VERIFIED — línea 239](../../01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py)|
|V07|SW100-C0303|P2|[Conclusión ajena recibe FormalProof y estado CANONICAL — línea 146](../../01_KISH_ENGINE/babylon60/autodidact/epistemology.py)|
|V08|SW100-C0364|P1|[El marcado de shredding conserva la capacidad de descifrar — línea 353](../../01_KISH_ENGINE/babylon60/crypto/shredder.py)|
|V09|SW100-C0483|P1|[Ledger divergente con igual nombre se elimina — línea 70](../../scripts/c5_cortex/consolidate_dbs.py)|
|V10|SW100-C0484|P1|[La copia de SQLite pierde filas confirmadas solo en WAL — línea 32](../../scripts/c5_cortex/consolidate_dbs.py)|
|V11|SW100-C0539|P1|[El purge de extensión acepta rutas fuera de Extensions — línea 171](../../tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py)|

### V01 · Observaciones NEMESIS emitidas sin ejecutar campañas

El compilador genera cuatro campañas SUPPORTED_WITHIN_SCOPE sin campañas ejecutadas; firma software y checksums válidos sobre los bytes emitidos.

**Alcance:** Una firma correcta acredita bytes y clave; no acredita que las observaciones ocurrieran.

**Evidencia original:** [a/result.json](evidence/swarm100-round2-20261028/a/result.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V02 · Salida existente eliminada antes de validar entradas

Con CLAIMS inexistente y, por separado, ledger inexistente, compile_pack falla después de borrar el archivo testigo previo.

**Alcance:** Dos variantes del mismo defecto. Solo directorios desechables bajo el argumento output_dir.

**Evidencia original:** [a/result.json](evidence/swarm100-round2-20261028/a/result.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V03 · CRL malformada deja pasar certificado revocado

La lista válida rechaza el certificado de fixture; con JSON malformado en la misma ruta, el parser lo convierte en un literal de ID y el certificado pasa.

**Alcance:** Certificado de prueba firmado con Ed25519 software; sin alegación de falsificación ni autoridad de un emisor productivo.

**Evidencia original:** [b/results.json](evidence/swarm100-round2-20261028/b/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V04 · Payload del ledger JSON alterado mantiene el resultado válido

Cambiar amount de 10 a 999999 conservando entry_hash y raíz firmada mantiene valid=True; cambiar el hash sí se rechaza.

**Alcance:** Se acredita integridad insuficiente de los campos del evento; una lista que solo declara hashes puede tener otro contrato. No se rompió la función hash ni la firma.

**Evidencia original:** [b/results.json](evidence/swarm100-round2-20261028/b/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V05 · Revocación intercalada permite hijo activo de padre revocado

Dos instancias SQLite: A valida el padre; se ejecuta la revocación B en el punto de append; A reanuda y persiste hijo ACTIVE con padre REVOKED. Añadir tras una revocación ya terminada se rechaza.

**Alcance:** Intercalado determinista mediante hook de planificación; lógica real de validación y persistencia. No es estrés multihilo ni bypass de autenticación.

**Evidencia original:** [b/results.json](evidence/swarm100-round2-20261028/b/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V06 · Cristal con contenido alterado conserva INTEGRITY_VERIFIED

El cristal generado originalmente se modifica para afirmar cinco lados en un triángulo, conservando statement_hash; verify_crystal_integrity lo acepta. Cambiar el hash sí falla.

**Alcance:** Se ejecutó la API; la CLI y consumidores externos se trazaron antes pero no se ejecutaron en esta reproducción.

**Evidencia original:** [c/results.json](evidence/swarm100-round2-20261028/c/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V07 · Conclusión ajena recibe FormalProof y estado CANONICAL

Una premisa sobre triángulos de tres lados permite un objetivo contradictorio de cinco lados: FormalProof, confianza 1.0, CANONICAL y verify=True. El control de modalidad deóntica sí rechaza.

**Alcance:** Se rebaja la prioridad sugerida P1 a P2 en esta ronda: defecto real de comprobación/etiquetado del modelo, sin efecto externo autorizado demostrado.

**Evidencia original:** [c/results.json](evidence/swarm100-round2-20261028/c/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V08 · El marcado de shredding conserva la capacidad de descifrar

shred_fact devuelve éxito y deja marcas persistente/en memoria; el mismo ciphertext se descifra con la instancia existente y otra instancia creada con la misma clave sintética.

**Alcance:** Contradice la destrucción criptográfica anunciada en esta API; no evalúa borrado físico ni filtros de consulta de la aplicación.

**Evidencia original:** [c/results.json](evidence/swarm100-round2-20261028/c/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V09 · Ledger divergente con igual nombre se elimina

Origen y destino tienen filas distintas. Después de consolidate_dbs el origen desaparece y el destino conserva solo su fila anterior.

**Alcance:** Invocación local explícita, globals REPO_ROOT/CENTRAL_DIR redirigidas a directorios temporales.

**Evidencia original:** [d/results.json](evidence/swarm100-round2-20261028/d/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V10 · La copia de SQLite pierde filas confirmadas solo en WAL

Una fila confirmada está en WAL. La copia central queda vacía y el WAL de origen se elimina.

**Alcance:** Conexión de fixture abierta y autocheckpoint desactivado; testigo SQL real. No se tocó un ledger del operador.

**Evidencia original:** [d/results.json](evidence/swarm100-round2-20261028/d/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


### V11 · El purge de extensión acepta rutas fuera de Extensions

Con ../victim y con una ruta absoluta se elimina un directorio testigo fuera de Extensions, manteniendo el perfil falso.

**Alcance:** Dos variantes del mismo defecto; callbacks y funciones reales, base de Chrome redirigida y guardas de borrado limitadas a fixtures.

**Evidencia original:** [d/results.json](evidence/swarm100-round2-20261028/d/results.json). **Repetición independiente:** [resumen de replay](evidence/swarm100-round2-20261028/root-replay/replay-summary.json). La fuente y su SHA-256 constan en [findings.json](evidence/swarm100-round2-20261028/findings.json).


## Comprobaciones y límites

- 59 pruebas existentes pasaron en verificador standalone, gobernanza de memoria y exportación de certificados: [salida completa](evidence/swarm100-round2-20261028/existing-tests.log).
- Los cuatro arneses terminaron con código 0 y corroboraron los 13 escenarios esperados; el cero significa que se observaron los fallos previstos, no que el producto los haya corregido.
- Se incluyeron controles negativos: CRL válida, hash alterado, derivación tras revocación terminada y restricción de modalidad. Las variantes esperadas se rechazaron.
- Las firmas usadas son software de fixture y no atestación hardware. Las guardas Python y los directorios redirigidos son mecanismos de prueba, no aislamiento del sistema operativo.
- La carrera de gobernanza usa una intercepción determinista de planificación, sin reemplazar validación ni persistencia. Los módulos de algunas fixtures se importan sin inicializadores amplios; las funciones evaluadas conservan su fuente original.
- El problema SIMD conserva corroboración estática/matemática; no se cargó ni explotó una biblioteca nativa. No se infiere un bypass de ejecución del MCP a partir de propuestas.
- No se modificó código productivo ni se desplegó. Los hashes se volvieron a contrastar con el inventario original antes de entregar.

Los cinco scripts de reproducción entregados pasaron Ruff. Se conservaron los bytes ejecutados originalmente como `*.executed-source.txt`; los scripts `.py` se formatearon y volvieron a ejecutar en fixtures nuevas, con el resultado de los 13 escenarios conservado. El import tardío de criptografía tiene una supresión E402 localizada para ejecutarlo bajo la guarda de auditoría de la fixture. [Ruff final](evidence/swarm100-round2-20261028/repro-ruff-final.log).

## Repetición

Desde la raíz del repositorio, con las dependencias ya disponibles, este comando genera una carpeta temporal nueva y devuelve su ruta:

```sh
uv run --locked python docs/security/evidence/swarm100-round2-20261028/replay_all.py
```

El runner solo ajusta las rutas del repositorio y de las fixtures. Conserva en la salida los scripts renderizados, sus hashes, los resultados y stdout/stderr. Los scripts del paquete se revisaron para evitar perfiles, claves o bases del operador; siguen siendo código de prueba que ejecuta funciones del repositorio y no un sandbox. Las bases temporales y el pack sintético no se añaden a las fuentes del proyecto.

## Depuración del registro

Se contrastaron cinco pares con fuente completa idéntica, misma línea y disparador/impacto equivalentes. Se conserva un candidato canónico y las dos rutas afectadas en [duplicate-adjudications.json](evidence/swarm100-round2-20261028/duplicate-adjudications.json). Los 593 grupos provisionales restantes no representan 593 defectos únicos confirmados: pueden quedar más duplicados o hipótesis por descartar.

La actualización de estado cubre 11 candidatos reproducidos y cinco duplicados. Los otros 582 registros no reciben un estado final en esta ronda. Esto no invalida los dictámenes estáticos previos; delimita qué se ha vuelto a verificar mediante reproducción o deduplicación. [Actualizaciones por ID](evidence/swarm100-round2-20261028/candidate-status-updates.json).

La prioridad de V07 se rebaja de P1 a P2 porque la reproducción demuestra un error de comprobación/etiquetado en el modelo y no establece un efecto externo autorizado. Los datos originales se conservan para trazar esa corrección.
