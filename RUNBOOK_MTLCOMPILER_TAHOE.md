<!-- C5-REAL EXERGY CERTIFIED -->
# Runbook: MTLCompilerService SIGABRT (macOS Tahoe 26.5.2)

## 1. Topología del Fallo (Firma Estructural)
Este runbook documenta la etiología y mitigación de un colapso sistémico originado en el compilador de Metal de macOS (Tahoe 26.5.2).

**Firma del Crash Log (`.ips`):**
- **Proceso:** `MTLCompilerService`
- **Proceso Responsable (Trigger):** `Google Chrome Helper`
- **Excepción:** `EXC_CRASH (SIGABRT)`
- **Mecanismo:** `llvm::report_fatal_error` invocado desde `llvm::vfs::FileSystem::getBufferForFile` durante la ejecución de `MTLGPUCompilerBuildFromSourceToBuffer`.

## 2. Diagnóstico Diferencial (Lo que NO es)
- **NO es el bug de WindowServer (`_cornerMask`) de Electron (PR #48376):** Ese fallo satura WindowServer y causa ralentización global. Tu `.ips` demuestra un fallo directo en la compilación de shaders (Metal/LLVM), no en la máscara de ventanas.
- **NO es el bug `EXC_BREAKPOINT` del App Store (Issue #49522):** Tu fallo es un `SIGABRT` por aserción interna fallida de LLVM al no poder leer del Virtual File System (VFS), no una trampa del Sandbox.

## 3. Etiología (Causa Raíz)
Chrome (cuyo motor de renderizado genera operaciones WebGL/WebGPU) despacha comandos al SO para compilar shaders en tiempo de ejecución.
En macOS 26.5.2, el `MTLCompilerService` interactúa con el sistema de archivos virtual (VFS) de LLVM para leer o cachear buffers. Bajo ciertas condiciones de concurrencia o de caché corrupta, `openNativeFileForRead` falla, y LLVM entra en pánico (`fatalErrorHandler`), terminando violentamente el servicio con `SIGABRT`.
Al caer `MTLCompilerService`, Chrome pierde su aceleración de hardware abruptamente.

## 4. Mitigación Física (C5-REAL)
Dado que Chrome no hereda variables de entorno de Electron (`ELECTRON_DISABLE_GPU` es Anergía aquí), la única intervención causal es desactivar la solicitud de shaders de hardware en el origen:

### Opción A: Desactivación por UI (Chrome)
1. Abre Google Chrome.
2. Ve a `chrome://settings/system`.
3. Desactiva **"Usar aceleración de gráficos cuando esté disponible"**.
4. Reinicia Chrome.

### Opción B: Desactivación por CLI (Bypass VFS)
Arrancar Chrome forzando el renderizado por software:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --disable-gpu
```
*(Nota: Si usas VS Code/Cursor y sufres esto mismo por el renderizado de Chromium subyacente, añade `"disable-hardware-acceleration": true` en el `argv.json` mediante "Preferences: Configure Runtime Arguments").*

## 5. Cierre Epistémico
Este fallo es un defecto nativo del stack Metal/LLVM de Apple en Tahoe 26.5.2. Las ramas locales han sido contenidas mediante desactivación de GPU. La solución definitiva (Upstream) llegará previsiblemente en **macOS 26.6**. No se requiere intervención a nivel de `launchctl` ni variables de entorno globales.
