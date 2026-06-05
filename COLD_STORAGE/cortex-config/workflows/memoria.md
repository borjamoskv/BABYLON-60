---
description: "Persist current session context to CORTEX v4 Full Ontology"
workflow: memoria
expected_duration_min: 5
---
# 💾 MEMORIA v4 — Protocolo de Persistencia por Proyecto

// turbo-all

Al finalizar sesión, cristalizar todo en el proyecto correcto.

---

## Paso 1 — Identificar Proyecto Activo

Detectar en qué proyecto se trabajó. Si se tocaron múltiples, repetir pasos 2-8 por cada uno.
Capturar conversation ID actual (disponible en `ADDITIONAL_METADATA`).

```bash
ls ~/.agent/memory/projects/
```

---

## Paso 2 — Cargar Estado del Proyecto

```bash
cat ~/.agent/memory/projects/<proyecto>.json
```

Si el archivo no existe → crearlo desde template:
```bash
cat ~/.agent/memory/projects/_template.json
```

Inferir `stack` automáticamente del repo si está vacío:
```bash
# Ejemplo: detectar lenguajes por extensión
find <path_proyecto> -maxdepth 2 -name "*.py" -o -name "*.ts" -o -name "*.sol" 2>/dev/null | \
  sed 's/.*\.//' | sort -u
```

---

## Paso 3 — Calcular Delta

| Campo | Qué actualizar | Cuándo |
|---|---|---|
| `ghost.last_task` | Última tarea ejecutada | SIEMPRE |
| `ghost.last_file` | Último archivo tocado | SIEMPRE |
| `ghost.last_conversation` | Conversation ID actual | SIEMPRE |
| `ghost.timestamp` | ISO8601 ahora | SIEMPRE |
| `recent_changes[]` | Cambios realizados (max 10, FIFO — purgar el más antiguo si overflow) | SIEMPRE |
| `known_issues[]` | Quitar resueltos, añadir nuevos | SIEMPRE |
| `pending_tasks[]` | Quitar completadas, añadir nuevas | SIEMPRE |
| `decisions[]` | Decisiones arquitectónicas | Si hubo |
| `knowledge[]` | Nuevos aprendizajes con confidence tag | Si aplica |
| `health` / `health_score` | Estado del proyecto | Si se verificó |
| `meta.last_touched` | ISO8601 ahora | SIEMPRE |

### FIFO Purge — recent_changes

Si `recent_changes[]` tiene ≥10 items antes de añadir → eliminar el item más antiguo (índice final).

---

## Paso 4 — Conflict Detection

Antes de guardar, verificar:

1. Leer `decisions[]` existentes del proyecto
2. Comparar con acciones de esta sesión
3. Si hay contradicción → alertar:

```
⚠️ CONFLICTO: Decisión "No usar SQLite" vs acción "añadiste sqlite3.connect()"
   → ¿Crear #revision o revertir?
```

---

## Paso 5 — Error Memory (con dedup guard)

Si en esta sesión se cometieron errores REALES, verificar primero que no están ya registrados:

```bash
# Check duplicado antes de añadir
grep -F "<descripción del error>" ~/.agent/memory/mistakes.jsonl && echo "⚠️ YA EXISTE — VERGÜENZA" || \
echo '{"ts":"<ISO8601>","project":"<id>","error":"<qué falló>","root_cause":"<por qué>","fix":"<solución probada>","severity":"<critical|high|medium|low>","tags":["#tag1"]}' >> ~/.agent/memory/mistakes.jsonl
```

Reglas:
- Solo errores REALES, no typos
- Root cause OBLIGATORIO
- Fix debe estar PROBADO antes de escribir
- Si el error ya existe → NO registrar, pero documentar que se repitió en `ghost.last_task`

---

## Paso 6 — Bridges (Cross-Project)

Registrar si cualquiera de estas condiciones es verdadera:

- [ ] Un patrón resuelto aquí existe como problema abierto en otro proyecto
- [ ] Una decisión arquitectónica aquí contradice una decisión en otro proyecto
- [ ] Un bug encontrado aquí puede manifestarse en otro proyecto del mismo stack

```bash
echo '{"ts":"<ISO8601>","from":"<proyecto-origen>","to":"<proyecto-destino>","tag":"<patrón>","note":"<descripción>"}' >> ~/.agent/memory/bridges.jsonl
```

Si ninguna condición es verdadera → saltar explícitamente con `# BRIDGES: ninguno esta sesión`.

---

## Paso 7 — Ghost Update

Actualizar `ghosts.json` — incluir `last_conversation`:

