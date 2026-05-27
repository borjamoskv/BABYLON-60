---
description: Forge complete web projects with YInMn design tokens and Impact Patterns
---

# 🔨 /forjar — Crear Proyecto Web

// turbo-all

Forjar un proyecto web completo desde cero.

---

## Uso

```
/forjar "[nombre]" --para [quién] --sentir [emoción] --nivel [tech]
```

| Param | Valores | Default |
|---|---|---|
| `--sentir` | asombro, confianza, emoción, calma, lujo, urgencia | asombro |
| `--nivel` | bajo (CSS), medio (JS+CSS), alto (WebGL/shaders) | medio |
| `--para` | Descripción del público/cliente | - |

## Paso 1 — Anti-Pattern Check

```bash
grep -i "tags.*$(echo $EMOCION)" ~/.agent/memory/mistakes.jsonl
```

Si hay errores previos con esos tags → mostrar antes de empezar.

## Paso 2 — Seleccionar Impact Patterns

Leer `~/.agent/memory/webs/patterns.json`

Filtrar por:
1. `emotion` incluye la emoción target
2. `complexity` compatible con `--nivel`
3. `fitness` > 0.7

Seleccionar 3 patterns y mostrar:

```
🎯 PATTERNS SELECCIONADOS para "asombro":
   IMP-001 Kinetic Typography (fitness: 0.90)
   IMP-005 Reveal on Scroll (fitness: 0.95)
   IMP-002 Magnetic Depth (fitness: 0.85)
```

## Paso 3 — Crear Estructura

```
[nombre]/
├── index.html          ← Semántico, ARIA, meta SEO
├── css/
│   ├── tokens.css      ← Design tokens YInMn
│   ├── reset.css       ← Reset mínimo
│   ├── layout.css      ← Grid/Flex base
│   ├── components.css  ← Componentes
│   └── animations.css  ← Micro-animations + patterns
├── js/
│   ├── main.js         ← Entry point
│   ├── observers.js    ← IntersectionObserver, scroll
│   └── interactions.js ← Hover, click, tilt
├── assets/
│   ├── images/
│   └── fonts/
└── README.md           ← Con runbook
```

## Paso 4 — Generar tokens.css

```css
:root {
  /* YInMn Blue System */
  --color-primary: #2E5090;
  --color-primary-dark: #1A3A6E;
  --color-primary-light: #4A7BC8;
  --color-accent: #FF6B35;
  --color-bg: #0A0F1E;
  --color-surface: #F4F6F8;
  --color-text: #E8E8E8;
  --color-text-muted: #8899AA;

  /* Typography */
  --font-display: 'Outfit', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-code: 'JetBrains Mono', monospace;

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;
  --space-2xl: 8rem;

  /* Easing */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Transitions */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast: 0ms;
    --duration-normal: 0ms;
    --duration-slow: 0ms;
  }
}
```

## Paso 5 — Crear Proyecto en CORTEX

Crear `~/.agent/memory/projects/[nombre].json` desde template.
Registrar ghost en `ghosts.json`.

## Paso 6 — Mostrar Dashboard

```
┌─ WEBS+ FORJADO ────────────────────────┐
│  Proyecto: [nombre]                     │
│  Emoción:  [target]                     │
│  Patterns: IMP-001, IMP-005, IMP-002    │
│  Archivos: 9 creados                    │
│  Runbook:  npx serve . -l 3000          │
│  Status:   🟢 Listo para /impactar      │
└─────────────────────────────────────────┘
```
