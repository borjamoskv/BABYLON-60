---
description: "SHIP-Ω — Sovereign Closure Protocol. 8 C5-REAL checks or it's NOT done"
workflow: ship
expected_duration_min: 15
---

# 🚢 SHIP-Ω — Sovereign Closure Protocol (Exergy-Maximized)

// turbo-all

Protocolo terminal para declarar un proyecto CRISTALIZADO en el plano físico. Si no pasa los 8 checks, la ejecución es C4-SIM (simulación) y se RECHAZA. Cero concesiones.

---

## Paso 1 — Matriz de Cierre (8 Gates)

El proyecto DEBE superar TODOS los gates empíricamente:

```yaml
🚢 SHIP-Ω MATRIX — [Nombre_del_Proyecto]

[ ] 1. C5-REAL FUNCIONALIDAD : 0 crashes, 0 dependencias silenciosas. Ejecución verificada en hardware/API viva.
[ ] 2. DEPLOY SOBERANO     : Live en Producción (Vercel/Akash/Cloud). No es válido "funciona en mi máquina".
[ ] 3. MULTI-VECTOR AGILE  : UI (3 viewports: 375, 768, 1440) o CLI/API (3 entornos probados).
[ ] 4. EXERGY PERFORMANCE  : Lighthouse >90 O ejecución O(1)/latencia mínima probada. Entropía termodinámica purgada.
[ ] 5. MOSKV AESTHETIC     : Industrial Noir 2026. Cero prose UI. Focus rings, micro-animaciones, CLI determinista.
[ ] 6. FALSACIÓN EXTERNA   : Probado por humano ajeno o falsado (L3 Resurrection) en entorno CI estricto.
[ ] 7. CRISTALIZACIÓN (KI) : Knowledge Item o README generado (sin "prose" decorativo, solo Signal Density).
[ ] 8. GIT SENTINEL (SOTA) : `git status` limpio. Todos los cambios en remote vía Conventional Commits.
```

---

## Paso 2 — Ejecución y Verificación Determinista

### Gate 1: Funcionalidad (C5-REAL)
```bash
# Validar logs o CI tests:
pytest tests/ --verbosity=2
# O equivalente en tu stack (npm test, cargo test). Debe arrojar 100% pass rate.
```

### Gate 2: Deploy Soberano
> Declarar URL pública o registro de paquete (NPM, PyPI, Crates, Docker Hub).

### Gate 3: Multi-Vector
> Validar métricas de responsividad (browser_subagent) o tests de integración multiplataforma.

### Gate 4: Exergy Performance
```bash
# Evaluar bounds térmicos y de ejecución. Si es web:
# Lighthouse CI / PageSpeed
# Si es código puro: profiler evidence.
```

### Gate 5: Moskv Aesthetic
> Revisión de diseño UI/UX (Glassmorphism, jerarquía, contrastes HSL) o CLI UX (colors, clean stdout).

### Gate 6: Falsación Externa
> ¿Usuario confirma o hay QA automatizado (Playwright/Cypress) en verde? Si no -> BLOQUEADO.

### Gate 7: Cristalización
```bash
# Verificar existencia de artefacto de alta densidad de señal
ls -la README.md docs/overview.md || echo "❌ No Documentation"
```

### Gate 8: Git Sentinel
```bash
git status --porcelain
# DEBE retornar vacío.
git log -1 --stat
# Verificar que remote == local.
```

---

## Paso 3 — Veredicto Termodinámico

### Si 8/8 ✅:
```yaml
Estado: SHIPPED
Proyecto: [Nombre]
Sello_Temporal: [ISO8601]
Reality_Level: C5-REAL
Exergy_Yield: Positivo
Artifact_URL: [URL/Registro]
Acción: Generando Time Capsule. Purgando entropía de sesión.
```

### Si <8/8 ⛔:
```yaml
Estado: RECHAZADO (C4-SIM)
Gates_Superados: [N]/8
Fallos:
  - Gate [X]: [Justificación con Formato R2]
  - Gate [Y]: [Justificación con Formato R2]
Acción: Bloquear cierre. Requerir refactor o finalización inmediata.
```

---

## Paso 4 — Time Capsule (Solo si Shipped)

Forjar `~/.gemini/antigravity/knowledge/[nombre_proyecto_shipped]/artifacts/overview.md`:

```markdown
# 📦 Time Capsule: [proyecto]

## Resumen [R3 Signal Density]
- Target: [Qué hace]
- Stack: [Tecnologías]

## Justificación Arquitectónica [R2 Format]
Claim: Arquitectura finalizada y desplegada.
Proof: { Base: Repositorio en master/main, Range: C5-REAL, Confidence: C5 }

## Exergy Gains (Qué funcionó)
- [Decisión 1]
- [Patrón reutilizable]

## Entropic Leaks (Qué falló y se mitigó)
- [Error 1] -> [Fix]

## Próximo Estado (Post-Software)
- [Siguiente evolución]
```

---

## Paso 5 — Cristalización de CORTEX

1.  Actualizar metadatos globales (`cortex_memory_vsa.db` o CORTEX Persist).
2.  Emitir `/memoria` para archivar el contexto de la sesión actual.
3.  Terminar el agente actual o poner en Idle.

---

## Cuándo Ejecutar

- Cuando el desarrollo iterativo llega a un hito demostrable en C5-REAL.
- Obligatorio antes de cambiar radicalmente de proyecto o cerrar una iniciativa importante.
- Si el usuario requiere el fin de un ciclo (e.g. "Terminamos por hoy y sube todo").