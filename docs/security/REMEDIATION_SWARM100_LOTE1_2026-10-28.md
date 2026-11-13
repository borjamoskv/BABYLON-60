# Lote 1: ejecución de C0373, C0501 y C0420 — 28/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

## Contrato previo a las ediciones

Ejecutar el [plan aprobado](PLAN_SWARM100_LOTE1_2026-10-28.md) únicamente en
sus cuatro archivos productivos: transductor de correo, motor Tamkarum y las
dos copias SOCINT. Añadir regresiones antes del parche y conservar sus fallos
contra los hashes de selección. Actualizar pruebas, evidencia, registro e
informe; preparar el Lote 2 sin editar otros módulos productivos.

Aceptación: ninguna credencial/argv en errores de correo; sello SOCINT v2
ligado recursivamente a nombres, tipos y valores del cuerpo final; verificación
Tamkarum con firma Ed25519 del cuerpo completo, clave pública externa y
evidencias actuales, con rechazo de ausencia/cambio/esquema inválido y salida
CLI no cero. C0264 y C0421 se comprueban como superficies relacionadas.

Pruebas con tokens sintéticos, claves efímeras y archivos temporales. Sin
correo, redes, campañas del operador, firma hardware, cambios de dependencias,
commits o despliegues. Aplican los [contratos de evidencia y hashes](../03_guides/agent_contracts.md).
El grafo MCP no está expuesto; se usan rutas y consumidores delimitados.

Ruff inicial detecta deuda previa en los mismos cuatro archivos. Se conservará
el diagnóstico y se limitará su saneamiento a cambios mecánicos sin efectos.
Las dos copias SOCINT se comprobarán por separado en MyPy para evitar su
colisión de nombre de módulo.

## Resultado

**C0373, C0501 y C0420 quedan FIXED**, junto a C0421 (P2). C0264 se reconcilia
como copia duplicada de C0501, también FIXED. Se modificaron únicamente los
cuatro archivos productivos del plan.

| ID | Cambio comprobado |
| --- | --- |
| C0373 | Los errores devuelven códigos y mensajes estáticos; descartan argv, stderr, excepciones y cuerpos de error del proveedor. Los IDs de éxito redactan la credencial si aparece. |
| C0501 / C0264 | Sello `socint-fields-v2` con nombres y tipos JSON recursivos, separación de dominios y rechazo de valores no finitos/no admitidos. El productor sella después de completar los campos de análisis y publica cobertura exacta. |
| C0420 | `tamkarum-evidence/v2` verifica firma Ed25519 del cuerpo completo con clave pública externa, recalcula tres archivos actuales y contrasta commit, topología canónica y raíz declarada del manifest. |
| C0421 | La CLI sale con 1 ante rechazo, 0 ante una fixture válida y 2 ante modo ausente u opciones incompatibles. No hay emisión por omisión. |

El emisor Tamkarum produce un manifiesto **UNSIGNED**, sin inventar auditorías,
cumplimiento o atestación hardware. La autenticación requiere que un firmante
autorizado externo aporte la firma del esquema documentado. Una fixture firmada
con clave efímera autorizada verifica en la API y en la CLI real: la corrección
no consiste en rechazar siempre.

## Verificación

- Fuentes originales (material no distribuido: `evidence/swarm100-lot1-20261028/before-source-manifest.json`):
  los cuatro hashes coincidían con la selección antes de editar.
- Primera ejecución (material no distribuido: `evidence/swarm100-lot1-20261028/before-tests.log`):
  **48 failed, 3 passed**, 51 casos sobre los hashes originales. Incluye los
  tres escenarios de los arneses aislados convertidos a regresiones.
- Batería final relacionada (material no distribuido: `evidence/swarm100-lot1-20261028/related-tests.log`):
  **242 passed, 1 skipped**, trece archivos: la batería anterior, AgentPager y
  62 regresiones de este lote. La omisión requiere `strike_rs`, no construido.
  El alcance es la batería Python relacionada; no toda la suite del repositorio.