```bash
# Editar la entrada del proyecto activo con:
# - last_task: qué estabas haciendo (verbatim, accionable)
# - last_file: último archivo tocado (path relativo al proyecto)
# - last_conversation: conversation ID de la sesión
# - timestamp: ISO8601 ahora
cat ~/.agent/memory/ghosts.json
```

---

## Paso 8 — System Log (con FIFO guard)

Añadir entrada de sesión al log global:

```bash
# Añadir a sessions_log[] — verificar longitud primero
python3 -c "
import json, sys
f = '$HOME/.agent/memory/system.json'
d = json.load(open(f))
log = d.get('sessions_log', [])
if len(log) >= 30:
    log.pop()  # FIFO: eliminar el más antiguo
log.insert(0, {
    'date': '<ISO8601>',
    'project': '<id>',
    'focus': '<tema>',
    'duration_approx': '<Xh>',
    'key_output': '<output clave>',
    'conversation_id': '<conv-id>'
})
d['sessions_log'] = log
d['last_updated'] = '<ISO8601>'
json.dump(d, open(f, 'w'), indent=2, ensure_ascii=False)
print('✅ System log actualizado')
"
```

---

## Paso 9 — Persistir y Validar JSON

```bash
python3 -c "import json; json.load(open('$HOME/.agent/memory/projects/<id>.json')); print('✅ Proyecto OK')"
python3 -c "import json; json.load(open('$HOME/.agent/memory/system.json')); print('✅ Sistema OK')"
python3 -c "import json; json.load(open('$HOME/.agent/memory/ghosts.json')); print('✅ Ghosts OK')"
```

---

## Paso 10 — Git Sentinel (R4)

Ejecutar SIEMPRE después de cristalizar:

```bash
git -C <path_proyecto> status --short 2>/dev/null || echo "No es repo git"
```

Si dirty state detectado → proponer Conventional Commit:
```bash
git -C <path_proyecto> add -A && git -C <path_proyecto> commit -m "chore(cortex): crystallize session delta [/memoria]"
```

---

## Paso 11 — Snapshot (guard: solo si han pasado ≥7 días)

```bash
python3 -c "
import os, time, glob
snaps = sorted(glob.glob(os.path.expanduser('~/.agent/memory/snapshots/system_*.json')))
if snaps:
    last = os.path.basename(snaps[-1]).replace('system_','').replace('.json','')
    last_ts = time.mktime(time.strptime(last, '%Y%m%d'))
    days = (time.time() - last_ts) / 86400
    print(f'Último snapshot: {last} ({days:.1f} días)')
    if days < 7:
        print('⏭ Snapshot omitido (< 7 días)')
        exit(0)
else:
    print('No hay snapshots previos')
import shutil, datetime
dst = os.path.expanduser(f'~/.agent/memory/snapshots/system_{datetime.date.today().strftime(\"%Y%m%d\")}.json')
shutil.copy(os.path.expanduser('~/.agent/memory/system.json'), dst)
print(f'📸 Snapshot creado: {dst}')
"
```

---

## Paso 12 — Diff Visual (con conversation ID)

```
💾 CORTEX v4 UPDATE — <ISO8601>

🔗 Conversation: <conv-id>
📁 [proyecto]:
  👻 Ghost: "<última tarea>"
  📄 Last file: <archivo>
  + changes: "<cambio 1>", "<cambio 2>"
  - issues resueltos: "<issue>" ✅
  ⚠️  issues nuevos: "<issue>"
  🧠 decisions: "<decisión>"
  ~ health: <before> → <after>

❌ Errores registrados: +<N>
🔗 Bridges creados: +<N>
📅 Sesión: <duración> — "<resumen>"

✅ Persistido y validado. Git: <clean|dirty→committed>
```

---

## Cuándo Ejecutar

- Al final de cada sesión productiva (≥2 cambios)
- Cuando el usuario diga `/memoria`
- Después de un `/mejoralo`
- Después de deploy
- **ANTES DE CERRAR** si hubo trabajo significativo

## Changelog

| Versión | Cambio |
|---|---|
| v4.0 | Snapshot guard 7 días (evita inflation) |
| v4.0 | `ghost.last_conversation` — trazabilidad completa hacia conv ID |
| v4.0 | FIFO purge explícito en `recent_changes[]` y `sessions_log[]` |
| v4.0 | Dedup guard en Error Memory (grep antes de append) |
| v4.0 | R4 Git Sentinel integrado como Paso 10 obligatorio |
| v4.0 | Bridges con checklist heurística — ya no se puede "saltar sin razón" |
| v4.0 | Diff visual con `conversation_id` y `git` status |
| v4.0 | Stack auto-inferencia en Paso 2 |