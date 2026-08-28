<!-- C5-REAL EXERGY CERTIFIED -->
# Referencia Técnica: Ingeniería Inversa de WebGL, Shaders GLSL y Post-Processing

Esta referencia detalla el procedimiento de descompilación y análisis de efectos WebGL en sitios web galardonados.

## 1. Detección del Canvas & Contexto WebGL
Al inspeccionar el DOM o bundles compilados, identificar la inicialización del contexto:
```javascript
const canvas = document.querySelector('canvas');
const gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
```

## 2. Anatomía de un Shader de Distorsión Líquida (Displacement Mapping)

### Vertex Shader (GLSL ES 1.00 / 3.00)
Calcula las coordenadas de vértice e inyecta la posición del cursor o progreso de scroll:
```glsl
attribute vec3 position;
attribute vec2 uv;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

varying vec2 vUv;

void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
```

### Fragment Shader (GLSL ES 1.00 / 3.00)
Mapea la mezcla de texturas con deformación por mapa de ruido/desplazamiento:
```glsl
precision highp float;

uniform sampler2D u_texture1;
uniform sampler2D u_texture2;
uniform sampler2D u_map;
uniform float u_progress;

varying vec2 vUv;

void main() {
    vec4 mapColor = texture2D(u_map, vUv);
    vec2 distortedUv = vec2(
        vUv.x + mapColor.r * u_progress,
        vUv.y + mapColor.g * u_progress
    );
    vec4 c1 = texture2D(u_texture1, distortedUv);
    vec4 c2 = texture2D(u_texture2, distortedUv);
    gl_FragColor = mix(c1, c2, u_progress);
}
```

## 3. Estrategias de Desoptimización e Inspección
1. **Hooking en `gl.shaderSource`**: Interceptar en tiempo de ejecución las llamadas a `gl.shaderSource(shader, source)` mediante extensiones de desarrollo WebGL (ej. Chrome WebGL Inspector / Spector.js).
2. **Destrucción de Contextos para Evitar Leaks**:
   ```javascript
   const loseContext = gl.getExtension('WEBGL_lose_context');
   if (loseContext) loseContext.loseContext();
   ```
