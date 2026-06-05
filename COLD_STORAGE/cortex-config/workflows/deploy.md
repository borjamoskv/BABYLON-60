---
description: "Safety rule — ALWAYS question before deploy, push, or irreversible actions"
workflow: deploy
expected_duration_min: 10
---

# 🚦 Deploy Seguro v2 — Protocolo Anti-Desastre

## Regla Absoluta

**NUNCA ejecutar directamente** ninguna acción irreversible sin confirmación explícita.

---

## Acciones Peligrosas

| Acción | Riesgo | Nivel |
|---|---|---|
| `git push` | Sube código al remote | 🟡 Medio |
| `git push --force` | DESTRUYE historial remoto | 🔴 Crítico |
| Deploy a Cloud Run / Vercel / Netlify | Producción en vivo | 🔴 Crítico |
| `npm publish` | Publica paquete público | 🔴 Crítico |
| `rm -rf` / borrado masivo | Elimina archivos | 🔴 Crítico |
| Modificar `.env` producción | Rompe servicios | 🔴 Crítico |
| DROP / DELETE en DB producción | Pérdida de datos | 🔴 Crítico |
| Modificar DNS | Puede dejar offline | 🟡 Medio |
| Revocar API keys | Rompe integraciones | 🟡 Medio |

---

## Checklist Pre-Deploy (5 Gates)

### Gate 1 — ¿Compila?
```bash
# Ejecutar build del proyecto → DEBE pasar
npm run build  # o swift build, cargo build, etc.
```

### Gate 2 — ¿Git limpio?
```bash
git status
# Si hay cambios → commit con mensaje descriptivo ANTES de deploy
```

### Gate 3 — ¿QA pasado?
- Si es UI → `/guardian` o `/qa` debe haber pasado con score ≥ 70
- Si es API → tests deben pasar
- Si es script → dry-run primero

### Gate 4 — ¿Destino correcto?
> "¿Esto va a PRODUCCIÓN, staging, o local?"
> Confirmar branch: `main`/`master` para producción

### Gate 5 — ¿Hay rollback?
> "Si algo sale mal, ¿cómo revertimos?"
> git revert, redeploy anterior, restaurar backup

---

## Formato de Confirmación (OBLIGATORIO)

```
⚠️ ACCIÓN IRREVERSIBLE

📍 Acción: [qué se va a hacer exactamente]
🎯 Destino: [producción/staging/npmjs/etc]
🌿 Branch: [branch actual]
📦 Cambios: [N commits, N archivos]
💥 Riesgo: [qué puede salir mal]
🔙 Rollback: [plan B]
✅ QA: [score del último /qa o /guardian]

¿Confirmas? (necesito un SÍ explícito)
```

---

## Acciones SEGURAS (sin confirmación)

| Acción | Por qué segura |
|---|---|
| `git add` / `git commit` | Solo local |
| `git status/log/diff/blame` | Solo lectura |
| `npm install` / `pip install` | Deps locales |
| `npm run dev` | Servidor local |
| `swift build` / `cargo build` | Compilación local |
| Health checks / QA | Solo verificación |
| Leer archivos / buscar código | Solo lectura |

---

## Post-Deploy

Después de deploy exitoso:
1. ✅ Verificar que el servicio responde
2. 📸 Screenshot si es web
3. 💾 Registrar en CORTEX como evento `deploy`
4. 🏷️ Tag en git si es release