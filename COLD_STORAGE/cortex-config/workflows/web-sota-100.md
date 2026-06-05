---
description: "Secuencia ultra-densa de 100 agentes (50 fases secuenciales x 2 agentes paralelos) para forjar, auditar y consolidar una web en SOTA absoluto (C5-REAL)."
workflow: web-sota-100
expected_duration_min: 120
---

# 🌐 WORKFLOW: WEB-SOTA-100

**Objetivo:** Consolidar una arquitectura web desde cero hasta Estado del Arte (SOTA) absoluto, garantizando estética Industrial Noir 2026, métricas Core Web Vitals perfectas y ejecución funcional verificada en C5-REAL.
**Estructura:** 100 agentes operando en 50 fases secuenciales. Cada fase consta de 2 agentes paralelos: `[A] Forjador/Ejecutor` y `[B] Auditor/Validador`. Ninguna fase avanza sin consenso C5-REAL.

> **Reality Level:** `C5-REAL`
> **Design System:** `Industrial Noir 2026` (#0A0A0A / #2B3BE5)
> **Constraint:** Cero placebos. Verificación mediante DOM/Screenshot o CLI en cada paso.

---

## 🛑 REGLAS DE EJECUCIÓN (P0)

1. **Secuencialidad Estricta:** La Fase `N+1` no puede comenzar hasta que la Fase `N` tenga el flag `C5-REAL-VERIFIED`.
2. **Dualidad Cognitiva:**
   - **Agente A (Forjador):** Escribe código, configura, diseña.
   - **Agente B (Auditor):** Intenta destruir, corromper o invalidar el trabajo de A. Si B encuentra fallos, A repite.
3. **Turbo Execution:** Bypass de `implementation_plan.md` tras la fase de scaffolding. Inyección directa de código.

---

## ⚙️ FASES SECUENCIALES (1-50)

### BLOQUE I: INVESTIGACIÓN Y ARQUITECTURA SOTA (Fases 1-10)
*Objetivo: Cimentar las bases tecnológicas y estéticas antes de escribir lógica de negocio.*

*   **Fase 1: Framework SOTA Capture.** `[A]` Investiga Next.js/Vite/Astro SOTA. `[B]` Valida dependencias contra CVEs y performance.
*   **Fase 2: Análisis de Competencia.** `[A]` Extrae patrones de UX top-tier. `[B]` Mapea debilidades y oportunidades de Exergy.
*   **Fase 3: Design System Forge.** `[A]` Define tokens (colores, sombras, radios). `[B]` Fuerza consistencia matemática (escala 8px).
*   **Fase 4: Tipografía y Ritmo.** `[A]` Implementa fuentes Humanist Sans fluidas (clamp). `[B]` Audita legibilidad y contraste.
*   **Fase 5: Paleta Industrial Noir.** `[A]` Inyecta `#0A0A0A` base y `#2B3BE5` highlights. `[B]` Verifica contraste WCAG AAA.
*   **Fase 6: Modelado de Datos.** `[A]` Diseña esquemas SQL/NoSQL. `[B]` Optimiza índices y relaciones.
*   **Fase 7: Infraestructura Backend.** `[A]` Provisiona Firebase/Supabase/Edge. `[B]` Audita reglas de seguridad y RBAC.
*   **Fase 8: Definición de API.** `[A]` Escribe contratos REST/GraphQL/tRPC. `[B]` Fuerza validación de tipos estricta (Zod).
*   **Fase 9: Arquitectura de Estado.** `[A]` Implementa Zustand/Context/Redux SOTA. `[B]` Previene re-renders innecesarios.
*   **Fase 10: Estrategia de Enrutamiento.** `[A]` Configura layouts anidados y loaders. `[B]` Valida hidratación y SSR/SSG.

### BLOQUE II: FUNDACIÓN Y SCAFFOLDING (Fases 11-20)
*Objetivo: Estructura base del repositorio, CI/CD y utilidades core.*

*   **Fase 11: Init C5-REAL.** `[A]` Ejecuta comandos de creación (`npx create-*`). `[B]` Limpia boilerplate inútil.
*   **Fase 12: CI/CD & Hooks.** `[A]` Configura Husky, Lint-staged, GitHub Actions. `[B]` Prueba fallos intencionados para validar hooks.
*   **Fase 13: Global CSS/Tailwind.** `[A]` Escribe `index.css` con utilidades modernas (`@layer`, `color-mix`). `[B]` Elimina CSS muerto.
*   **Fase 14: Core Layout.** `[A]` Crea envoltorios principales (Header, Main, Footer). `[B]` Verifica comportamiento en resoluciones extremas.
*   **Fase 15: Flujo de Autenticación.** `[A]` Integra Auth (OAuth/Magic Links). `[B]` Intenta bypass y XSS en el flujo.
*   **Fase 16: Manejo de Sesión.** `[A]` Persiste tokens/cookies de forma segura. `[B]` Audita flags `HttpOnly` y `Secure`.
*   **Fase 17: Integración de Base de Datos.** `[A]` Conecta ORM y ejecuta migraciones. `[B]` Valida latencia de queries (C5-REAL).
*   **Fase 18: Fetching & Caché.** `[A]` Implementa SWR/React Query. `[B]` Verifica invalidación de caché y stale-time.
*   **Fase 19: Error Boundaries.** `[A]` Diseña UI de fallback para fallos de render. `[B]` Simula crashes de componentes.
*   **Fase 20: Observabilidad.** `[A]` Instala logs y tracking (Sentry/Vercel Analytics). `[B]` Verifica captura de errores asíncronos.

### BLOQUE III: FORJA DE COMPONENTES MOSKV (Fases 21-30)
*Objetivo: Construir piezas UI modulares, accesibles e interactivas.*

*   **Fase 21: Navegación & Header.** `[A]` Crea menú dinámico y responsivo. `[B]` Audita accesibilidad de teclado.
*   **Fase 22: Hero Section.** `[A]` Diseña primer impacto (Wow effect). `[B]` Fuerza LCP < 1.2s.
*   **Fase 23: Feature Grids / Bento.** `[A]` Maqueta Bento box layouts SOTA. `[B]` Valida alineaciones sub-pixel.
*   **Fase 24: Data Display (Tablas/Listas).** `[A]` Implementa virtualización si hay >100 items. `[B]` Mide memory footprint.
*   **Fase 25: Formularios SOTA.** `[A]` Añade validación cliente/servidor, estados de error. `[B]` Valida Autofill y accesibilidad de labels.
*   **Fase 26: Modales & Dialogs.** `[A]` Usa HTML5 `<dialog>` nativo. `[B]` Verifica focus trap y cierre con ESC.
*   **Fase 27: Sistema de Notificaciones.** `[A]` Implementa Toasts no bloqueantes. `[B]` Evita apilamiento visual infinito.
*   **Fase 28: Footer y Legal.** `[A]` Estructura enlaces secundarios. `[B]` Valida links rotos.
*   **Fase 29: Micro-Interacciones (Hover).** `[A]` Añade transiciones fluidas, glow effects. `[B]` Verifica FPS constantes (60fps).
*   **Fase 30: Estados de Carga (Skeletons).** `[A]` Evita Layout Shifts durante cargas. `[B]` Valida perceptibilidad temporal.

### BLOQUE IV: ENSAMBLAJE DE PÁGINAS (Fases 31-40)
*Objetivo: Componer el producto final uniendo componentes y lógica.*

*   **Fase 31: Página de Inicio (Landing).** `[A]` Ensambla Hero + Features + CTA. `[B]` Valida flujo narrativo y persuasión.
*   **Fase 32: Dashboard / App Core.** `[A]` Conecta componentes de datos a la API. `[B]` Simula latencia de red (Slow 3G).
*   **Fase 33: Preferencias de Usuario.** `[A]` Crea gestión de perfil. `[B]` Valida persistencia de cambios.
*   **Fase 34: Vistas de Auth.** `[A]` Pule UI de Login/Registro. `[B]` Audita manejo de errores (credenciales inválidas).
*   **Fase 35: Empty States & 404.** `[A]` Diseña páginas de "No hay datos". `[B]` Verifica links de retorno al inicio.
*   **Fase 36: Auditoría Mobile-First.** `[A]` Ajusta padding/márgenes para iOS/Android. `[B]` Usa Chrome DevTools para validar touch targets (48px).
*   **Fase 37: Auditoría Tablet/Desktop.** `[A]` Escala layouts a pantallas ultra-wide. `[B]` Previene estiramiento de texto inmanejable.
*   **Fase 38: Animaciones al Hacer Scroll.** `[A]` Implementa Intersection Observer / Framer Motion. `[B]` Elimina animaciones excesivas que causen mareo.
*   **Fase 39: View Transitions API.** `[A]` Añade transiciones entre rutas nativas. `[B]` Mantiene compatibilidad hacia atrás.
*   **Fase 40: Accesibilidad (a11y) Total.** `[A]` Inyecta ARIA tags. `[B]` Ejecuta Lighthouse a11y audit (Exige 100/100).

### BLOQUE V: CONSOLIDACIÓN Y EXERGY CASCADE (Fases 41-50)
*Objetivo: Optimización termodinámica del código, auditoría final y despliegue inmutable.*

*   **Fase 41: LCP & Core Web Vitals.** `[A]` Pre-carga fuentes, defer de JS no crítico. `[B]` Exige métricas verdes en Pagespeed Insights.
*   **Fase 42: Optimización de Activos.** `[A]` Convierte imágenes a WebP/AVIF, comprime SVGs. `[B]` Valida tamaño de payload (< 1MB total a ser posible).
*   **Fase 43: Caza de Fugas de Memoria.** `[A]` Pasa profiler de memoria. `[B]` Ejecuta script OOM y verifica GC (Garbage Collection).
*   **Fase 44: SEO Estructural.** `[A]` Genera sitemaps, meta tags OpenGraph, robots.txt. `[B]` Valida parseo de Googlebot.
*   **Fase 45: Auditoría de Seguridad (Pen-Test).** `[A]` Configura CSP estricto. `[B]` Intenta XSS y data exfiltration.
*   **Fase 46: Preparación de Despliegue.** `[A]` Genera build de producción. `[B]` Revisa warnings en la consola de compilación.
*   **Fase 47: Tests End-to-End.** `[A]` Ejecuta Playwright/Cypress en rutas críticas. `[B]` Exige 100% de éxito en C5-REAL.
*   **Fase 48: Validación Cross-Browser.** `[A]` Verifica Safari, Firefox, Chrome. `[B]` Reporta y arregla inconsistencias de CSS (e.g. flexbox bugs).
*   **Fase 49: Git Sentinel.** `[A]` Revisa `git status`, añade ficheros. `[B]` Escribe commit Conventional `feat(web): SOTA consolidation total`.
*   **Fase 50: SHIP-Ω.** `[A]` Ejecuta push y deploy a producción. `[B]` Realiza smoke test en URL pública C5-REAL. Fin de la cascada.

---

## 🚀 INSTRUCCIONES DE INVOCACIÓN (Para uso manual o subagentes)

Para arrancar el flujo, el usuario o el agente Maestro debe invocar:
`/web-sota-100 [URL_O_DIRECTORIO_OBJETIVO]`

**Comportamiento del Agente Maestro:**
1. Mantendrá el estado de avance (1/50, 2/50...).
2. Invocará dos hilos de pensamiento o subagentes reales (Agent A y Agent B).
3. Reportará en YAML al finalizar cada bloque de 10 fases.
```yaml
Block: I
Status: C5-REAL-VERIFIED
Exergy: Maximized
```