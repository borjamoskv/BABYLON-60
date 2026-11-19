# Confinamiento de agentes

## Con tu agente

```bash
babylon60 run --preset claude-code -- claude
```

```bash
babylon60 run --preset codex -- codex
```

Sin perfil, `babylon60 run -- <comando>` concede el workspace, las rutas del
sistema en lectura, `/dev/shm`, los dispositivos `/dev/null`, `/dev/zero`,
`/dev/full`, `/dev/random`, `/dev/urandom`, `/dev/tty` y `/dev/ptmx`, su propio
terminal, un TMPDIR privado que se borra al acabar y, si el ejecutable del
comando está bajo un HOME, ese archivo y solo él, en lectura y ejecución. En
macOS concede también el prefijo del intérprete que arranca el trampolín y deja
leer los enlaces simbólicos bajo un HOME que llevan hasta el comando, porque
para Seatbelt seguir un enlace es leerlo. Cada perfil concede además
la configuración de su agente, sus prefijos de instalación y, en solo lectura,
la configuración de git, solo si existen. `--dry-run` muestra la política sin
ejecutar nada. Un agente instalado fuera de las rutas del sistema y de los HOME
(por ejemplo, con npm bajo un prefijo propio) necesita `--allow-read` de su
instalación; en Linux, `run` lo detecta y dice qué directorio conceder (el
primer `node_modules`, la raíz del virtualenv o la carpeta del programa).

- **Rutas.** `--allow-read` y `--allow-write` añaden rutas, comprobadas por
  identidad de inodo. Se rechazan el HOME y sus ancestros, los directorios
  sticky que todos pueden escribir (`/tmp`, `/var/tmp`), la escritura sobre,
  encima o dentro del propio diario y del código del lanzador (su virtualenv,
  el paquete, la biblioteca estándar del intérprete), que en lectura sí se
  pueden conceder, y el conjunto protegido: `~/.ssh`, `~/.gnupg`, `~/.aws`,
  `~/.azure`, `~/.kube`, `~/.docker`, `~/.netrc`, `~/.git-credentials`,
  `~/.password-store`, `~/.config/gcloud`, `~/.config/gh`, `~/.config/hub`,
  `~/.config/op`, `~/.config/git/credentials`,
  `~/.config/containers/auth.json`, `~/.npmrc`, `~/.pypirc`,
  `~/.cargo/credentials(.toml)`, `~/.vault-token`,
  `~/.terraform.d/credentials.tfrc.json`, `~/.local/share/keyrings` y
  `~/Library/Keychains`. Mientras existan, una ruta que los contenga también
  se rechaza.
- **git.** Cada perfil concede en solo lectura, uno por uno: `~/.gitconfig`;
  los `config`, `ignore` y `attributes` de `~/.config/git` (o de
  `$XDG_CONFIG_HOME/git`); lo que incluyen con `include.path` e
  `includeIf.<condición>.path`, hasta la profundidad que lee git (10), y nunca
  un `includeIf` sin condición, que git no incluye; los archivos que nombran
  `core.excludesFile`, `core.attributesFile` y `commit.template`, y el
  directorio de `core.hooksPath`, cuyos hooks se ejecutan dentro, confinados.
  Son 64 rutas como máximo. `~/` sale del HOME que recibe el agente y
  `~usuario/`, de la base de cuentas, como en git; un `~usuario` que no existe
  en `include.path` o en una ruta de `core` hace morir a git, y ahí se deja de
  seguir ese archivo. Un enlace simbólico en el camino, como los de stow o
  home-manager, se sigue si está fuera de todo grant de escritura, y si está
  bajo el HOME `run` avisa de qué destino concede; uno que el agente podría
  cambiar no se sigue. Cada ruta pasa antes las comprobaciones
  de cualquier otra: se rechazan el HOME y sus ancestros, el conjunto
  protegido, también por hardlink, y una ruta que pasa por un directorio con
  nombre de ruta protegida (`.ssh`, `.aws`…) de un HOME ajeno. Tampoco se
  concede un archivo cuyo contenido parece una credencial, ni un directorio de
  hooks que contenga un archivo retenido por eso. En la configuración cuentan
  `http.*.extraHeader`, una URL con contraseña o una URL http(s) con usuario
  (también en una reescritura `url.*.insteadOf`), una clave con `pass`,
  `token`, `secret` u `oauth` en el nombre y un `credential.helper` con
  `password=` o `token=`; una marca de orden de bytes UTF-8 al principio no
  oculta la primera sección. En `ignore`, `attributes` y la plantilla solo
  cuentan esas URL: `[Bb]in/` es un patrón, no una sección.
  `run` avisa con el archivo, la línea y la clave, nunca el valor, y dice qué
  hará git dentro: sin un `config` no lee su configuración; sin un `ignore`,
  fallan `git add`, `git commit` y `git status`; sin `attributes`, solo avisa;
  sin la plantilla, `git commit` falla si no recibe un mensaje; sin los hooks,
  falla `git commit` cuando debe ejecutar un `pre-commit`. Es una heurística:
  una credencial con otra forma se concede con su archivo. Lo que incluye o
  nombra un archivo que el agente puede escribir no se sigue. Necesitan
  `--allow-read`: un archivo retenido como credencial, el destino de un enlace
  que el agente podría cambiar, las demás rutas que nombre la configuración
  (`init.templateDir`, `blame.ignoreRevsFile`, `gpg.ssh.allowedSignersFile`, un
  programa bajo el HOME…) y lo que apunte `GIT_CONFIG_GLOBAL`. Un directorio de
  hooks que las comprobaciones rechazan, como el HOME o una ruta protegida, no
  se concede de ninguna forma. En macOS se salta una ruta que Seatbelt no puede
  nombrar en una regla (con un carácter de control, o más larga que sus
  literales); si llega con `--allow-read`, `run` sale con 3.
