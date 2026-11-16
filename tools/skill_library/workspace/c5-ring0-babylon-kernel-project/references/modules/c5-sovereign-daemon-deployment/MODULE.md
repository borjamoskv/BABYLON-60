---
name: c5-sovereign-daemon-deployment
display_name: Despliegue del Sovereign Spark Daemon en Launchd
description: Protocolo estricto para desplegar el Sovereign Spark Daemon (Antigravity
  Engine en Rust) sobre el sistema init local de macOS (launchd) para ejecución 24/7
  ininterrumpida. Dispara con "c5-sovereign-daemon-deployment", "desplegar sovereign
  daemon", "launchd rust daemon", "daemon 24/7".
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

# Despliegue de Daemon Soberano 24/7 (launchd + Ring-0)

Cuando el operador solicite desplegar el daemon en macOS, preparar su configuración para el checkout y el ejecutable elegidos. Preparar el archivo no autoriza instalarlo ni arrancar el proceso; aplicar el contrato de autorización y atestación vigente antes del efecto protegido.

## 1. Topología del Agente (Rust)
El orquestador DEBE estar escrito en Rust (Ring-0) para minimizar la disipación térmica y latencia de ciclo.
- Si la tarea requiere construir el ejecutable, compilar el target elegido con perfil optimizado y lockfile: `cargo build --release --locked --bin <target>`. Preparar únicamente un plist para un binario existente no requiere compilar.
- Verificar la interfaz real del gate y los parámetros estructurados de acción, agente, ámbito y hash antes de integrar la llamada. Conservar el rechazo sin reintentos y verificar el efecto por separado; el nombre del daemon no acredita atestación.

## 2. Archivo de Lista de Propiedades (`.plist`)
Preparar el plist fuera de `~/Library/LaunchAgents` para revisión. Una sesión de usuario por sí sola no garantiza acceso a TouchID; comprobar los requisitos del gate en el entorno objetivo.

**Generación portable:** recibe rutas absolutas verificadas del proyecto, binario y directorio de logs. `WorkingDirectory` fija la raíz usada por los recursos relativos; `plistlib` escapa espacios y caracteres XML. La función solo devuelve bytes, sin escribir, instalar ni arrancar servicios.
```python
from pathlib import Path
import plistlib

def render_launch_agent(project_root, executable, log_dir):
    root, binary, logs = map(Path, (project_root, executable, log_dir))
    if not all(p.is_absolute() for p in (root, binary, logs)):
        raise ValueError("Use verified absolute paths")
    if not root.is_dir() or not binary.is_file() or not logs.is_dir():
        raise ValueError("Project, executable and log directory must exist")
    return plistlib.dumps({
        "Label": "com.c5real.antigravity.daemon",
        "ProgramArguments": [str(binary)],
        "WorkingDirectory": str(root),
        "RunAtLoad": False,
        "KeepAlive": False,
        "StandardOutPath": str(logs / "daemon_stdout.log"),
        "StandardErrorPath": str(logs / "daemon_stderr.log"),
        "EnvironmentVariables": {"C5_SANDBOX_MODE": "0"},
    })
```

## 3. Ignición y Ciclo de Vida (`launchctl`)
Validar el plist preparado con `plutil -lint <archivo>`, revisar sus rutas y comprobar los permisos de ejecución y logs. Instalarlo y usar `launchctl` solo dentro de la autorización explícita del despliegue y con atestación del efecto real. Mantener el arranque y reinicio automáticos desactivados hasta verificar su política; un rechazo biométrico no debe convertirse en un bucle de reintentos.

## 4. Invariante de Hardware (Mac Studio)
Recordar que en portátiles bajo suspensión profunda, `launchd` se detiene. El entorno objetivo de esta habilidad asume un nodo de escritorio de alta densidad conectado a red permanente (Mac Studio Ultra) actuando como el cerebro de ejecución remota para la flota.
