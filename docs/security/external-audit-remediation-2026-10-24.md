# Contraste y corrección de la auditoría externa

Revisión: 24 de octubre de 2026, Europe/Madrid. Entrada: transcripción adjunta
de 2.728 líneas, con informes v1–v7. Encargo confirmado: contrastar y corregir
fallos reproducidos. No se adopta como evidencia ninguna afirmación del auditor
sin comprobar su fuente.

## Resultado y alcance

La auditoría identifica defectos reales de vinculación, presentación y
distribución, pero extiende algunos resultados más allá de su evidencia.
La corrección principal es rechazar un paquete rehasheado cuyo manifiesto de
release describe otros claims. También se corrige la presentación ES/EN de la
web: revisión por pares, alcance de Lean, certificación, SLA, acceso al código,
procedencia del árbol y CSP.

Rutas: `babylon60-verification/verify.py` y artefactos del espejo; componentes,
páginas, proyección de evidencia y cabeceras de `babylon60.com`. En este
repositorio se añade este informe y evidencia. Se preservan cambios anteriores
y concurrentes de kernel, licencia, empaquetado y validadores. No se cambian
dependencias ni lockfiles. Tras la autorización expresa del usuario para
publicar, se integra y publica el espejo; el despliegue web queda bloqueado
por el gate de atestación, como se detalla al final.

Aceptación: reproducción negativa, rechazo tras la corrección, paquete válido,
compilación Lean, construcción y controles web, navegación local y controles
documentales. La comprobación del runtime completo y la firma de una nueva
release quedan fuera de lo ejecutado. La atestación de publicación no certifica
el runtime ni firma los informes históricos de la release.

## Hallazgos contrastados

| Hallazgo | Contraste y tratamiento |
| --- | --- |
| RELEASE_MANIFEST no vinculado a CLAIMS | Confirmado en el espejo público `eb20966c61cb6214c3d80392bb8d504045d7f7c5`: digest `e34750…` frente a `79f326…`. El verificador corregido exige igualdad con CLAIMS y con los cinco contadores del sitrep. |
| Éxito antes de completar validaciones | Confirmado: imprimía INTEGRITY OK antes de comprobar el sitrep. Ahora se imprime tras validar hashes, vínculos y contadores. |
| No preservar el manifiesto anterior | El parche conserva los bytes previos en `reports/historical-release-manifest.json`. El sustituto procede del árbol local del motor, está ligado a la ejecución histórica existente y sigue sin firma. Su procedencia queda en `artifact_updates`. No se inventa una ejecución nueva. |
| Fecha de empaquetado confundida con fecha de prueba | El nuevo manifiesto fecha su generación; el timestamp histórico de claims permanece intacto. Se conserva el hash del manifiesto anterior. |
| Atestado de 16 bytes | Confirmado en el informe histórico del espejo: coincide con el prefijo del hash y no acredita una firma Ed25519. Se mantiene visible como limitación. Durante la tarea llegó una corrección del motor que separa `manifest_hash_prefix_16b` de `signature: null`; no es una nueva firma. |
| Release sin firma | Confirmado. No se genera una clave para simular identidad. La comprobación opcional sigue exigiendo una clave independiente. |
| 28 flags verified frente a 9 estados verified | Confirmado en el registro histórico. La proyección web distingue ahora estado verificado de suite ejecutada con éxito. Cambios previos/concurrentes del motor añaden `suite_passed`; sus pruebas dirigidas pasan. No se reescribió el sitrep histórico del espejo. |
| Verified(tx) distinto | La discrepancia del informe está confirmada; el árbol del motor ya tenía una corrección que alinea locator, pre-state hash y ledger precondition, con EffectObserved separado. Se preserva; no equivale a una prueba de runtime. |
| SIGKILL_SIMULATED y VERIFIED_IN_SILICON | Confirmado en documentos históricos diferentes. Siguen etiquetados como evidencia limitada y STALE; no se ejecuta ni se inventa una campaña de crash nueva. |
| 1.900 intentos frente a 1.000.000 | Es una distancia entre muestra registrada y objetivo, no una prueba de resistencia a escala. Continúa declarada. |
| Timestamps iguales implican fabricación | Inferencia no demostrada. No se puede concluir simulación de fsync ni intención a partir de igualdad de segundos o duración corta. |
| PEER-VERIFIED sin revisión identificada | Confirmado en Research ES/EN. Se reemplaza por investigación en curso y se añade un control de copy para evitar reintroducir la insignia. |
| Teorema universal por reflexión / en silicio | Confirmado. Se separan ejemplos rfl del teorema inductivo con propext y se conserva la premisa de traza válida desde Proposed. Se explicita que AX0 no modela nonces ni persistencia. |
| CERTIFIED y SLA garantizado | Confirmado en las páginas Enterprise locales y en la web consultada. Se sustituyen por evidencia experimental y condiciones por acordar. Precios conservados como propuestas; sin promesa de alta inmediata ni SLA activo. |
| local-first implica inferencia siempre local | Excesivo. La página corregida separa broker/ledger locales de contexto enviado a proveedores externos configurados. |
| CSP script-src none frente a unsafe-inline | Confirmado en la configuración. `_headers` pasa a script-src none; el navegador local recibe esa política y las rutas comprobadas no contienen scripts ejecutables. No se afirma que ya esté desplegada. |
| Ocultar dirty en la revisión | Corregido: el hero presenta SOURCE SNAPSHOT y +dirty; el footer muestra el SHA completo y el estado dirty del snapshot. |
| Repositorio necesariamente privado / no hay harness | La API actual de GitHub devuelve `private: false`. EDIN contiene orquestación LLM; la clasificación absoluta no se sostiene. La web ahora enlaza el código publicado y distingue revisiones. Véase también el informe previo enlazado abajo. |
| verify.sh ausente | Ya no se reproduce en el espejo público observado: contiene el wrapper ejecutable, y el ZIP distribuido supera extracción, verificación y Lean. |
| Wheel de julio con código clínico | Confirmado por inspección ZIP sin instalar ni ejecutar: PyPI 1.0.2, SHA-256 `44277399fe60ebe93779dc45510233e9787d5405eafcdd7e95378d1020b3b86f`, contiene apex_trials y una licencia CLOSED-CORE. No demuestra condición de producto sanitario ni que sea la versión local 5.0.1. |
| Licencias diferentes prueban incompatibilidad | Hay textos distintos y alcance confuso; no basta el nombre compartido para demostrar que las mismas obras/versiones tengan concesiones incompatibles. No se relicencia software por inferencia. La decisión jurídica y la distribución histórica siguen pendientes. |
| Falta de páginas legales prueba toda infracción alegada | No se adopta esa conclusión. Se prepara un borrador fuera del runtime; faltan titular fiscal, domicilio y prácticas reales de tratamiento que se han solicitado al usuario. |
| Edad del repo, estrellas o forks prueban calidad | No. La fecha de publicación no fecha el comienzo del desarrollo; estrellas, DOI y un HTTP 200/202 no prueban seguridad, revisión externa ni validez jurídica. |
| Rehashear todo puede producir INTEGRITY OK | Límite esperado de integridad sin ancla externa. Las regresiones exigen coherencia interna; no convierten hashes locales en identidad autenticada. |
| Debilitar un teorema a True compila | Lean comprueba el enunciado presentado. Se necesita control de revisión/enunciado y correspondencia con el runtime; no se presenta el mero build como tal vínculo. |

