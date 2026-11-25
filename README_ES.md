[![BABYLON-60 — Recupera tu contexto. Controla tus agentes.](assets/brand/github-art-brut.png)](https://babylon60.com/)

# BABYLON-60

[English](README.md) · **Español**

**Más inteligencia. La misma autoridad.**

BABYLON-60 ofrece controles locales para agentes de IA: confinamiento de sus
procesos por el sistema operativo y autorización firmada para determinadas
herramientas MCP. El modelo propone una acción; la política configurada y el
operador determinan sus permisos.

[![Python Tests](https://github.com/borjamoskv/BABYLON-60/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/borjamoskv/BABYLON-60/actions/workflows/python-tests.yml)
[![Verify Claims](https://github.com/borjamoskv/BABYLON-60/actions/workflows/verify_claims.yml/badge.svg?branch=main)](https://github.com/borjamoskv/BABYLON-60/actions/workflows/verify_claims.yml)
[![Licencia](https://img.shields.io/badge/license-Sovereign_Dual--License_·_not_OSI--approved-F3F52B?style=flat-square&labelColor=171717)](LICENSE)

> [!IMPORTANT]
> **Alpha de seguridad.** El confinamiento y el broker se configuran por separado.
> `babylon60 run` no activa el broker; instalar una integración no confina al
> cliente. Ningún comando de esta página combina ambas capas.
> Las garantías se limitan al [alcance y la evidencia declarados](#qué-está-verificado).

[Probar](#probar-en-5-minutos) · [Con tu agente](#con-tu-agente) ·
[Instalar / integrar](#instalación) · [Límites](#lo-que-run-no-impide) ·
[Verificar](#qué-está-verificado) · [Referencia](#documentación) ·
[Preguntas frecuentes](#preguntas-frecuentes-para-humanos)

## Qué funciona hoy

| Capacidad | macOS | Linux x86_64 | Windows |
| :--- | :--- | :--- | :--- |
| Confinamiento de procesos (`run`, `demo`) | Seatbelt | Landlock ABI 3+ y seccomp | Sin backend |
| CLI y registro de eventos MCP | Sí | Sí | Probados en Python 3.11 / 3.12 |
| Broker de efectos MCP (alpha) | Requiere biblioteca nativa y Touch ID | Sin helper de aprobación | No |

`run` restringe el acceso a archivos y deja la red abierta. El servidor MCP
almacena eventos SQLite con procedencia declarada por quien llama; eso no
valida que un evento sea una fuente original o una inferencia correcta.

## Probar en 5 minutos

**Requisitos:** `git`, Python 3.11+, [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
y macOS con `/usr/bin/sandbox-exec`, o Linux x86_64 con Landlock ABI 3+
activado (kernel 6.2+). Linux aarch64 está `NO_VERIFICADO`. En Windows sigue
[Instalación](#instalación); la demo de confinamiento no está disponible.

Clona una vez y elige la demo o la integración de cliente de las siguientes secciones:

```bash
git clone --depth 1 https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60
bash install.sh --demo
```

El instalador crea la CLI en `.venv` dentro del clon; no la añade al PATH.
La demo utiliza un script atacante en Python, **no un LLM**, que sigue una
instrucción maliciosa de un README contra una clave señuelo en un HOME
desechable. Nunca toca tu `~/.ssh` real.

Busca `verdict: BLOCKED` y código de salida 0. Exige que funcionen los controles
positivos y se bloqueen todos los ataques contabilizados. La salida 1 significa
`FALSIFIED`, 2 significa `INCONCLUSIVE` y 3 indica que no hay backend de
confinamiento. Los totales cambian según plataforma y revisión; las cifras
históricas están en la [referencia de la demo](docs/03_guides/README_REFERENCE_ES.md#demo-método-y-ejecuciones-registradas).

## Con tu agente

Tras instalar, ejecuta desde **la carpeta de tu proyecto**, sustituyendo
`~/BABYLON-60` por la ruta del clon:

```bash
cd ~/tu-proyecto
~/BABYLON-60/.venv/bin/babylon60 run --preset codex -- codex
# O bien:
~/BABYLON-60/.venv/bin/babylon60 run --preset claude-code -- claude
```

Se puede escribir en el workspace, la carpeta temporal privada y las rutas
que el preset habilite para escritura; Linux también permite `/dev/shm`.
Los demás archivos personales se retienen salvo permiso explícito.
Estas acciones no requieren firma del broker.

- `--dry-run` muestra la política; `run --help` enumera todas las opciones.
- Los presets conservan las credenciales de su agente. `--pass-env NOMBRE`
  permite pasar explícitamente otras variables con nombre de credencial.
- `run` rechaza como workspace el clon de Babylon, tu HOME o sus antecesores
  y directorios compartidos con sticky bit, como `/tmp`. También rechaza
  permisos que abarquen rutas de credenciales protegidas.
- Las comprobaciones de clientes registradas cubren `claude --version` y
  `codex --version` confinados en Linux x86_64. Las sesiones completas con
  un LLM siguen `NO_VERIFICADO`.

[Permisos, opciones y compatibilidad](docs/03_guides/README_REFERENCE_ES.md#con-tu-agente).

## Instalación

Usa el checkout fuente, no `pip install babylon60`: el nombre en PyPI pertenece
a una versión 1.0.2 antigua con otro contenido. El instalador requiere `uv`,
Python 3.11+ y un checkout limpio. Instala la CLI de terminal y el servidor MCP,
sin abrir una aplicación de escritorio.

**macOS / Linux:** si no ejecutaste la demo, ejecuta primero `bash install.sh`
desde el clon. Después puedes configurar un cliente:

```bash
.venv/bin/babylon60 setup --client codex --dry-run
.venv/bin/babylon60 setup --client codex
.venv/bin/babylon60 doctor --client codex
```

**Windows (PowerShell):** instala desde un clon limpio o el ZIP fuente.
Windows admite la CLI y el servidor MCP, pero no el confinamiento de procesos:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun -Client codex
pwsh -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Client codex
.\.venv\Scripts\babylon60.exe doctor --client codex
```

Si no tienes `pwsh`, también sirve `powershell`. `-ExecutionPolicy` afecta
solo a ese proceso.

En ambas plataformas, sustituye `codex` por `claude`, `cursor` o `gemini` según
tu cliente; Codex necesita su CLI en PATH. Setup registra MCP e instrucciones
gestionadas en la configuración del cliente. Revisa el dry run y abre una
**conversación nueva**. `doctor` comprueba la configuración y prueba MCP
directamente; no acredita que el cliente cargue o aplique la integración.

**Gemini:** la configuración está en `~/.gemini`, o en
`$GEMINI_CLI_HOME/.gemini` con una carpeta personal alternativa. Ejecuta
`gemini mcp list` para comprobar su detección; la confianza de la carpeta puede
mantener desactivado un servidor listado. Repetir setup corrige los registros
antiguos en una raíz incorrecta y conserva los archivos anteriores.

El estado permanece en `~/.babylon60` (o `$BABYLON_HOME`). El manifiesto marca
v5.1.0 como `candidate`; la etiqueta Git es anterior a `run`, `demo` y `log`.
Anota `git rev-parse HEAD` para identificar la revisión que instalas.

[Instalación avanzada y retirada](docs/03_guides/README_REFERENCE_ES.md#instalación).

<a id="límites-conocidos"></a>

## Lo que `run` no impide

- **Acceso a la red:** los datos del workspace pueden salir de la máquina.
- **Persistencia:** los archivos concedidos siguen admitiendo escritura.
  Se comparan rutas seleccionadas de arranque y configuración antes y después;
  editar archivos como `AGENTS.md` o `Makefile` puede no generar aviso.
  Revisa los cambios antes de ejecutar el contenido fuera del sandbox.
- **Otros accesos al equipo:** el llavero de macOS no queda completamente
  aislado. En Linux siguen legibles las líneas de órdenes de otros procesos
  y las señales no se aíslan por debajo de Landlock ABI 6. Nunca pases
  credenciales como argumentos de comandos.
- **Equipo comprometido:** un administrador o sistema operativo comprometido
  queda fuera del modelo de amenazas declarado. Babylon se ejecuta en espacio de usuario.

Algunas funciones de los agentes y sus sandboxes anidados dejan de funcionar
bajo confinamiento. Las [restricciones por plataforma y compatibilidad](docs/03_guides/README_REFERENCE_ES.md#lo-que-deja-de-funcionar-dentro)
detallan las funciones afectadas y lo que sigue sin verificarse.

## Cómo funciona

Son **dos rutas que se configuran por separado**, no un lanzador combinado:

```mermaid
flowchart LR
    subgraph Confinamiento
        Run["babylon60 run"] --> Agent["CLI del agente bajo política del SO"]
    end
    subgraph Autorización
        MCP["Herramienta MCP con efectos"] --> Broker["Broker nativo + aprobación válida"]
        Broker --> Effect["Efecto protegido"]
    end
```

El broker rechaza las herramientas MCP con efectos si falta la biblioteca
nativa Rust o una aprobación válida para esa tarea exacta. El instalador no
compila la biblioteca; consulta la [configuración del broker](docs/security/fl-mcp01-authority-drift.md#uso-y-comprobación)
y la [autorización firmada](docs/03_guides/guide_signed_authorization.md).

El registro de eventos es distinto del adaptador CORTEX Memory versionado,
que requiere su propio vínculo de lanzamiento firmado y un broker nativo.
Setup no arranca ese adaptador. [Arquitectura y alcance de la memoria](docs/03_guides/README_REFERENCE_ES.md#más-allá-del-confinamiento).

## Qué está verificado

[`CLAIMS.toml`](CLAIMS.toml) registra estado, alcance y nivel de evidencia por
declaración. Los modelos formales, los tests software y la verificación física
del hardware son evidencias distintas. La demo tiene sus propias ejecuciones registradas.

```bash
bash verify.sh
```

Comprueba el árbol de fuentes, los hashes de ambos README, las declaraciones,
el SBOM y la evidencia frente a [`RELEASE_MANIFEST.json`](RELEASE_MANIFEST.json).
**No** vuelve a ejecutar las suites. Editar las fuentes invalida el recibo;
regenerarlo requiere pruebas nuevas sobre un commit fuente limpio.

Un manifiesto `unsigned_local_evidence` con `signature: null` comprueba
integridad, pero no autentica al publicador. Los badges de CI corresponden a
su workflow y commit, no a todas las garantías. Los tests P-256 software no
acreditan Touch ID; las pruebas con `SIGKILL` no acreditan resistencia a cortes
eléctricos físicos. Babylon no certifica por sí solo conformidad jurídica.

[Niveles de evidencia, métodos y límites](docs/03_guides/README_REFERENCE_ES.md#qué-está-verificado).

## Documentación

[Referencia técnica completa](docs/03_guides/README_REFERENCE_ES.md) ·
[Guía de usuario](docs/03_guides/USER_GUIDE.md) ·
[Índice documental](docs/README.md) · [Web](https://babylon60.com/)

Las secciones detalladas que antes estaban en esta página siguen disponibles aquí:

| Tema | Referencia |
| :--- | :--- |
| <a id="qué-verás"></a>Qué verás | [Leer](docs/03_guides/README_REFERENCE_ES.md#qué-verás) |
| <a id="qué-hace-la-demo"></a>Qué hace la demo | [Leer](docs/03_guides/README_REFERENCE_ES.md#qué-hace-la-demo) |
| <a id="ejecuciones-registradas"></a>Ejecuciones registradas | [Leer](docs/03_guides/README_REFERENCE_ES.md#ejecuciones-registradas) |
| <a id="lo-que-deja-de-funcionar-dentro"></a>Lo que deja de funcionar dentro | [Leer](docs/03_guides/README_REFERENCE_ES.md#lo-que-deja-de-funcionar-dentro) |
| <a id="más-allá-del-confinamiento"></a>Más allá del confinamiento | [Leer](docs/03_guides/README_REFERENCE_ES.md#más-allá-del-confinamiento) |
| <a id="vocabulario"></a>Vocabulario | [Leer](docs/03_guides/README_REFERENCE_ES.md#vocabulario) |
| <a id="cinco-pruebas-de-aceptación"></a>Cinco pruebas de aceptación | [Leer](docs/03_guides/README_REFERENCE_ES.md#cinco-pruebas-de-aceptación) |
| <a id="cotas-de-incidentes-sigkill-de-proceso-vs-corte-eléctrico-físico"></a>Cotas de Incidentes (SIGKILL de Proceso vs. Corte Eléctrico Físico) | [Leer](docs/03_guides/README_REFERENCE_ES.md#cotas-de-incidentes-sigkill-de-proceso-vs-corte-eléctrico-físico) |
| <a id="matriz-normativa-de-hashes-blake3--sha-256--sha3-256"></a>Matriz Normativa de Hashes (BLAKE3 · SHA-256 · SHA3-256) | [Leer](docs/03_guides/README_REFERENCE_ES.md#matriz-normativa-de-hashes-blake3--sha-256--sha3-256) |
| <a id="mapa-del-repositorio"></a>Mapa del repositorio | [Leer](docs/03_guides/README_REFERENCE_ES.md#mapa-del-repositorio) |

## Preguntas Frecuentes para Humanos

**¿Me pedirá la huella continuamente?**
`run` no pide firmas. Las herramientas MCP con efectos requieren aprobar la
tarea exacta. Si Touch ID falla, `approve` aborta sin reintentos ni autenticación alternativa
por contraseña o PIN. El ejecutor Rust admite por separado una clave Ed25519
autorizada. [Alcance de la autenticación](docs/03_guides/README_REFERENCE_ES.md#preguntas-frecuentes-para-humanos).

**¿Ralentiza el equipo o gasta batería?**
El consumo de batería, CPU y tráfico de coherencia de caché está `NO_VERIFICADO`.
Un benchmark local de throughput no es una medida de energía.

**¿Cómo lo desinstalo?**
Desde el clon, ejecuta `.venv/bin/babylon60 setup --client <cliente> --remove`
para cada integración (Windows: `.\.venv\Scripts\babylon60.exe`). Conserva
configuración ajena o modificada y el ledger. Después elimina el clon;
conserva la carpeta de estado separada salvo que quieras borrar también esos datos.
[Conflictos y retirada](docs/03_guides/guide_codex_first_use.md#diagnóstico-y-retirada).

## Licencia, seguridad y cita

[Sovereign Dual-License v4.0](LICENSE) es una licencia propia, **no aprobada por OSI**.
El uso no comercial tiene un nivel gratuito; el uso comercial tiene
[condiciones específicas](docs/COMMERCIAL_LICENSE.md). Consulta la licencia para
conocer las condiciones completas, incluidas las restricciones de redistribución
y uso automatizado de los activos.

Comunica vulnerabilidades de forma privada a `security@babylon60.com` según
[SECURITY.md](SECURITY.md). Para citar el proyecto, usa [CITATION.cff](CITATION.cff).

<sub>BABYLON-60 v5.1.0 · Borja Moskv</sub>
