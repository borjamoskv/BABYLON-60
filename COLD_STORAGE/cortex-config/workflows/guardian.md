---
description: Visual Multi-viewport Audit, UI Auto-Healing, Moskv Aesthetic Enforcement
---
// turbo-all
# 🛡️ The Guardian v2 (El Guardián Vitaminado)

Este flujo utiliza el Browser Subagent + análisis de código para detectar, diagnosticar y corregir errores visuales automáticamente.

---

## Paso 1 — Objetivo Visual

- Preguntar URL o usar el proyecto activo de CORTEX
- Default viewport: Desktop (1440x900)
- También testear: Mobile (375x812), Tablet (768x1024)

---

## Paso 2 — Auditoría Visual Completa (Browser Subagent)

### 2A — Desktop (1440x900)

```
Task: Navegar a [URL]. Hacer screenshot de la página completa.
Verificar:
1. ¿Hay scroll horizontal? (FALLO CRÍTICO)
2. ¿Hay elementos desbordados o cortados?
3. ¿Hay superposiciones de elementos?
4. ¿Los textos son legibles?
5. ¿Las imágenes están cargadas?
6. ¿Los hovers funcionan? (mover cursor sobre botones/links)
7. ¿Las animaciones son suaves? (scroll down/up)
Return: Lista de problemas encontrados con su ubicación en la página.
```

### 2B — Mobile (375x812)

```
Task: Resize a 375x812. Navegar a [URL]. Hacer screenshot.
Verificar:
1. ¿El layout se adapta o solo se encoge?
2. ¿Hay menu hamburguesa si el nav tiene muchos items?
3. ¿Los touch targets son >= 44x44px?
4. ¿El texto es legible sin zoom? (min 16px)
5. ¿No hay modales/popups que se salgan de la pantalla?
Return: Lista de problemas responsive.
```

### 2C — Tablet (768x1024)

```
Task: Resize a 768x1024. Navegar a [URL]. Hacer screenshot.
Verificar:
1. ¿El grid se adapta correctamente?
2. ¿No hay espacios muertos excesivos?
3. ¿Las cards/galerías se reorganizan bien?
Return: Lista de problemas de breakpoint intermedio.
```

---

## Paso 3 — Auditoría de Código CSS

Complementar lo visual con análisis de código:

```bash
# 1. Colores prohibidos (Moskv Aesthetic)
grep -rn '#ccc\|#999\|#666\|#888\|#fff\b\|#fafafa\|color: red\|color: blue\|color: green' --include='*.css' .

# 2. !important (prohibido salvo overrides de libs)
grep -rn '!important' --include='*.css' .

# 3. Inline styles (prohibidos)
grep -rn 'style="' --include='*.html' .

# 4. Selectores > 3 niveles
grep -rn '[a-z] .*[a-z] .*[a-z] .*[a-z] {' --include='*.css' .

# 5. Fonts correctas (Outfit, Inter, JetBrains Mono)
grep -rn 'font-family' --include='*.css' . | grep -v 'Outfit\|Inter\|JetBrains\|system-ui\|sans-serif\|monospace'

# 6. Variables CSS missing
grep -rn 'var(--' --include='*.css' . | head -20

# 7. Transiciones en interactivos
grep -rn ':hover' --include='*.css' . | head -20
```

---

## Paso 4 — Enforcement de Moskv Aesthetic

Checklist automático basado en `moskv-aesthetic` skill:

| # | Check | Criterio | Auto-fix? |
|---|---|---|---|
| 1 | Fondo oscuro | `#000` o `#0a0a0a` | ✅ Sí |
| 2 | Fonts importadas | Google Fonts link presente | ❌ Manual |
| 3 | Glassmorphism | `backdrop-filter: blur()` donde hay profundidad | ❌ Manual |
| 4 | Hover en interactivos | `transition` + `transform` | ✅ Sí |
| 5 | Focus ring | `:focus-visible` presente | ✅ Sí |
| 6 | Colores de paleta | Solo variables `--accent-*`, `--danger-*` | ✅ Sí |
| 7 | Skeleton loaders | Shimmer en vez de spinners | ❌ Manual |
| 8 | `prefers-reduced-motion` | Media query presente | ✅ Sí |
| 9 | Grain texture | `::after` con noise en background | ❌ Manual |
| 10 | Glow en elementos activos | `box-shadow` con opacidad baja | ✅ Sí |

---

## Paso 5 — Auto-Healing

Para cada problema encontrado:

1. **Clasificar severidad**: 🔴 Crítico / 🟡 Medio / 🟢 Cosmético
2. **Proponer fix**: CSS/HTML/JS concreto
3. **Si el usuario aprueba** (o si es cosmético) → aplicar con `replace_file_content`
4. **Re-verificar**: Refresh del Browser Subagent para confirmar

---

## Paso 6 — Reporte Guardián

```
🛡️ GUARDIAN REPORT — [URL]

📊 Score Moskv Aesthetic: [X/100]

🖥️ Desktop (1440x900):
  ✅ Layout OK | ❌ 2 issues

📱 Mobile (375x812):
  ✅ Responsive OK | ⚠️ 1 warning

🎨 CSS Audit:
  ✅ 0 colores prohibidos
  ⚠️ 2 !important encontrados
  ✅ 0 inline styles

🛡️ Moskv Compliance: 8/10 checks passed

🔧 Auto-fixes aplicados: [N]
⚠️ Fixes manuales pendientes: [N]

Estado: ✅ PREMIUM | ⚠️ Necesita trabajo | ❌ Inaceptable
```

---

## Uso

```bash
/guardian [url] [instrucción_opcional]
```

Si no se da URL, usar el servidor dev activo detectado en los terminales corriendo.
