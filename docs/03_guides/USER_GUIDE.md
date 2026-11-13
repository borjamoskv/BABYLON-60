# Guía de usuario de BABYLON-60

La distribución de terminal ofrece la CLI `babylon60` y el servidor de memoria
`babylon60-mcp`. Puedes usarlos para conectar memoria estructurada a un cliente
MCP y consultar las herramientas y preferencias de presentación del proyecto.
El núcleo de seguridad se mantiene como alpha: sus garantías dependen del
broker, del aislamiento del agente y de la evidencia delimitada en
[`CLAIMS.toml`](../../CLAIMS.toml).

## 1. Instalar y conectar

Necesitas Python 3.11 o posterior y `uv`. Para la integración con Codex también
deben estar disponibles Codex y su CLI. Desde un checkout limpio o el paquete
fuente de distribución, en macOS o Linux:

```sh
bash install.sh --dry-run --client codex
bash install.sh --client codex
.venv/bin/babylon60 doctor --client codex --json
```

En Windows, desde PowerShell:

```powershell
pwsh -NoProfile -File .\install.ps1 -DryRun -Client codex
pwsh -NoProfile -File .\install.ps1 -Client codex
.\.venv\Scripts\babylon60.exe doctor --client codex --json
```

Si quieres únicamente CLI y MCP, omite `--client codex` o `-Client codex`.
El instalador muestra dónde queda el ejecutable; usa esa ruta si `babylon60`
no está en PATH. La instalación de terminal no incluye una aplicación de
escritorio. Abre una conversación nueva de Codex tras activar la integración.

## 2. Comprobar qué está disponible

Desde el entorno instalado:

```sh
babylon60 --help
babylon60 --version
babylon60 doctor --client codex --json
babylon60 tools --server all
babylon60 skills list --scope workspace
```

`doctor` comprueba la configuración y la inicialización del MCP con datos
temporales. Un diagnóstico correcto acredita disponibilidad local. Comprobar
que Codex carga y aplica las preferencias en una conversación requiere una
observación separada, descrita en la
[guía de primera conversación](guide_codex_first_use.md).

`tools` muestra un catálogo de herramientas y recursos; una entrada en ese
catálogo no prueba que haya un servidor activo. `skills` permite consultar las
habilidades declaradas. Usa la ayuda de cada comando para ver sus opciones y
requisitos en la versión instalada.

## 3. Usar memoria persistente

El servidor de memoria se comunica por stdio y utiliza un ledger SQLite con
encadenamiento de hashes. Para apuntarlo a un archivo propio:

```sh
babylon60-mcp --ledger /ruta/absoluta/mi_proyecto.db
```

Configura el cliente MCP para iniciar ese ejecutable con la misma ruta en cada
sesión. El cliente y el agente deciden cuándo consultar o guardar información;
la conexión no supone memoria automática entre proyectos. Los hashes permiten
comprobar integridad dentro del protocolo implementado. Un archivo SQLite no
aporta por sí solo almacenamiento físicamente inmutable ni una garantía de
recuperación frente a cualquier fallo.

El [puente MCP del kernel](guide_kernel_mcp.md) es una integración independiente
que requiere el checkout completo y su propio entorno. Sus operaciones están
sujetas a los controles de autorización y aislamiento aplicables.

## 4. Consultar preferencias y herramientas adicionales

```sh
babylon60 presentation
babylon60 signature --schema
babylon60 skills status
```

El [contrato de presentación](../../01_KISH_ENGINE/babylon60/presentation.md)
orienta la redacción de respuestas. La aplicación anfitriona controla cómo se
cargan y se muestran esas instrucciones. Los enlaces de reglas del repositorio
comparten una fuente; cada cliente debe admitirla y cargarla para aplicarla.

La [firma portable](guide_portable_signature.md) presenta datos observados de
una tarea. Su formato no constituye una atestación hardware ni certifica el
contenido. Los informes del exportador de evidencia también requieren revisar
sus fuentes y alcance; generarlos no certifica cumplimiento normativo.

La CLI contiene otras herramientas que puedes descubrir con `--help`. Su
presencia en el menú no acredita que estén desplegadas, autorizadas o validadas
en tu equipo.

## 5. Actualizar o retirar la integración

Conserva el ledger y su configuración antes de cambiar de versión. Si se mueve
el entorno instalado, vuelve a ejecutar `setup` desde la nueva instalación y
comprueba el resultado con `doctor`. Los conflictos de configuración requieren
revisión; no deben resolverse borrando preferencias ajenas.

Para retirar únicamente la integración gestionada de Codex:

```sh
babylon60 setup --client codex --remove --dry-run
babylon60 setup --client codex --remove
```

La retirada conserva los datos del ledger y las preferencias ajenas. Consulta
el [procedimiento de diagnóstico y retirada](guide_codex_first_use.md#diagnóstico-y-retirada)
si se informa de una modificación externa. El alcance de la versión y las
fuentes de implementación se recogen en la
[guía de fuente de verdad](guide_repository_source_of_truth.md).
