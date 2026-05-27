---
description: Obsessive refinement — micro-animations, performance, a11y, Core Web Vitals
---

# ✨ /pulir — Refinamiento Obsesivo

// turbo-all

Convertir lo bueno en excelente.

---

## Uso

```
/pulir [alcance] --auditar [perf|a11y|visual|todo]
```

| Alcance | Qué cubre |
|---|---|
| `general` | Todo el proyecto |
| `[sección]` | Solo esa sección |
| `[archivo]` | Solo ese archivo |

## Paso 1 — Audit Visual

- [ ] Jerarquía tipográfica consistente
- [ ] Spacing con tokens (no valores mágicos)
- [ ] Colores del sistema YInMn (no hex sueltos)
- [ ] Hover states en todo lo interactivo
- [ ] Focus visible en todo lo focusable
- [ ] Transiciones con easing curves del sistema
- [ ] Stagger delays donde hay listas/grids

## Paso 2 — Audit Performance

```bash
# Lighthouse CLI si disponible
npx lighthouse [url] --output json --quiet
```

Verificar:
- [ ] LCP < 2.5s
- [ ] CLS < 0.1
- [ ] FID < 100ms
- [ ] CSS crítico inline
- [ ] Imágenes: WebP, lazy-loading, srcset
- [ ] Fonts: preload, font-display: swap
- [ ] JS: defer/async, no blocking

## Paso 3 — Audit A11Y

- [ ] Contraste ≥ 4.5:1 (texto normal), ≥ 3:1 (texto grande)
- [ ] `alt` en todas las imágenes (descriptivo, no filename)
- [ ] ARIA labels en elementos interactivos
- [ ] Heading hierarchy (h1 > h2 > h3, sin saltos)
- [ ] Skip navigation link
- [ ] `prefers-reduced-motion` en todas las animaciones
- [ ] Tab order lógico
- [ ] Role attributes donde corresponde

## Paso 4 — Micro-Animations Polish

Revisar cada animación:

| Check | Criterio |
|---|---|
| Anticipación | ¿Hay movimiento preparatorio? (scale 0.98 antes de 1.0) |
| Follow-through | ¿El final tiene overshoot sutil? (ease-spring) |
| Stagger | ¿Los elementos en grupo tienen delay secuencial? |
| Duración | 150-300ms para UI, 300-500ms para decorativo |

## Paso 5 — Generar Reporte

```
✨ POLISH REPORT:
   ┌───────────────────────┐
   │ Visual:    9/10  (+1) │
   │ Performance: 92  (+5) │
   │ A11Y:       98  (+8)  │
   │ Motion:    8/10  (+2) │
   └───────────────────────┘
   
   Fixes aplicados: 7
   Mejoras sugeridas pendientes: 2
   
   "Si algo no es accesible, no es bello" ✓
```