- CLI real con fixtures (material no distribuido: `evidence/swarm100-lot1-20261028/cli-smoke.json`):
  cinco controles de salida pasan, incluida firma autorizada positiva y
  rechazo tras cambiar un archivo, sin clave, sin modo o con flags incompatibles.
- Revisión independiente (material no distribuido: `evidence/swarm100-lot1-20261028/independent-review.json`):
  62 pruebas, hashes y cobertura revisados; ningún hallazgo accionable pendiente
  dentro del alcance. Detectó que `--emit` ignoraba flags de verificación.
  Cinco regresiones fallaron (material no distribuido: `evidence/swarm100-lot1-20261028/emit-controls-before.log`)
  antes del ajuste; ahora esos flags se rechazan antes de llamar al emisor.
- Ruff (material no distribuido: `evidence/swarm100-lot1-20261028/ruff.log`) y MyPy sobre las cuatro fuentes:
  aprobados. Cada copia SOCINT se comprueba por separado por su nombre de módulo.
  La deuda inicial de Ruff está conservada; quitar prefijos f innecesarios y
  renombrar una variable ambigua no alteró el AST funcional ajeno al parche,
  según la revisión independiente.
- Validación final (material no distribuido: `evidence/swarm100-lot1-20261028/validation.json`): comandos,
  códigos de salida, hashes, enlaces, controles documentales y contabilidad.

Se refrescó la evidencia de C0265, C0268, C0269 y C0270 porque comparten un
archivo modificado; siguen OPEN. El cambio de hash no se utiliza para cerrarlos.

## Límites y compatibilidad

Los errores de correo conservan estado/código, pero ya no exponen diagnósticos
arbitrarios del proveedor. Las pruebas sustituyen únicamente el transporte y
usan tokens sintéticos; no hubo envío ni consulta de Keychain.

SOCINT v2 cambia la raíz respecto al esquema heredado. El informe distingue
legacy sin verificación v2; no migra silenciosamente sellos anteriores. El
cuerpo final queda comprometido salvo el objeto `merkle_seal`; su timestamp
es metadato declarado fuera del hash. Un Merkle root no acredita autoría.

Tamkarum usa JSON y Ed25519 bajo un dominio propio, no COSE/SCITT registrado.
La clave autorizada y las referencias de archivos provienen del llamante,
nunca del documento. Sin firma/ancla válidas se rechaza. Los digests describen
los bytes efectivamente leídos; no prueban verdad de claims, validez legal,
revocación de claves ni snapshot atómico entre archivos. Las expectativas
offline de commit/topología, cuando se proporcionan, son entradas de confianza
externas; por defecto se consulta el estado local actual.

## Inventario y siguiente lote

Quedan **562 hallazgos únicos OPEN** originales: 77 P1, 475 P2 y 10 P3;
tres mitigados y el P1 adicional SW100-R3-0001 siguen pendientes. La reducción
desde 567 combina cuatro correcciones directas y la deduplicación de C0264.
En los 582 IDs de la ronda quedan 564 OPEN, 12 FIXED, 2 MITIGATED y
4 NOT_APPLICABLE. Los cambios por ID (material no distribuido: `evidence/swarm100-lot1-20261028/candidate-status-updates.json`)
y el registro reconciliado conservan historia y hash vigente.

El [Lote 2](PLAN_SWARM100_LOTE2_2026-10-28.md) contiene cinco P1 estáticos sobre
consolidación, WAL y sesiones globales, más una copia duplicada. Sus cinco
archivos productivos siguen intactos; se presenta solo el plan.

Sin dependencias nuevas, cambios de lockfiles, commit, push ni despliegue.
Controles documentales limitados al workspace, con telemetría de ghost listeners
y configuración global omitidas. Ninguna campaña o sesión real fue leída.
