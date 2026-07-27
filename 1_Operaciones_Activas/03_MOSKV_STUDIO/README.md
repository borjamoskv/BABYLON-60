# 03_MOSKV_STUDIO

**Aplicaciones de Escritorio (Tauri), Panel Web y Forjas Multimedia**

La capa visual y de producción de contenidos del ecosistema.

## Submódulos Incluidos
- **`src-tauri/`**: Código nativo en Rust para la aplicación de escritorio Mac/Windows.
- **`portal/` / `src/`**: Interfaz de usuario en React/Vite/TypeScript.
- **`video-forge/`**: Generador y ensamblador de pipelines de vídeo.
- **`twin-forge/` & `harmony-forge/`**: Procesadores de gemelos de voz y audio.

## Modos de Uso
- Servidor web de desarrollo: `cd 1_Operaciones_Activas/03_MOSKV_STUDIO/portal && npm run dev`
- App nativa Tauri: `cd 1_Operaciones_Activas/03_MOSKV_STUDIO/src-tauri && cargo tauri dev`
