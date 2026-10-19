---
name: c5-anti-slop-ui
display_name: Linter y Directivas Frontend Anti-Slop (C5-REAL)
description: Erradica el AI Slop y el pastiche estético en interfaces de usuario (WCAG AAA, escalas modulares áureas, ritmo vertical, veto al atractor grisáceo de Tailwind). Dispara con "anti-slop ui", "impeccable c5", "linter de diseño", "auditoría ui", "pulir frontend", "erradicar ai slop".
role: auditor
allowed_roles:
- auditor
- ejecutor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Directiva c5-anti-slop-ui (Erradicación del AI Slop)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only`
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Esta directiva implementa el contrapeso determinista frente al colapso de los modelos de lenguaje en el atractor medio del diseño web moderno ("AI slop": paletas grises clónicas, tipografía neutra sin jerarquía, tarjetas anidadas sin tensión visual y contraste deficiente).

---

## 1. Las Cinco Invariantes de Diseño C5-REAL

### Invariante 1: Veto al Atractor Grisáceo Clónico (Zero Neutral Gray Slop)
* **Diagnóstico:** Los LLMs tienden por defecto a generar combinaciones perezosas como `bg-zinc-950 text-zinc-400 border-zinc-800` para todo componente, creando interfaces estériles y clónicas.
* **Norma:** Toda interfaz debe poseer **personalidad cromática intencionada**:
  * Un color de acento dominante con saturación calibrada.
  * Tinte intencionado en los neutros (fondos con matices fríos, cálidos, minerales o telúricos, nunca gris puro desvitalizado).
  * Jerarquía de luminancia explícita:
    * **Titulares / Primario:** Luminancia $> 90\%$ (Dark) o $< 10\%$ (Light).
    * **Cuerpo de Texto:** Luminancia $> 75\%$ (Dark) o $< 25\%$ (Light).
    * **Metadatos y Etiquetas:** Luminancia $> 60\%$ (Dark) o $< 40\%$ (Light).

### Invariante 2: Contraste Determinista WCAG AAA (Luminancia Relativa)
* **Texto Normal ($< 18\text{pt}$ o $< 14\text{pt}$ negrita):** Ratio de contraste $\ge 7:1$.
* **Texto Grande ($\ge 18\text{pt}$ o $\ge 14\text{pt}$ negrita):** Ratio de contraste $\ge 4.5:1$.
* **Componentes Interactivos / Bordes Activos:** Ratio de contraste $\ge 3:1$ frente al fondo contiguo.
* Prohibición estricta de degradados de texto gris claro sobre fondos blancos o grises oscuros sobre fondos negros que no alcancen el umbral matemático de Chentsov-Markov.

### Invariante 3: Escala Tipográfica Modular Armónica
* Prohibición absoluta de tamaños arbitrarios dispersos (`13px`, `15px`, `17px`, `23px`).
* Todo tamaño de fuente debe pertenecer a una progresión geométrica basada en una razón modular estricta:
  * **Major Third ($r = 1.25$):** Ideal para interfaces densas de datos/dashboard:
    $$f_n = 16 \times 1.25^n \implies 10.2\text{px}, 12.8\text{px}, 16\text{px}, 20\text{px}, 25\text{px}, 31.25\text{px}$$
  * **Perfect Fourth ($r = 1.333$):** Ideal para documentación y aplicaciones de lectura:
    $$f_n = 16 \times 1.333^n \implies 12\text{px}, 16\text{px}, 21.3\text{px}, 28.4\text{px}, 37.9\text{px}$$
  * **Golden Ratio ($r = 1.618$):** Reservado para cartelería, hero sections y portadas de alta exergía.

### Invariante 4: Ritmo Espacial Base 4px / 8px
* Todo `padding`, `margin` y `gap` debe ser múltiplo estricto de $4\text{px}$ (escala $4, 8, 12, 16, 24, 32, 48, 64\text{px}$).
* Prohibido desalinear rejillas mediante offsets arbitrarios o márgenes mágicos desconectados de la retícula base.

### Invariante 5: Congruencia Somática y Accesibilidad
* Todo elemento interactivo (`<button>`, `<a>`, `<input>`) DEBE poseer estados visuales declarados:
  * `:hover` sutil y sin parpadeo.
  * `:focus-visible` con anillo de contraste alto (mínimo $2\text{px}$ visible).
  * `:active` con retroalimentación háptica/cinemática instantánea.
* Botones o enlaces compuestos únicamente por iconos (`<svg>`) DEBEN incluir obligatoriamente atributo `aria-label` descriptivo.

---

## 2. Herramienta Determinista de Auditoría en Silicio

Para auditar cualquier componente o directorio frontend sin coste de inferencia:
```bash
python3 .agents/skills/c5-anti-slop-ui/scripts/audit_ui_slop.py <ruta_archivo_o_directorio>
```

El linter analiza el árbol AST y patrones léxicos para emitir un informe de conformidad con salida estructurada y código de salida `0` (aprobado) o `1` (violación de invariantes).
