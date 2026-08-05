# C5-REAL EXERGY CERTIFIED
import ast, sys, pathlib, collections

REPO = pathlib.Path(".")
pyfiles = [p for p in REPO.rglob("*.py") if ".git" not in p.parts and "venv" not in p.parts and ".venv" not in p.parts]
stdlib = set(sys.stdlib_module_names)
imports = collections.defaultdict(set)

for p in pyfiles:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: imports[a.name].add(str(p))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports[node.module].add(str(p))
    except SyntaxError:
        continue

search_paths = [
    REPO,
    REPO / "1_Operaciones_Activas" / "02_CORTEX_ENGINE",
    REPO / "1_Operaciones_Activas" / "02_CORTEX_ENGINE" / "cortex_guard"
]

def exists_locally(mod_name):
    parts = mod_name.split(".")
    for sp in search_paths:
        path = sp.joinpath(*parts)
        if path.is_dir() or path.with_suffix(".py").is_file():
            return True
    return False

local_top = set()
for sp in search_paths:
    if sp.exists():
        for e in sp.iterdir():
            if not e.name.startswith("."):
                name = e.stem if e.is_file() else e.name
                local_top.add(name)

third = set()
fantasmas_internos = set()

for m, fs in imports.items():
    top_level = m.split(".")[0]
    if top_level in stdlib: continue

    if top_level in local_top:
        # Corrección Opus 5: Punto ciego de ruta punteada
        if not exists_locally(m):
            fantasmas_internos.add(f"{m} (en {', '.join(fs)})")
    else:
        third.add(top_level)

print("=== Dependencias Externas (Para verificar en PyPI) ===")
for m in third: print(m)

print("\n=== Módulos Internos Fantasma (Dotted-path blindspot) ===")
for m in fantasmas_internos: print(m)
