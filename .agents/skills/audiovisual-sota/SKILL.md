---
name: audiovisual-sota
description: Fuerza invariantes extremas en pipelines de renderizado audiovisual (FFmpeg/Remotion).
---

# Directiva audiovisual-sota

Cuando el usuario invoque `/audiovisual-sota`, aplicarás el protocolo de alta densidad visual para la generación o edición de código FFmpeg o componentes Remotion/Revideo.

## Invariantes Forzosas
1. **Audio Estéreo Compulsorio:** Todo pipeline de audio generado DEBE incluir `-ac 2` o `pan=stereo|c0=c0|c1=c0`.
2. **Zero-Disk Piping:** Prohíbe escribir frames intermedios en disco. Fuerza el pipeline `stdin` hacia FFmpeg: `-f image2pipe -vcodec png -i -`.
3. **Apilamiento Espectral Reactivo:** Si hay audio-reacción, exige componer sobre la marcha `showspectrum` y `showwaves`.
4. **Cinemática de Muelle (Remotion):** Está prohibido el uso de transiciones lineales puras. El código React debe forzar el uso de `spring()` con desfasaje temporal ($\Delta t$) para cada elemento (Staggered Spring Physics).
5. **Zero-Bare Visuals:** Ningún render puede ser solo el audio; debe tener la capa completa de UI (carteles, subtítulos).
6. **Límite Termodinámico de Hardware (M-Series 18GB):** NUNCA utilices `--concurrency=100%` en comandos de Remotion o Puppeteer pesados. Fuerza siempre un máximo de `--concurrency=2` o `--concurrency=4` para no saturar la Memoria Unificada del Mac. Añade sistemáticamente el flag `--timeout=120000` a los renders CLI para evitar abortos en frío del bundler de Vite/Webpack.
7. **Protocolo LAMP (Language-Assisted Motion Planning):** La física de las animaciones `spring()` no puede estar hardcodeada permanentemente. El LLM (Orquestador) DEBE calcular variables dinámicas (como `mass`, `damping` y `stiffness`) basándose en la gravedad semántica del guion (ej: masa alta para temas densos/burocráticos, masa baja para temas ágiles).
8. **Estética SOTA 2026 (Brutalismo Matemático / Vercel-Style):** Prohibido el uso de imágenes rasterizadas (PNG/JPG). Fondos con negros absolutos (`#030303` o `#000000`) combinados con grids matemáticos. Dominancia del rigor científico usando fuentes `monospace`. Uso intenso de `radial-gradient` y `blur()` para generar Glows reactivos por debajo de la interfaz.

**Salida:** Vuelca la receta Bash o el código React/Remotion estructurado asegurando que ninguna de estas invariantes ha sido omitida.