## Verificación de esta revisión

| Comprobación | Resultado |
| --- | --- |
| Regresiones antes de corregir el espejo | 7 fallos y 2 aciertos: seis corrupciones aceptadas y un mensaje de éxito prematuro |
| Mismas regresiones tras corregir | 9/9 pasan |
| Espejo candidato: ./verify.sh | 19 artefactos coherentes y Lean: Build completed successfully (3 jobs) |
| Pin externo de 64 ceros | Rechazado con salida 1 |
| Regresiones del espejo + ZIP web extraído | 11 tests pasan; incluye extracción, permisos del wrapper y Lean |
| Ruff del verificador y sus regresiones | Sin errores |
| Tests existentes de release/evidencia/distribución | 19 pasan, 1 omitido: instalación limpia opt-in con dependencias cacheadas; no se afirma haberlo ejecutado |
| npm run build | 111 archivos revisados, 0 errores/avisos; 48 páginas construidas |
| npm run verify | Gates de copy, enlaces, evidencia, recursos, AI Act y ensayos pasan; 42 tests Node pasan |
| Playwright local: Research ES y Enterprise EN | Insignias y premisas correctas, sin los textos retirados, sin desbordamiento horizontal en el viewport observado y sin scripts ejecutables |
| Semántica, presupuesto y topología locales | Los tres comandos exigidos pasan; [salidas completas](evidence/external-audit-remediation-2026-10-24/quality-gates.json). Se omiten configuración global y telemetría Ghost Listeners explícitamente. |

La CSP se comprueba en un servidor local que aplica la cabecera de `dist/_headers`.
Cloudflare aplica ese archivo a activos estáticos; las respuestas de Functions
requieren sus propias cabeceras. No se certifica la infraestructura pública ni
se audita el entorno de pagos por ejecutar sus tests ya configurados.

## Publicación y pendientes

