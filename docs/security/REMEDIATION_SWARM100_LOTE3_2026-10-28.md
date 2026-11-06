# Lote 3: autorización y despacho Git — 28/10/2026

Resultado: C0413 y C0418 corregidos en sus dos scripts; SW100-R3-0001 corregido
como hallazgo adicional fuera del inventario original. C0414 conserva su
rechazo: el preview permite preparación local. La
[validación reproducible](evidence/swarm100-lot3-20261028/validation.json)
y la [revisión independiente](evidence/swarm100-lot3-20261028/independent-review.json)
delimitan la evidencia; ninguna afirma una publicación real o atestación hardware.

## Reproducción y corrección

Los [tres casos previos](evidence/swarm100-lot3-20261028/before-tests.log)
fallaron contra los [hashes originales](evidence/swarm100-lot3-20261028/before-source-manifest.json).
En repositorios de fixture, el original alcanzó el publicador sin Gitleaks,
alcanzó el publicador sin gate y seleccionó C2 al cambiar la rama durante la
espera de A. Git, escáner y gate eran ejecutables de prueba sin red ni efectos
sobre el checkout del operador; no emitieron ATTESTED.

| ID | Cambio ejecutable | Evidencia de aceptación |
| --- | --- | --- |
| C0413 | Escáner obligatorio; cualquier error aborta. Materialización de blobs del árbol inmutable, política e ignores dentro del snapshot. | Ausencia/error del escáner; archivo export-ignored presente; symlink tratado como blob; objetos/rutas/políticas no soportados rechazados. |
| SW100-R3-0001 | Fuente de push es el commit guardado. Hash SHA-256 liga árbol/commit, destino, ref completa, force, acción/ámbito/agente, configuración de transporte y nonce nuevo. | Reproducción de A/B, segunda invocación real de preview en fixture, warmup y cuatro intentos solapados, despacho inocuo que conserva C1 ante cambios de rama/configuración. |
| C0418 | Preflight sin proveedor aborta antes de mutaciones; una sola invocación exige recibo fresco, acotado y verificable. | Vacío, malformado, estado inválido, cancelación, exceso de salida, plazo, hashes/campos/operador distintos y replay rechazados; sin fallback tras fallo. |

La revisión identificó y resolvió sustituciones por `refs/replace`, omisión de
hooks/LFS y un hijo huérfano del gate que retenía stdout. Las lecturas usan
`GIT_NO_REPLACE_OBJECTS`; el plazo mata el grupo completo. El snapshot mide
un tar PAX serializado con presupuesto estricto inferior a 20 MiB; el caso en
que los blobs caben pero el padding excede el límite también se rechaza.

El dispatcher usa un bare privado con almacén de objetos preseleccionado y
solo la configuración de transporte capturada. No hereda remotes, reglas URL,
hooks ni configuración Git global mutable. La observación de `ls-remote`
comprueba el commit/ref después del despacho y comunica desacuerdo sin reintento.
El preview informa Authorization/push NOT_CHECKED. El modo status de ship
permanece de solo lectura. La revisión adicional de retención reprodujo y
corrigió una limpieza que borraba un temporal ajeno tras una colisión; el
rechazo conserva ahora ese archivo y el recibo previo.

## Verificación y límites

**391 pruebas aprobadas y 1 omitida en la suite relacionada**, más cuatro
pruebas finales de retención (dos ya incluidas y dos nuevas): **393 casos
distintos verificados**, incluidas las **71 regresiones nuevas**.
La omitida requiere strike_rs compilado, fuera de este lote. Las suites se
ejecutaron con lockfile; comandos y logs constan en validation.json. La
revisión independiente añadió catorce controles aprobados: diez del flujo
y cuatro de almacenamiento. La última corrección solo afecta a limpieza de
retención y se verificó con sus cuatro casos dirigidos; el resto conserva
la implementación ya revisada. El dictamen conserva hashes de cada fase. Se ejecutan
bash -n, ShellCheck, Ruff y MyPy del helper Python extraído, con paridad de
ambas copias comprobada. Las pruebas de firma usan únicamente claves de
software y campos criptográficos aislados; nunca generan ATTESTED.

- El gate local seleccionado sigue siendo el componente de confianza. Comprobar
  una firma con la clave del recibo demuestra consistencia, no procedencia
  hardware independiente. Secure Enclave, usuario físico y push real siguen
  NO_VERIFICADOS.
- Hooks pre-push ejecutables, submódulos y punteros LFS (incluidas cabeceras
  heredadas) se rechazan expresamente. Este flujo no los omite ni implementa
  su transferencia; repositorios que los usan necesitan un contrato adicional.
- Ship conserva el recibo validado con su descriptor del efecto en
  `.babylon60/last_ship_receipt.json`: archivo 0600, apertura por descriptor,
  escritura temporal exclusiva, fsync y reemplazo atómico. No sigue symlinks ni
  elimina temporales que no creó. El recibo anterior nunca autoriza otro intento.
  La proyección pública mantiene su recibo temporal, como antes. Las pruebas de
  almacenamiento usan JSON inocuo sin ATTESTED y no prueban una aprobación.
- No se certifica ausencia absoluta de secretos ni aislamiento frente a procesos
  hostiles del mismo usuario, cambios de binarios/SSH, DNS o transporte externo.
  La revisión no ejecutó escaneo real del monorrepo ni hooks del operador.
- Sin cambios de dependencias/lockfiles, commits, merges, Swift, autenticación,
  despliegue ni publicación reales. Configuración y telemetría global omitidas.

El inventario original conserva sus 598 IDs: 560 OPEN, 30 FIXED,
4 MITIGATED y 4 NOT_APPLICABLE. Entre los 582 pendientes iniciales: 555 OPEN,
20 FIXED, 3 MITIGATED y 4 NOT_APPLICABLE. Quedan **554 hallazgos únicos OPEN**
(70 P1, 474 P2, 10 P3); SW100-R3-0001 se contabiliza aparte y está FIXED.

El [Lote 4 propuesto](PLAN_SWARM100_LOTE4_2026-10-28.md) agrupa C0061, C0083,
C0086 y C0087 en tres fuentes de bundles. Conserva sus hashes y no se aplica.

## Fuentes del contrato de herramientas

Se consultaron con Context7 las fuentes primarias de
[Gitleaks](https://github.com/gitleaks/gitleaks/blob/v8.30.1/README.md),
[Git remote](https://github.com/git/git/blob/master/Documentation/git-remote.adoc),
[Git archive](https://github.com/git/git/blob/master/Documentation/git-archive.adoc),
[rutas de hooks](https://github.com/git/git/blob/master/path.c) y
[punteros LFS](https://github.com/git-lfs/git-lfs/blob/main/lfs/pointer.go).
No había herramientas codebase-memory expuestas; se usaron búsquedas acotadas.
