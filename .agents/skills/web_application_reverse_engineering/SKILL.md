<!-- C5-REAL EXERGY CERTIFIED -->
---
name: web_application_reverse_engineering
description: Metodología forense sistemática y kit de automatización para descompilar, auditar e interpretar la arquitectura técnica, frontend, backend, bundles JS, CSS fluido, base de datos, shaders WebGL y modelo de negocio de cualquier sitio o aplicación web.
---

# Skill: Ingeniería Inversa de Aplicaciones Web

Esta skill proporciona la guía técnica completa, herramientas CLI automatizadas y la metodología de 7 etapas para realizar ingeniería inversa forense sobre cualquier plataforma o aplicación web.

## Herramientas Auxiliares Automatizadas
1. **Auditoría General Rápida (Etapas 1 a 5)**:
   ```bash
   python3 .agents/skills/web_application_reverse_engineering/scripts/inspect_web_target.py <TARGET_URL>
   ```
2. **Generador de Informes Forenses Markdown**:
   ```bash
   python3 .agents/skills/web_application_reverse_engineering/scripts/generate_audit_report.py <TARGET_URL> <PATH_TO_HTML> [OUTPUT_MD]
   ```
3. **Descompilador de Shaders GLSL & WebGL Canvas**:
   ```bash
   python3 .agents/skills/web_application_reverse_engineering/scripts/decompile_shaders.py <PATH_TO_JS_OR_HTML>
   ```

---

## Flujo de Trabajo en 7 Etapas

### Etapa 1: Sonda Directa de Red e Infraestructura
1. **Sonda HTTP de Cabeceras**:
   ```bash
   curl -sI -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" <TARGET_URL>
   ```
2. **Identificación de CDN y Proxy**: Inspeccionar cabeceras `Server`, `X-Cache-Status`, `Vary`, `Cache-Control`, `CF-Ray`, `Server-Timing`.
3. **Descarga de HTML Inicial**: Guardar el documento en la zona de aislamiento `scratch/`:
   ```bash
   curl -s -L -H "User-Agent: Mozilla/5.0..." <TARGET_URL> -o scratch/target_raw.html
   ```

### Etapa 2: Extracción de CSS Crítico y Ecuaciones Fluidas
1. **Detección de Monolitos Inlinados**: Verificar el tamaño de los bloques `<style>` en el `<head>`. Un bloque de `> 50KB` indica una estrategia de *Zero Render-Blocking CSS*.
2. **Mapeo de Design Tokens**:
   ```python
   # Extraer variables CSS
   re.findall(r'--[a-zA-Z0-9_\-]+', css_text)
   ```
3. **Ecuaciones de Escala Tipográfica y Spacing**:
   $$\text{FontSize}(vw) = y_0 + m \cdot vw$$
   Extraer funciones `clamp(min, slope + y_intercept, max)` para validar la interpolación lineal de Viewport ($V_{min}=320\text{px}$, $V_{max}=1440\text{px}$).

### Etapa 3: Descompilación de Bundles JS, Shaders & Runtime
1. **Extracción de Scripts**: Listar todas las fuentes en `<script src="...">` y descompilar los Webpack/Vite chunks principales.
2. **Análisis de Shaders GLSL / Three.js**: Ver [referencia técnica](references/webgl_and_shader_reverse_engineering.md) para descompilar shaders de distorsión líquida y mapas de desplazamiento.
3. **Firmas Regex de Librerías Frecuentes**:
   - `GSAP`: `\bgsap\b`, `ScrollTrigger`, `TimelineMax`
   - `Three.js / WebGL`: `\bTHREE\b`, `WebGLRenderer`, `ShaderMaterial`, `createBuffer`
   - `Stimulus`: `\bStimulus\b`, `Application.start()`, `data-controller`
   - `Locomotive Scroll / Lenis`: `locomotive-scroll`, `lenis`, `requestAnimationFrame`
   - `Lottie`: `\blottie\b`, `lottie-player`, `loadAnimation`
   - `Swiper`: `swiper-slide`, `Swiper`
   - `Choices.js`: `choices__inner`, `Choices`
   - `React / Next.js`: `__NEXT_DATA__`, `react-dom`
   - `Vue / Nuxt`: `__NUXT__`, `data-v-`
   - `Alpine.js`: `x-data`, `x-init`, `x-bind`

