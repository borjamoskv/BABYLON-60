---
description: "Visual QA with browser subagent — UI, responsive, animations, states"
workflow: qa
expected_duration_min: 15
---

# 🔍 QA Visual v2 — Testing PREMIUM

// turbo-all

---

## Paso 1 — Preparar entorno
1. Verificar servidor dev corriendo
2. Confirmar URL de prueba

## Paso 2 — Checklist QA (3 Viewports)

### 🖥️ Desktop (1440x900)
| # | Check | Criterio | Peso |
|---|---|---|---|
| 1 | Layout | Sin desbordamientos, sin scrollbar horizontal | 15 |
| 2 | Tipografía | Outfit/Inter cargadas, jerarquía clara | 10 |
| 3 | Colores | Paleta Moskv, contraste AA | 10 |
| 4 | Animaciones | Suaves 200-300ms, hover effects | 10 |
| 5 | Interacción | Botones/links/forms funcionales | 15 |
| 6 | Estados | Loading/error/vacío manejados | 10 |
| 7 | Imágenes | Cargadas, con alt, aspect ratio OK | 10 |
| 8 | Glassmorphism | backdrop-filter donde aplique | 5 |
| 9 | Micro-animations | Hover lifts, glow, underlines | 5 |
| 10 | Focus rings | `:focus-visible` en interactivos | 10 |

### 📱 Mobile (375x812)
| # | Check | Criterio | Peso |
|---|---|---|---|
| 1 | Responsive | Layout adaptado, no encogido | 20 |
| 2 | Navigation | Hamburger funcional | 15 |
| 3 | Touch targets | Min 44x44px | 15 |
| 4 | Scroll | Suave, sin horizontal | 15 |
| 5 | Text | Legible, min 16px body | 10 |
| 6 | Modales | No se salen de pantalla | 10 |
| 7 | Performance | lazy loading, no render blocking | 15 |

### 📱 Tablet (768x1024)
| # | Check | Criterio | Peso |
|---|---|---|---|
| 1 | Grid | Se adapta, 2-3 columnas | 25 |
| 2 | Espaciado | Sin muertos excesivos | 25 |
| 3 | Cards | Reorganización correcta | 25 |
| 4 | Navigation | Desktop o mobile, no híbrido roto | 25 |

## Paso 3 — Scoring

`Score = Σ(passed × peso) / Σ(pesos) × 100`

| Score | Nivel | Deploy? |
|---|---|---|
| 95-100 | 🏆 LEGENDARIO | Ship it! |
| 85-94 | ✅ PREMIUM | Apto |
| 70-84 | ⚠️ FUNCIONAL | Fixes recomendados |
| 50-69 | 🟠 MEDIOCRE | No deployar |
| 0-49 | ❌ INACEPTABLE | Arreglar ya |

## Paso 4 — Reporte

```
🔍 QA — COMPLETADO
📁 [URL] | 📅 [fecha]
🖥️ Desktop: [score]/100
📱 Mobile: [score]/100
📱 Tablet: [score]/100
Overall: [promedio]/100 — [nivel]
❌ Fallos: [lista]
✅ Highlights: [lista]
```

## Reglas
1. SIEMPRE 3 viewports mínimo
2. Fallos > 🟠 → corregir y re-testear
3. Score < 70 → NO apto para deploy