# Primera conversación con Babylon en Codex

Babylon añade preferencias de comprensión, resolución y presentación a las
conversaciones nuevas de Codex local. El MCP aporta herramientas y el contrato
portable. La instalación no cambia el modelo elegido ni acredita una mejora
por sí sola: la evaluación de respuestas se describe en el
[piloto de primera conversación](guide_first_conversation_pilot.md).

## Instalar y conectar

Desde un checkout limpio o el paquete fuente de distribución:

```sh
bash install.sh --client codex
```

En Windows:

```powershell
pwsh -NoProfile -File .\install.ps1 -Client codex
```

Si Babylon ya está instalado, usa su ejecutable `babylon60`:

```sh
babylon60 setup --client codex --dry-run
babylon60 setup --client codex
babylon60 doctor --client codex --json
```

Si no está en PATH, el instalador indica la ruta absoluta. Codex y su CLI deben
estar instalados; Babylon no los instala automáticamente. Abre una conversación
nueva o recarga el cliente después de activar la integración. No hace falta
copiar instrucciones en cada petición. La configuración local no se propaga a
otros equipos ni a clientes web.

## Qué se configura

La integración registra el MCP del entorno instalado y añade un bloque breve
de preferencias al archivo global de instrucciones efectivo de Codex. Respeta
`CODEX_HOME`, las preferencias existentes y las instrucciones de cada proyecto.
No modifica el selector del modelo. La configuración y el bloque propios se
identifican para permitir activaciones repetidas y su retirada.

Una entrada Babylon incompatible, un archivo no seguro o una edición concurrente
produce un conflicto explícito. No se reemplaza contenido ajeno para resolverlo.
Si cambia el archivo global efectivo, vuelve a ejecutar el diagnóstico y setup
para migrar únicamente el bloque gestionado. Mover o borrar el entorno instalado
puede dejar una ruta inválida; vuelve a configurar la integración tras reinstalar.

El perfil se aplica con intensidad adaptativa: resultado primero y respuesta
ágil en tareas simples; contexto, herramientas y comprobaciones adicionales
cuando ayuden a resolver. MOSKV-1 y el Panel conservan sus funciones de identidad
y trazabilidad. La activación no autoriza recopilación indiscriminada, memoria
automática entre proyectos ni efectos protegidos del kernel.

## Diagnóstico y retirada

`doctor` comprueba configuración, ejecutable instalado, inicialización MCP,
descubrimiento de herramientas y entrega del contrato. La sonda usa datos
temporales; no escribe en el ledger productivo. Un resultado correcto acredita
disponibilidad local, no una sesión real de Codex ni aplicación por el modelo.
La mejora de comportamiento permanece `NO_VERIFICADO` hasta su evaluación.

```sh
babylon60 setup --client codex --remove --dry-run
babylon60 setup --client codex --remove
```

La retirada elimina únicamente configuración y preferencias gestionadas que no
hayan sido alteradas por terceros. Conserva los datos del ledger y las demás
preferencias. Una modificación externa se informa para evitar borrar trabajo
del usuario. Instalar sin seleccionar cliente conserva el modo CLI/MCP y no
activa preferencias globales. El modo servidor `--mcp` se usa por separado de
`--client` para preservar el transporte JSON-RPC.

Codex no expone todas las opciones de un registro mediante su CLI de consulta.
Por eso, antes de una retirada o reconfiguración destructiva Babylon también
comprueba que el archivo de configuración conserva la revisión registrada.
Un cambio posterior, incluso en otra sección, puede exigir revisión manual;
repetir setup no adopta silenciosamente esa configuración como propia.

## Alcance de la evidencia

Las pruebas automatizadas cubren instalación y transporte; una conversación
real debe acreditar por separado que Codex carga las preferencias sin pegarlas
en el chat. El piloto compara tareas equivalentes con y sin Babylon y requiere
revisión humana. No se extrapola su resultado a clientes, versiones o tareas
no evaluados. Consulta el [contrato de presentación](../../01_KISH_ENGINE/babylon60/presentation.md)
y la [firma portable](guide_portable_signature.md) para adaptar la salida al medio.
