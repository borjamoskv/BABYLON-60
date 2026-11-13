# H10 — construcción y prueba de la imagen Docker

> **Registro histórico recuperado el 13 de noviembre de 2026.** Este documento conserva la evidencia y los dictámenes de la iteración del 5–6 de noviembre, tomada de `bc563d6cd4d6e021ca73ec035a75588774a4f511`. No valida el árbol recuperado sobre `daa0a848e5dce9d79446fe47dc4c3083061346a5` ni sustituye su nueva aceptación. H08 y la ejecución remota de H09 permanecen pendientes; los resultados locales de Docker, dependencias y pruebas requieren repetición sobre ese árbol.

**H10 cerrado en Linux ARM64.** La imagen final se construyó sin caché y pasó
las pruebas reales de instalación, CLI, MCP y dashboard. H08 y la validación
remota de H09 permanecen pendientes. Este trabajo no incluye merge ni publicación
de la imagen en un registro.

La iteración parte de `7ff9b5efaf1e115552df7512dd45b8a3e28b87c9` de la
[PR #48](https://github.com/borjamoskv/BABYLON-60/pull/48). El resultado actual de
la auditoría es **21 hallazgos aceptados localmente, H09 parcial y H08 aplazado**.

La [validación posterior de Z3](Z3_INSTALLATION_VALIDATION_2026-11-05.md)
reconstruye esta imagen con Z3 5.3.3.0 y el nuevo control de compatibilidad;
registra el ID actualizado. Las observaciones siguientes conservan la primera
construcción de H10 con Z3 5.1.0.

## Correcciones

- `.dockerignore` excluye bases de datos, credenciales locales, Git, entornos y
  cachés. Conserva los recursos de skills necesarios para construir el paquete.
- Ambas etapas usan Python 3.14 sobre Debian Trixie: glibc 2.41 admite el wheel
  ARM64 de Z3 que requiere manylinux 2.38. El runner declara `libstdc++6`.
- uv está fijado a 0.13.5. `uv sync --locked --no-dev --no-editable` comprueba
  el lock e instala el paquete; se deshabilitan caché y descarga de otro Python.
  No cambian dependencias ni lockfiles.
- El builder conserva el compilador C necesario para evdev y retira toolchains
  Rust/LLVM/Protobuf que no ejecutaba. No se afirma que esta imagen compile o
  certifique el kernel Rust. El MCP base usa su propio transporte stdio;
  no necesita instalar el extra Gemini.
- El runner usa el paquete instalado, sin PYTHONPATH, y el usuario `babylon60`
  con UID 1000. Su estado se crea bajo `/home/babylon60/.babylon60`.

## Evidencia de construcción

| Propiedad | Observación |
| --- | --- |
| Plataforma | Linux ARM64, Docker Engine 29.5.2 en Colima sobre macOS ARM64 |
| Build | Imagen completa con `docker build --no-cache`, exit 0; 70,975 segundos |
| Imagen local | `babylon60-h10:pr48` |
| ID de imagen | `sha256:7c514bcb3085ff9d3fc89e4ba9f69a39cf8388448077fabda420b5b3e9949a10` |
| Base Python observada | `python@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d` |
| Base uv observada | `ghcr.io/astral-sh/uv@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff` |
| Python / libc del runner | Python 3.14.10 / glibc 2.41 |

El cliente usó el builder legacy disponible, que informa una advertencia de
obsolescencia por ausencia del plugin Buildx. La construcción sí terminó;
esa advertencia no se convierte en una prueba de BuildKit ni de otras plataformas.
Los tags de base y paquetes del sistema pueden cambiar: los digests anteriores
identifican las bases observadas, no una promesa de reconstrucción bit a bit.

## Pruebas reales de la imagen

El harness [smoke_docker.py](../../scripts/c5_quality_gates/smoke_docker.py)
crea contenedores temporales propios y comprueba el ID de la imagen construida.
El resultado combinado fue `status=passed`, `acceptance_complete=true`; todos
los comandos terminaron en cero y se retiraron sus contenedores.

Un revisor independiente repitió el runtime de ese mismo ID de imagen: 30
comandos con salida cero, los mismos resultados de aplicación y ningún
contenedor de prueba restante. Su ejecución `runtime_only` no afirma otro build;
el cierre combina esa repetición con la construcción completa registrada.

- UID del proceso y PID 1: 1000. El estado inicial no existe y el usuario puede
  crearlo y escribirlo. Git, cachés y bases de datos locales no aparecen en `/app`.
- Origen importado: `/app/.venv/lib/python3.14/site-packages/babylon60/`.
  Z3 5.1.0 carga su biblioteca nativa y resuelve una expresión comprobada.
- Recursos empaquetados: catálogo, directorio físico y lock íntegros; 131 skills,
  26 de workspace y raíz `6acb4327e05ce6e1f421fc69b7b28020b95477822b9fb30557185b17c54f6a61`.
- CLI `--help`: exit 0 e interfaz prevista.
- MCP real por stdio: initialize, 13 herramientas, skills físicos, ping y EOF
  con exit 0. Se rechazan respuestas con error, IDs incorrectos o datos ausentes.
- CMD original del dashboard: índice y `/api/metrics` responden 200. Una fila
  SQLite con nonce nuevo aparece con sus tres campos públicos y excluye una
  columna privada; `dashboard.js` responde y el healthcheck llega a `healthy`.
- Runtime sin red exterior (`--network none`), mounts, puertos publicados ni
  variables proxy heredadas. Se conserva el bind loopback del servidor.

Los ocho tests del harness, Ruff y MyPy pasan. Una corrección de tipos capturó
los mismos handles de stdin/stdout para sus closures; después se repitieron
los ocho tests y el runtime completo sobre el mismo ID de imagen, con éxito.
Estos tests comprueban rechazos de
respuestas inválidas; la aceptación de H10 se apoya en los contenedores reales,
no en esos tests unitarios. Los logs y el JSON detallado permanecen en el
expediente local; este documento no distribuye un archivo de imagen ni esos logs.

Para reproducir desde la raíz, con un motor Docker operativo:

```sh
python3 scripts/c5_quality_gates/smoke_docker.py \
  --docker-context colima-babylon60-h10 \
  --image babylon60-h10:pr48 \
  --build-context . \
  --output-dir /tmp/babylon60-h10
```

Sustituir el contexto por el del motor local. `--runtime-only` permite repetir
el arranque de una imagen existente, pero por sí solo deja
`acceptance_complete=false`: no acredita una construcción nueva.

## Fallos conservados y límites

El primer comando rechazó `--progress` porque este cliente no tenía Buildx.
El siguiente build de la configuración anterior terminó con un error de I/O al
materializar la capa de Rust/compiladores. En paralelo se observó ENOSPC en el
host; se atribuye el fallo a ese agotamiento, sin confundir ambos mensajes. No
llegó a ejecutar uv sync. Se conservó su log,
se retiró únicamente el perfil Docker de prueba y se simplificó el builder antes
de repetir. Se regeneraron tres entornos de pruebas temporales inactivos,
conservando sus inventarios, fuentes, resultados y logs. Esos intentos fallidos
no cuentan como aceptación.

El dashboard sigue escuchando en el loopback del contenedor: la prueba HTTP
se ejecuta dentro de él. Publicar un puerto con `-p` en una red bridge no cambia
ese bind ni acredita acceso desde el host. No se añade un relay ni se relaja
la protección. No se ensayan otras arquitecturas, producción, biometría, efectos
externos ni CI hosted. H08 y la validación remota de H09 siguen pendientes;
la PR debe permanecer abierta, sin merge ni auto-merge.