- **Entorno.** Las variables cuyo nombre parece una credencial no llegan al
  agente. Con las palabras del nombre separadas por `_`: una que acaba en
  `TOKEN` o contiene `SECRET`, `PASSWORD`, `PASSWD`, `PASSPHRASE` o
  `CREDENTIAL`; una última palabra `KEY`, `APIKEY`, `PAT` o `AUTH`; `PASS` o
  `PWD` como palabra que no sea la primera (`DB_PASS`, `SMTP_PASS_1`,
  `ORACLE_PWD`; nunca `PWD` ni `OLDPWD`); `*_KEY_ID`, `OP_SESSION_*` y una
  lista fija (`AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`,
  `AWS_SECURITY_TOKEN`, `KRB5CCNAME`, `MYSQL_PWD`, `DOCKER_AUTH_CONFIG`,
  `GOOGLE_APPLICATION_CREDENTIALS`…). Tampoco llega, se llame como se llame,
  una variable cuyo valor es una URL con contraseña
  (`DATABASE_URL=postgres://usuario:clave@host`). Otras de AWS sí llegan, como
  `AWS_PROFILE`, `AWS_REGION`, `AWS_DEFAULT_REGION`, `AWS_CONFIG_FILE` o
  `AWS_ROLE_ARN`; `~/.aws` sigue protegido. `run` dice cuáles retira, nunca
  sus valores. `--pass-env NAME` conserva una y cada perfil conserva la
  credencial de su agente (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`…).
  `SSH_AUTH_SOCK` y `GPG_AGENT_INFO` se retiran salvo `--keep-agent-sockets`.
  Si retiene algo, `run` se re-ejecuta sin esas variables antes de lanzar al
  agente, así que ni el lanzador las conserva. Es defensa en profundidad:
  Landlock y Seatbelt ya niegan leer el entorno de otro proceso (V22).
- **TMPDIR privado.** El agente recibe en `TMPDIR` un directorio privado que se
  borra al acabar. Algunas herramientas no usan `TMPDIR` y escriben donde el
  agente no puede, y donde lo que dejara sobreviviría a la sesión; `run` les da
  un sitio dentro de ese directorio salvo que tu entorno ya fije la variable:
  - `CLANG_MODULE_CACHE_PATH=<TMPDIR>/clang-module-cache`, que el driver de
    clang lee cuando no recibe `-fmodules-cache-path`. Sin ella,
    `clang -fmodules` guarda su caché de módulos en el directorio de cachés
    del usuario en `/private/var/folders` (macOS), que el perfil niega, o en
    `~/.cache/clang/ModuleCache` (Linux), bajo el HOME negado. Medido en Linux
    x86_64 con clang 18.1.3 y Landlock, como root y como uid 65534: sin la
    variable, compilar un módulo propio a través de `run` falla («unable to
    open output file ... ModuleCache ...»); con la de `run`, compila y la
    caché queda en el TMPDIR privado
    (`test_clang_builds_a_module_through_run_with_its_cache_in_the_private_tmpdir`).
    Fuera del sandbox, un `-fmodules-cache-path` explícito sigue mandando y
    una compilación sin módulos no la usa. Tu valor se respeta aunque esté
    vacío, como fuera de `run`: con él clang no usa caché, y una compilación
    que necesita un módulo falla (medido sin confinar con clang 18.1.3:
    «fatal error: module 'B60' is needed but has not been provided, and
    implicit use of module files is disabled»). En macOS el clang de Apple la
    lee, también con el valor que pone `run` (medido en f3242c4: ese test y
    `clang -fmodules` con `@import Foundation`, con la variable de `run` y con
    una propia, pasaron con su nombre en el JUnit).
  - `MAC_CHROMIUM_TMPDIR=<TMPDIR>`, solo en macOS, también si la tuya está
    vacía. Chrome crea el directorio del socket de su ProcessSingleton con
    `base::GetTempDir`, que en macOS lee esa variable y, si no está o está
    vacía, `NSTemporaryDirectory()` (código de Chromium,
    `base/files/file_util_apple.mm`). Que `NSTemporaryDirectory()` dé el
    directorio T del usuario y no `TMPDIR` se infiere del fallo de f3747db,
    con el TMPDIR privado escribible; coincide con swift-foundation
    (`String.temporaryDirectoryPath` lee `_CS_DARWIN_USER_TEMP_DIR` antes que
    `TMPDIR`) y con un comentario antiguo de Chromium
    (`base/files/file_util_mac.mm` en 90.0.4430.0: fijar `$TMPDIR` desde fuera
    no tenía efecto). Con la variable desapareció ese fallo (medido: en
    f3747db, sin ella, `[chrome-headless]`, la única variante entonces,
    escribió «Failed to create socket directory» y abortó; en f3242c4, con
    ella, `[chrome-headless-no-sandbox]` no lo escribió y llegó a arrancar
    procesos auxiliares, que Chrome solo lanza pasado ese paso, según su
    código; `[chrome-headless]` murió tras sus líneas de Crashpad, que en
    f3747db precedieron a ese fallo, así que su stderr no dice si llegó a ese
    paso), pero Chrome sin interfaz sigue sin funcionar confinado: muere por
    una señal (límite declarado en «macOS», arriba).

  Los directorios de cachés y temporales del usuario siguen negados: una caché
  de módulos que el agente pudiera escribir allí la cargarían después tus
  compilaciones sin confinar.
- **Terminal.** Si `run` tiene un terminal, el agente recibe un
  pseudoterminal privado y `run` hace de relé, como `sudo` con `use_pty`. Al
  acabar, ese terminal cuelga y, en Linux, `run` termina todo lo que el agente
  dejó en marcha antes de comparar hooks y metadatos.
- **Seccomp (Linux).** Se rechazan `TIOCSTI` y `TIOCLINUX`, los keyrings del
  kernel, la IPC System V, los modos setuid y setgid, `io_uring`, `openat2`
  (las librerías vuelven a `openat`) y los sockets Unix, salvo
  `--allow-unix-sockets`. Los pares de sockets de flujo dentro del sandbox
  siguen funcionando.
- **Seatbelt (macOS).** Se niegan las escrituras fuera de las rutas concedidas,
  las conexiones a sockets Unix con ruta (salvo `mDNSResponder` y `syslog`), las
  terminales ajenas, los clones y enlaces del conjunto protegido, los cambios de
  metadatos en el HOME y los bits setuid y setgid. También se niega lo que
  ejecutaría código o leería credenciales fuera del sandbox: LaunchServices
  (`open`), Apple Events, trabajos de launchd, montajes, señales, información y
  depuración de procesos ajenos y escribir preferencias. El perfil devuelve al
  agente las señales, la información y los puertos de tarea de sus propios
  procesos: que pueda señalar a sus hijos y depurar con `lldb` un programa que
  arrancó está medido en f3242c4, igual que la negación de las señales, de
  `KERN_PROCARGS2` y de la depuración de procesos ajenos, y que `hdiutil` no
  pueda montar. Con `ps` no puede inspeccionarlos: el propio sandbox niega
  ejecutar `/bin/ps`, setuid root (límite declarado arriba). Listar su grupo de
  procesos por `sysctl` (`kern.proc.pgrp`) también pasó en f3242c4. Según el
  código de XNU, las listas de `kern.proc` no pasan por la regla de
  información de procesos (`sysctl_prochandle` no la consulta); como el perfil
  solo niega `kern.procargs*` entre las lecturas de `sysctl`, con
  `kern.proc.all` el agente vería también los procesos ajenos: pid, padre,
  nombre y usuario, no sus argumentos ni su entorno (deducido del código;
  `NO_VERIFICADO` hasta que la CI corra
  `test_processes_outside_the_sandbox_are_not_listed_by_kern_proc`).
- **Servicios de macOS negados.** El perfil no deja buscar estos servicios Mach:
  el portapapeles (`com.apple.pasteboard.1`), salvo `--allow-clipboard`;
  Kerberos (`com.apple.GSSCred`); CoreSimulator; DiskArbitration; y, por
  `INV_C5_COMPUTER_USE_TRUST_GATEWAY`, el servidor de ventanas
  (`com.apple.windowserver.active`), la accesibilidad
  (`com.apple.accessibility.AXServer`), los Apple Events
  (`com.apple.coreservices.appleevents`) y la entrada de texto
  (`com.apple.tsm.portname`). Por eso, dentro del agente no funcionan `git`,
  `ssh` ni HTTP autenticados con Kerberos (GSSCred), los simuladores de iOS ni
  el portapapeles; es lo que implica el perfil, no una medida de la CI. En
  f3242c4 se midió negada la búsqueda del portapapeles, de Kerberos, de
  DiskArbitration, del servidor de ventanas y de los Apple Events;
  CoreSimulator, la accesibilidad y la entrada de texto no estaban registrados
  en el runner y su test se omitió. Chrome sin interfaz muere por una señal
  confinado, con su propio sandbox y sin él, y el servidor de ventanas sigue
  negado, como pide `INV_C5_COMPUTER_USE_TRUST_GATEWAY` (que sea parte de lo
  que cierra la captura de pantalla es inferido; límite declarado en «macOS»,
  arriba).
- **Portapapeles.** `--allow-clipboard` sirve para pegar imágenes en el agente
  y abre las dos direcciones, y `run` lo avisa: el agente puede leer lo que
  copies, una contraseña del gestor incluida, y sustituirlo, de modo que lo que
  pegues después, también en otro terminal, puede ser una orden suya. En Linux,
  donde la opción no cambia nada, `run` no avisa (medido); el aviso en macOS
  está medido en f3242c4
  (`test_allow_clipboard_warns_where_it_opens_the_pasteboard`).
- **Otras terminales.** `--allow-ptys` concede todas las terminales del
  usuario; `run` avisa porque deja leer y escribir otras pestañas.

| Agente | Estado | Comprobación |
| --- | --- | --- |
| Claude Code | Arranca confinado (`claude --version`); un `cat` del HOME recibe `Permission denied` | Linux x86_64, 11-11-2026. Sesión con LLM: `NO_VERIFICADO` |
| Codex CLI | Arranca confinado (`codex --version`); avisa de que no puede crear alias si falta `~/.codex` | Linux x86_64, 11-11-2026. Sesión con LLM: `NO_VERIFICADO` |
| git con su configuración | Con `--preset claude-code` o `--preset codex`, `git init`, `git add`, `git commit` y `git log` funcionan y leen el nombre de un archivo incluido, también con `~/.gitconfig` como enlace de stow, una reescritura `insteadOf` a ssh, `core.excludesFile`, `core.attributesFile`, `commit.template` sin `-m` y un hook `pre-commit` en `core.hooksPath`. Sin perfil, git muere: «fatal: unknown error occurred while reading the configuration files» | Linux x86_64, uid 65534, 11-11-2026 (`tests/test_confine_git.py`). macOS: `NO_VERIFICADO` |
| Firmar commits y credenciales de git | En Linux no funcionan dentro: las claves, los agentes y los almacenes de credenciales quedan fuera. `git commit -S` con gpg: «gpg: signing failed: Permission denied», con o sin `gpg-agent` en marcha. `git credential fill` con `credential.helper=store`: «could not read Username» (`~/.git-credentials` está protegido); con `credential.helper=cache`: «unable to connect to cache daemon: Operation not permitted». Firmar con una clave SSH y `git push` por SSH: `NO_VERIFICADO`, no hay `ssh` en la máquina de medida; `~/.ssh` está protegido (V01) y el socket de `ssh-agent` se niega (V16). En macOS el llavero sigue al alcance por `securityd` (límite declarado arriba): las credenciales de `osxkeychain`, el helper habitual allí, están `NO_VERIFICADO` y probablemente se pueden usar dentro | Linux x86_64, uid 65534, 11-11-2026. macOS: `NO_VERIFICADO` |
| Sandbox propio del agente anidado | En Linux se puede crear un espacio de nombres de usuario (`unshare -U true` sale con 0), pero no escribir su `uid_map` (`/proc` está concedido solo en lectura) ni cambiar montajes, y un sandbox anidado como bubblewrap necesita las dos cosas. `unshare -Urm true` funciona sin confinar y confinado responde «unshare: cannot open /proc/self/uid_map: Permission denied»; `unshare -Um true`, «unshare: cannot change root filesystem propagation: Operation not permitted». Claude Code 2.1.322 usa bubblewrap para su sandbox en Linux; bwrap no está instalado aquí, así que el sandbox de Claude Code anidado está `NO_VERIFICADO`, igual que el de Codex y Seatbelt dentro de Seatbelt | Linux x86_64, uid 65534, 11-11-2026 |

Arrancar confinado demuestra que la política deja funcionar al agente; no demuestra
que todas sus acciones queden cubiertas. `run` registra en el diario la política,
el código de salida, las variables retiradas (solo nombres), lo que cambió en la
persistencia y en los metadatos, y lo que quedó en marcha al acabar; las
denegaciones individuales de un agente real solo llegan al registro de auditoría
del kernel si está activo.
