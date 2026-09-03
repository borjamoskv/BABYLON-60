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

**Salida:** Vuelca la receta Bash o el código React/Remotion estructurado asegurando que ninguna de estas invariantes ha sido omitida.