### Etapa 4: Mapeo del DOM y Micro-Controladores
1. **Server-Side Rendering (SSR) vs. SPA Reconciliación**:
   - Si existen atributos `data-controller="..."`, `data-action="..."`, `data-target="..."` la aplicación utiliza **Stimulus.js** u **Alpine.js** acoplado sobre SSR HTML-First (Symfony, Rails, Elixir Phoenix).
   - Si existe un nodo raíz `<div id="root"></div>` o `__NEXT_DATA__`, la aplicación utiliza React/Next.js SPA/RSC.
2. **Mapeo de Acciones Interactivas**: Extraer todos los disparadores `click->controller#action`, `keyup->search#search`, etc.

### Etapa 5: Reconstrucción Backend & Modelo Relacional
1. **Identificación del Framework Backend**:
   - `Symfony`: URLs de sub-peticiones ESI `/_fragment?_hash=...&_controller=App\...`, rutas de filtro `/media/cache/thumb_...` (LiipImagineBundle).
   - `Laravel`: Cookies `XSRF-TOKEN`, `laravel_session`.
   - `Ruby on Rails`: `csrf-param`, `data-remote="true"`.
   - `Django`: `csrfmiddlewaretoken`.
2. **Modelado Entidad-Relación (ERD)**: Deducir las tablas principales (Usuarios, Entidades, Calificaciones, Transacciones) e índices de búsqueda (Elasticsearch BM25 + función de decaimiento por antigüedad).

### Etapa 6: Termodinámica & Alineación en Silicio (C-ABI)
1. **Evaluación del Límite de Landauer (Anergía vs. Exergía UI)**:
   $$\Delta Q_{\text{min}} = k_B \cdot T \cdot \ln(2) \cdot \Delta I$$
   Validar si las transformaciones visuales utilizan exclusivamente `transform: translate3d()` e `opacity` para forzar ejecución en VRAM GPU eliminando las fases de Layout/Paint del hilo principal.
2. **Especificación C-ABI de Memoria Compartida**:
   Verificar que toda estructura atómica de comunicación entre runtime y kernel esté alineada a **64 Bytes** (`#[repr(C, align(64))]`) para prevenir el *Cache-Line Splitting* y el *False Sharing*.

### Etapa 7: Transducción Comercial Enterprise
Traducir el foso técnico interno a los **4 Vectores de Valor Corporativos**:
1. **Certidumbre Legal & Compliance**: Cumplimiento del Artículo 15 de la EU AI Act y atestación de autenticidad de artefactos con recibos Merkle SHA3-256 (SCITT).
2. **Cap Contractual de Responsabilidad**: Absorción garantizada de contingencias operativas.
3. **Coste Operativo Cero en Nube**: Margen bruto $\sim 95\%+$ mediante delegación de cómputo al cliente (Zero Marginal COGS).
4. **SLA & Fail-Stop Garantizado**: Garantía determinista de latencia sub-milisegundo ($T_{\text{eff}} < 5\text{ ms}$).

---

## Recursos de Referencia
* [webgl_and_shader_reverse_engineering.md](references/webgl_and_shader_reverse_engineering.md): Guía de descompilación de shaders GLSL y contextos WebGL2.

---

## Plantilla de Informe de Auditoría (Para guardar en `scratch/audit_<domain>.md`)

```markdown
# Informe de Ingeniería Inversa: [NOMBRE_PLATAFORMA]

## 1. Stack de Infraestructura y Red
- **Servidor Web**: [Nginx / Cloudflare / Varnish / Envoy]
- **Backend Framework**: [Symfony / Next.js / Rails / Axum / Express]
- **Estrategia de Caché**: [FastCGI / Edge CDN / SWR]

## 2. Frontend & Sistema de Diseño
- **CSS Architecture**: [Inlined Monolith / Tailwind / Styled Components]
- **Interpolación Fluida**: `clamp(...)` identificados en [N] componentes.
- **Librerías de Animación**: [GSAP / Three.js / Motion / Lottie]
- **Micro-Controladores DOM**: [Stimulus / Alpine / Hydration VDOM]

## 3. Modelo Relacional & Search Index
- **Base de Datos Principal**: [PostgreSQL / MySQL / DynamoDB]
- **Motor de Búsqueda**: [Elasticsearch / Algolia / Meilisearch]

## 4. Evaluaciones de Silicio & Termodinámica
- **Compilaciones C-ABI**: Shared Manifest alineado a 64 bytes.
- **Eficiencia Exergética**: Aislamiento GPU en Compositor Layers.

## 5. Mapeo Comercial Enterprise
- **Compliance**: EU AI Act / DPA / SOC 2.
- **COGS**: Margen Bruto estimado ~95%+.
```
