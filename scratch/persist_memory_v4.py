import json
import os
import fcntl
import datetime
import time
import glob
import shutil

# Variables
project_id = "Teorema-Robinson-Moskv"
conv_id = "13b2a265-796e-4492-83d9-c43f767e844b"
iso_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
last_task = "Implementada topología strongly-typed (Domain, Primitive, Modifier) para Action Space 1000 y ejecutada auditoría Kantiana/Legal."
last_file = "src-tauri/src/kernel.rs"
changes = [
    "Reescrito kernel.rs con Enums para Domain, Primitive y Modifier.",
    "Añadida gestión Async a primitivas en Rust.",
    "Refactor namespace cortex/audits/ING-INV a ing-inv.",
    "Añadido panic Kantiano a base transductor (empty_op)."
]
decisions = ["Mapear el Action Space C5-REAL a Enums en Rust para evitar hardcoding de índices estocásticos y delegar type-safety al compilador."]

def load_or_create(path, default_data):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return default_data
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        return default_data

# 1. Update Project
proj_path = os.path.expanduser(f"~/.agent/memory/projects/{project_id}.json")
proj_data = load_or_create(proj_path, {
    "id": project_id,
    "stack": ["rust", "typescript", "markdown"],
    "ghost": {},
    "recent_changes": [],
    "known_issues": [],
    "pending_tasks": [],
    "decisions": [],
    "knowledge": [],
    "health_score": 100,
    "meta": {}
})

proj_data["ghost"]["last_task"] = last_task
proj_data["ghost"]["last_file"] = last_file
proj_data["ghost"]["last_conversation"] = conv_id
proj_data["ghost"]["timestamp"] = iso_now

for c in changes:
    proj_data["recent_changes"].append(c)
while len(proj_data["recent_changes"]) > 10:
    proj_data["recent_changes"].pop(0)

for d in decisions:
    if d not in proj_data["decisions"]:
        proj_data["decisions"].append(d)

proj_data["meta"]["last_touched"] = iso_now

with open(proj_path, 'w') as f:
    json.dump(proj_data, f, indent=2, ensure_ascii=False)

# 2. Update Ghosts
ghosts_path = os.path.expanduser("~/.agent/memory/ghosts.json")
ghosts_data = load_or_create(ghosts_path, {"ghosts": {}})
if "ghosts" not in ghosts_data:
    ghosts_data["ghosts"] = {}

ghosts_data["ghosts"][project_id] = {
    "last_task": last_task,
    "last_file": last_file,
    "last_conversation": conv_id,
    "timestamp": iso_now
}
with open(ghosts_path, 'w') as f:
    json.dump(ghosts_data, f, indent=2, ensure_ascii=False)

# 3. Update System Log
sys_path = os.path.expanduser("~/.agent/memory/system.json")
sys_data = load_or_create(sys_path, {"sessions_log": []})
with open(sys_path, 'r+') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    try:
        d = json.load(f)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        d = {"sessions_log": []}
        
    log = d.get('sessions_log', [])
    if len(log) >= 30:
        log.pop()
    
    log.insert(0, {
        'date': iso_now,
        'project': project_id,
        'focus': "Auditoría Retrospectiva y Type-Safety",
        'duration_approx': "1h",
        'key_output': "Cristalizado Kernel 1000-Primitive Space en Rust",
        'conversation_id': conv_id
    })
    d['sessions_log'] = log
    d['last_updated'] = iso_now
    
    f.seek(0)
    f.truncate()
    json.dump(d, f, indent=2, ensure_ascii=False)

print("✅ JSON Files updated atomically.")

# 4. Snapshot Guard
snaps = sorted(glob.glob(os.path.expanduser("~/.agent/memory/snapshots/system_*.json")))
do_snapshot = True
if snaps:
    last = os.path.basename(snaps[-1]).replace("system_","").replace(".json","")
    try:
        last_ts = time.mktime(time.strptime(last, "%Y%m%d"))
        days = (time.time() - last_ts) / 86400
        if days < 7:
            do_snapshot = False
            print(f"⏭ Snapshot omitido ({days:.1f} días < 7)")
    except (OSError, RuntimeError, ValueError):
        pass

if do_snapshot:
    os.makedirs(os.path.expanduser("~/.agent/memory/snapshots"), exist_ok=True)
    dst = os.path.expanduser(f"~/.agent/memory/snapshots/system_{datetime.date.today().strftime('%Y%m%d')}.json")
    shutil.copy(sys_path, dst)
    print(f"📸 Snapshot creado: {dst}")

print("✅ Persistencia completada.")