El usuario autorizó publicar la web y el espejo, dejando la parte legal pendiente.
El espejo se publicó en `origin/main` mediante un merge explícito:
[`de1f87ca85c9363009c63e5f8cad8953478b5b7b`](https://github.com/borjamoskv/babylon60-verification/commit/de1f87ca85c9363009c63e5f8cad8953478b5b7b).
`git ls-remote` confirma esa revisión y el checkout queda limpio. Antes del push
se verificó la firma P-256 del recibo nativo vinculada al plan de publicación.
Se repitieron las nueve regresiones y `verify.sh`: 19 artefactos y Lean correctos.

Se respetó la migración concurrente que obtiene el ZIP web del repositorio
canónico: `npm run mirror:sync` importa esa revisión publicada y `npm run ci`
termina correctamente. Los dos tests del archivo distribuible también pasan.
El manifiesto preparado tiene SHA-256
`302b25aba7c7ced7abf7cd406c0808b8e2aba9f8c09ced52ea0e9d9c66a722e9`;
el ZIP, `cd69d61b9c5669c77049759357a3610112886dbecaa18c30dbfe93b165ecc2a5`.

Durante la preparación se detectó un intento concurrente del flujo canónico
`scripts/deploy.mjs` abortado con `legacyKeyRequiresMigration`, sin proyectos
publicados. Su gate rechaza el formato antiguo del registro de clave; el recibo
del binario instalado tampoco coincide con la clave pública fijada por ese
flujo. No se cambian las claves, no se reintenta el efecto y no se sustituye el
gate por una vía alternativa. El [contrato de atestación](../03_guides/agent_contracts.md#atestacion-biometrica)
exige abortar sin reintentos ni autenticación alternativa. Queda pendiente
resolver la migración y la identidad de firma del despliegue.

Comprobación con Playwright el 24 de octubre a las 01:50 UTC: la web responde
200 y ya muestra los cambios de copy de Research y Enterprise de un despliegue
concurrente anterior. Sin embargo, conserva la CSP con `script-src 'self'
'unsafe-inline'` y el manifiesto público anterior, SHA-256
`2840cf6c8bc1dc722480d67a69faa0bb779382c9fdf1be76b785dde77eb8229c`.
La publicación web no se da por completada. El proxy inspeccionado conserva las
cabeceras de Pages; no se le atribuye la causa de la CSP antigua sin comprobarla.
El borrador legal permanece fuera de `dist` y no se publica.

[Estado de publicación y pruebas](evidence/external-audit-remediation-2026-10-24/publication-status.json).

### Intento de migración autorizado posteriormente

El usuario autorizó expresamente migrar la clave y publicar la web. El gate
nativo creó un registro v2 separado, con permisos 0600, tras Touch ID; el proceso
terminó con salida 0. Sin embargo, la comprobación del llamante esperaba el
agente literal `MOSKV-1` y el gate lo identifica como `Codex · MOSKV-1`. El
llamante abortó antes de verificar la firma y no conservó el recibo completo.
Por ello no se activa ni se da por atestada la nueva clave. La clave activa,
la configuración de confianza y su copia privada anterior permanecen intactas;
no se repite la autenticación ni se intenta el despliegue en ese flujo.

Se corrige la integración de despliegue para incluir el agente completo en el
plan firmado, enviarlo al gate y exigir la misma identidad en el recibo. Una
regresión reproduce el fallo antes del cambio; las 11 pruebas dirigidas pasan
después. La previsualización nativa confirma el texto de origen sin solicitar
biometría. Se conserva el rechazo de claves extrañas, hashes distintos,
caducidad y replay. La parte legal continúa pendiente y fuera de la publicación.
[Estado de migración](evidence/external-audit-remediation-2026-10-24/key-migration-status.json).

Para una release autenticada faltan una revisión fijada y la ejecución pertinente,
la firma con identidad de confianza y la validación de hardware que corresponda.
Para los textos legales faltan datos del titular y del tratamiento. La wheel
histórica de PyPI no se ha reemplazado; la configuración local de exclusiones
recibida durante la tarea no certifica un nuevo artefacto publicado.
La documentación ES/EN advierte de esa diferencia y separa el snapshot local de
la web de la revisión que contiene el ZIP descargable.

## Fuentes

- [Revisión local previa del harness](harness-audit-2026-10-24.md).
- [Espejo público observado](https://github.com/borjamoskv/babylon60-verification/tree/eb20966c61cb6214c3d80392bb8d504045d7f7c5).
- [Research público](https://babylon60.com/research/) y [Enterprise EN](https://babylon60.com/en/enterprise/), consultados en esta tarea; la versión pública puede diferir del parche local.
- [API del repositorio](https://api.github.com/repos/borjamoskv/BABYLON-60) y [metadatos de PyPI](https://pypi.org/pypi/babylon60/json).
- [Cloudflare: cabeceras](https://developers.cloudflare.com/pages/configuration/headers/), consultadas mediante Context7.
- [RFC 9052](https://www.rfc-editor.org/rfc/rfc9052.html) y [RFC 9942](https://www.rfc-editor.org/rfc/rfc9942.html): ambas referencias existen; COSE_Sign1 y recibos de estructuras verificables no son términos intercambiables.

Las comprobaciones de esta tabla no son una auditoría independiente completa del
kernel ni una acreditación de conformidad legal.
