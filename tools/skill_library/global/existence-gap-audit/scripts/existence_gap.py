#!/usr/bin/env python3
"""
existence_gap.py — Detecta huecos de existencia en un repositorio.

Cruza el grafo de imports contra tres oraculos independientes:
  1. filesystem del repo
  2. manifiesto declarado (pyproject.toml / requirements*.txt / package.json)
  3. registro de paquetes (PyPI / npm)

Clasifica cada import externo en: FANTASMA, TRAMPA_SLOPSQUAT, NO_DECLARADO,
LOCAL_DESALINEADO u OK.

Solo stdlib. Sin dependencias.

Uso:
    python3 existence_gap.py <repo> [--json informe.json] [--offline] [--quiet]
"""

from __future__ import annotations

import argparse
import ast
import collections
import datetime
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

# ─────────────────────────────────────────────────────────────────────────────
# Configuracion
# ─────────────────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", "dist", "build", ".tox", "target", ".next", "vendor",
    "site-packages", ".ruff_cache", ".gradle", "third_party",
}

# Directorios cuyo contenido NO es una ruta viva (baja la severidad).
LOW_STAKES = re.compile(
    r"(^|/)(tests?|scratch|examples?|samples?|docs?|benchmarks?|fixtures?|"
    r"demos?|playground|sandbox|notebooks?|migrations?)(/|$)", re.I
)

# Rutas cuya compromision es critica (sube la severidad).
SECURITY_SENSITIVE = re.compile(
    r"(auth|login|session|token|credential|secret|licen[sc]e|crypt|sign|verif|"
    r"attest|permission|acl|payment|billing|admin|exec|eval|shell|subprocess)", re.I
)

# Nombres de modulo que SON un control de seguridad.
#
# Se aplica al modulo IMPORTADO, no al fichero importador. Un control que no
# existe no es deuda tecnica: es un control ausente. Sin esta comprobacion, la
# mitigacion por arbol legacy silencia el caso mas grave que este escaner puede
# encontrar — un `guard` que el codigo importa, la documentacion anuncia, y que
# no esta en ninguna parte.
SECURITY_CONTROL = re.compile(
    r"(guard|sandbox|sanitiz|validat|polic(y|ies)|quarantin|capabilit|"
    r"permission|authoriz|authent|ratelimit|rate_limit|firewall|allowlist|"
    r"denylist|blocklist|verif|attest|integrity)", re.I
)

# import-name -> nombre de distribucion, cuando difieren.
DIST_ALIASES = {
    "yaml": "pyyaml", "nacl": "pynacl", "dotenv": "python-dotenv",
    "PIL": "pillow", "cv2": "opencv-python", "sklearn": "scikit-learn",
    "bs4": "beautifulsoup4", "serial": "pyserial", "usb": "pyusb",
    "OpenSSL": "pyopenssl", "jwt": "pyjwt", "dateutil": "python-dateutil",
    "attr": "attrs", "google": "protobuf", "pkg_resources": "setuptools",
    "telegram": "python-telegram-bot", "gtts": "gTTS", "magic": "python-magic",
    "docx": "python-docx", "pptx": "python-pptx", "fitz": "pymupdf",
    "AppKit": "pyobjc-framework-Cocoa", "Cocoa": "pyobjc-framework-Cocoa",
    "Quartz": "pyobjc-framework-Quartz", "Vision": "pyobjc-framework-Vision",
    "ApplicationServices": "pyobjc-framework-ApplicationServices",
    "Foundation": "pyobjc-framework-Cocoa", "objc": "pyobjc-core",
    "zoneinfo": "backports.zoneinfo", "pythonosc": "python-osc",
    "mlx_lm": "mlx-lm", "llama_index": "llama-index", "py_ecc": "py-ecc",
    "sqlite_vec": "sqlite-vec", "nest_asyncio": "nest-asyncio",
    "prometheus_client": "prometheus-client", "zenoh": "eclipse-zenoh",
}

JS_IMPORT_RE = re.compile(
    r"""(?:^|\s)(?:import\s+(?:[\w*{}\s,$]+\s+from\s+)?|export\s+[\w*{}\s,]+\s+from\s+)"""
    r"""['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)""",
    re.M,
)

TIMEOUT = 12
UA = {"User-Agent": "existence-gap-audit/1.0"}


# ─────────────────────────────────────────────────────────────────────────────
# Recorrido
# ─────────────────────────────────────────────────────────────────────────────

def walk(root: pathlib.Path, suffixes: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if pathlib.Path(fn).suffix in suffixes:
                yield pathlib.Path(dirpath) / fn


# ─────────────────────────────────────────────────────────────────────────────
# Extraccion de imports
# ─────────────────────────────────────────────────────────────────────────────

PY_IMPORT_RE = re.compile(
    r"^\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([.\w]+)\s+import\s+(.+?)\s*$)", re.M)


def package_of(rel: str) -> tuple[str, ...]:
    """Paquete al que pertenece un fichero, subiendo mientras haya __init__.py.

    Necesario para resolver imports relativos: `from .swarm import legion` en
    src/babylon60/core.py significa babylon60.swarm, no `.swarm`. Sin esto, todo
    import relativo se descarta silenciosamente — y el codigo generado por LLM
    usa imports relativos precisamente en los subpaquetes que inventa.
    """
    parts = pathlib.PurePosixPath(rel).parts[:-1]
    return parts


def resolve_relative(rel: str, level: int, module: str | None, root: pathlib.Path) -> str | None:
    """`from ..core import x` en a/b/c.py -> 'a.core'. None si sube fuera del arbol."""
    pkg = list(package_of(rel))
    # level=1 es el paquete del propio fichero; cada nivel extra sube uno.
    up = level - 1
    if up > len(pkg):
        return None
    base = pkg[: len(pkg) - up] if up else pkg
    # Recortar prefijos de layout que no forman parte del nombre del paquete.
    while base and base[0] in ("src", "lib", "source"):
        base = base[1:]
    full = list(base) + ([module] if module else [])
    return ".".join(x for x in full if x) or None


IMPORT_ERRORS = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}


def _handles_import_error(node: ast.Try) -> bool:
    for h in node.handlers:
        if h.type is None:
            return True
        for n in ast.walk(h.type):
            if isinstance(n, ast.Name) and n.id in IMPORT_ERRORS:
                return True
    return False


def _dynamic_target(node: ast.Call) -> str | None:
    """importlib.import_module("x") / __import__("x") con literal.

    Un cargador de plugins escrito por un modelo enumera modulos por cadena. El
    AST walk que solo mira nodos Import no ve nada: el fichero parece limpio y
    el subsistema entero queda fuera del informe.
    """
    f = node.func
    name = (f.attr if isinstance(f, ast.Attribute) else
            f.id if isinstance(f, ast.Name) else None)
    if name not in ("import_module", "__import__"):
        return None
    if not node.args:
        return None
    a0 = node.args[0]
    return a0.value if isinstance(a0, ast.Constant) and isinstance(a0.value, str) else None


def visit(node, rel, root, add, from_symbols, flags, guarded, lazy):
    """Recorrido con contexto. ast.walk pierde la relacion padre-hijo, y sin ella
    no se puede distinguir un import que degrada limpiamente de uno que revienta
    el proceso al cargar el modulo — que es justo la distincion que separa una
    trampa latente de una vulnerabilidad activa."""
    for child in ast.iter_child_nodes(node):
        g = guarded or (isinstance(node, ast.Try) and _handles_import_error(node))
        l = lazy or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        marks = ({"guarded"} if g else set()) | ({"lazy"} if l else set())

        if isinstance(child, ast.Import):
            for a in child.names:
                add(a.name, rel, child.lineno, marks)
        elif isinstance(child, ast.ImportFrom):
            if child.level and child.level > 0:
                full = resolve_relative(rel, child.level, child.module, root)
            else:
                full = child.module
            if full:
                add(full, rel, child.lineno, marks)
                for a in child.names:
                    if a.name != "*":
                        from_symbols.append((rel, child.lineno, full, a.name))
        elif isinstance(child, ast.Call):
            tgt = _dynamic_target(child)
            if tgt:
                add(tgt, rel, child.lineno, marks | {"dinamico"})

        visit(child, rel, root, add, from_symbols, flags,
              guarded or (isinstance(child, ast.Try) and _handles_import_error(child)),
              lazy or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)))


def extract_python(root: pathlib.Path):
    """-> (imports: {top: [(relpath, lineno, full)]}, syntax_errors, from_symbols)

    from_symbols: [(relpath, lineno, modulo, simbolo)] para verificacion de nombre.
    """
    imports = collections.defaultdict(list)
    from_symbols = []
    syntax_errors = []
    flags = {}

    def add(full, rel, lineno, marks=()):
        if not full:
            return
        site = (rel, lineno, full)
        imports[full.split(".")[0]].append(site)
        if marks:
            flags.setdefault(site, set()).update(marks)

    for p in walk(root, {".py"}):
        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            syntax_errors.append((rel, f"linea {e.lineno}: {e.msg}"))
            # Rescate por regex: un fichero que no parsea NO es un fichero limpio.
            # Sus imports siguen siendo evidencia y deben entrar en el informe.
            for m in PY_IMPORT_RE.finditer(text):
                mod = m.group(1) or m.group(2)
                if mod and not mod.startswith("."):
                    add(mod, rel, text[: m.start()].count("\n") + 1)
            continue
        except Exception:
            continue

        visit(tree, rel, root, add, from_symbols, flags, guarded=False, lazy=False)

    return imports, syntax_errors, from_symbols, flags


# Modulos internos de Node. No estan en package.json y no deben consultarse en
# npm: 'fs', 'path' y 'events' existen ademas como paquetes publicos, asi que
# sin esta lista el escaner los reporta como dependencias sin declarar.
NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "domain",
    "events", "fs", "http", "http2", "https", "inspector", "module", "net",
    "os", "path", "perf_hooks", "process", "punycode", "querystring", "readline",
    "repl", "stream", "string_decoder", "sys", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}
JS_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".vue", ".svelte",
           ".d.ts")
JS_DYNAMIC_RE = re.compile(r"""\bimport\(\s*['"]([^'"]+)['"]\s*\)""")
JSONC_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def _load_jsonc(path: pathlib.Path):
    """tsconfig.json admite comentarios. json.loads no."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    try:
        return json.loads(JSONC_COMMENT_RE.sub("", raw))
    except Exception:
        return {}


def ts_aliases(root: pathlib.Path):
    """compilerOptions.paths -> [(prefijo, [dirs])].

    Sin esto, '@/components/Boton' se lee como paquete con scope '@/components'
    y se consulta en npm, que devuelve 404. Todo proyecto Next.js o Vite con
    alias produce un informe lleno de fantasmas inexistentes: el falso positivo
    masivo que hace que nadie vuelva a mirar el informe.
    """
    out = []
    for name in ("tsconfig.json", "jsconfig.json"):
        for cfg in list(root.glob(name)) + list(root.glob("*/" + name)):
            data = _load_jsonc(cfg)
            co = (data or {}).get("compilerOptions") or {}
            base = (cfg.parent / (co.get("baseUrl") or ".")).resolve()
            for pat, tgts in (co.get("paths") or {}).items():
                if isinstance(tgts, list):
                    out.append((pat.rstrip("*"), [str(base / t.rstrip("*")) for t in tgts]))
    return out


def js_resolves(spec: str, importer: pathlib.Path, root: pathlib.Path, aliases) -> bool:
    """¿La especificacion apunta a un fichero real del arbol?"""
    cands = []
    if spec.startswith("."):
        cands.append((importer.parent / spec).resolve())
    elif spec.startswith("/"):
        cands.append(pathlib.Path(spec))
    else:
        for pre, tgts in aliases:
            if pre and spec.startswith(pre):
                rest = spec[len(pre):]
                cands += [pathlib.Path(t) / rest for t in tgts]
    for c in cands:
        if c.is_file():
            return True
        for e in JS_EXTS:
            if c.with_name(c.name + e).is_file():
                return True
            if (c / ("index" + e)).is_file():
                return True
        if c.is_dir() and (c / "package.json").is_file():
            return True
    return not cands  # sin candidatos = no es una ruta local, no opinamos


def extract_js(root: pathlib.Path):
    """-> (imports externos, rutas locales rotas)"""
    imports = collections.defaultdict(list)
    broken_local = collections.defaultdict(list)
    aliases = ts_aliases(root)
    for p in walk(root, {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte"}):
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        specs = [(m.group(1) or m.group(2), m.start()) for m in JS_IMPORT_RE.finditer(text)]
        specs += [(m.group(1), m.start()) for m in JS_DYNAMIC_RE.finditer(text)]
        for spec, pos in specs:
            if not spec:
                continue
            lineno = text.count("\n", 0, pos) + 1
            aliased = any(pre and spec.startswith(pre) for pre, _ in aliases)
            if spec.startswith((".", "/")) or aliased:
                # Ruta local: o existe en disco, o es un hueco de existencia.
                # Delegarla al bundler es la misma excusa que descartar los
                # imports relativos en Python, y oculta el mismo fallo.
                if not js_resolves(spec, p, root, aliases):
                    broken_local[spec].append((rel, lineno, spec))
                continue
            base = spec[5:] if spec.startswith("node:") else spec
            parts = base.split("/")
            top = "/".join(parts[:2]) if base.startswith("@") else parts[0]
            if top in NODE_BUILTINS or spec.startswith("node:"):
                continue
            imports[top].append((rel, lineno, spec))
    return imports, broken_local


# ─────────────────────────────────────────────────────────────────────────────
# Oraculo 1: filesystem
# ─────────────────────────────────────────────────────────────────────────────

def package_roots(root: pathlib.Path) -> list[str]:
    """Directorios que entran en sys.path segun el manifiesto (o convencion).

    Sin esto, todo proyecto con src-layout —el layout por defecto de setuptools,
    hatch y poetry modernos— reporta LOCAL_DESALINEADO en cada import interno.
    Un falso positivo de severidad alta por proyecto entero destruye el informe.
    """
    roots = []
    data = _load_toml(root / "pyproject.toml")
    tool = data.get("tool", {}) if isinstance(data, dict) else {}
    find = tool.get("setuptools", {}).get("packages", {})
    if isinstance(find, dict):
        roots += [w for w in find.get("find", {}).get("where", []) if isinstance(w, str)]
    for pkg in tool.get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {}).get("packages", []) or []:
        if isinstance(pkg, str) and "/" in pkg:
            roots.append(pkg.rsplit("/", 1)[0])
    for pkg in tool.get("poetry", {}).get("packages", []) or []:
        if isinstance(pkg, dict) and pkg.get("from"):
            roots.append(pkg["from"])
    if (root / "src").is_dir():
        roots.append("src")
    return sorted({r.strip("./") for r in roots if r and r not in (".", "")})


def local_python_modules(root: pathlib.Path):
    """Modulos importables desde la RAIZ del repo (top-level)."""
    top = set()
    for entry in root.iterdir():
        if entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        if entry.is_dir():
            top.add(entry.name)
        elif entry.suffix == ".py":
            top.add(entry.stem)
    return top


def all_python_modules(root: pathlib.Path):
    """Todo modulo/paquete que exista en cualquier profundidad -> [rutas]."""
    found = collections.defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        d = pathlib.Path(dirpath)
        for dn in dirnames:
            found[dn].append(str((d / dn).relative_to(root)))
        for fn in filenames:
            if fn.endswith(".py") and fn != "__init__.py":
                found[fn[:-3]].append(str((d / fn).relative_to(root)))
    return found


# ─────────────────────────────────────────────────────────────────────────────
# Oraculo 2: manifiesto declarado
# ─────────────────────────────────────────────────────────────────────────────

def _load_toml(path: pathlib.Path) -> dict:
    """tomllib (py>=3.11) con respaldo en tomli (py3.10). Sin ninguno, {}."""
    try:
        import tomllib as _t
    except ImportError:
        try:
            import tomli as _t  # type: ignore[no-redef]
        except ImportError:
            return {}
    try:
        return _t.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower().strip()


def path_index(root: pathlib.Path) -> set:
    """Todas las rutas relativas (dirs y .py) del arbol, en formato posix."""
    idx = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and (d not in SKIP_DIRS or (pathlib.Path(dirpath) / d / "__init__.py").is_file())
        ]
        d = pathlib.Path(dirpath)
        for dn in dirnames:
            idx.add((d / dn).relative_to(root).as_posix())
        for fn in filenames:
            if fn.endswith(".py"):
                idx.add((d / fn).relative_to(root).as_posix())
    return idx


def resolve_dotted(dotted: str, idx: set) -> bool:
    """¿Resuelve 'a.b.c' a un modulo real en ALGUNA raiz de paquete del arbol?

    No se puede asumir que la raiz del paquete es la raiz del repo: en monorepos
    el paquete cuelga de un subdirectorio (`sub/proj/cortex/...`) y ese directorio
    entra en sys.path en tiempo de ejecucion. Resolver solo desde la raiz del repo
    produce falsos positivos masivos — y el peor caso es marcar como ausente un
    control de seguridad que si existe. Ante la duda, resolvemos.
    """
    parts = dotted.split(".")
    suffixes = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
        "/".join(parts),
    ]
    for p in idx:
        for s in suffixes:
            if p == s or p.endswith("/" + s):
                return True
    return False


def resolve_dotted_path(dotted: str, idx: set):
    """Como resolve_dotted pero devuelve la ruta concreta (o None)."""
    parts = dotted.split(".")
    for s in ("/".join(parts) + "/__init__.py", "/".join(parts) + ".py"):
        for p in idx:
            if p == s or p.endswith("/" + s):
                return p
    return None


def _module_bindings(path: pathlib.Path):
    """Nombres ligados en el nivel superior de un modulo. None = indeterminable.

    Devuelve None si el modulo usa `import *`, define `__getattr__` (PEP 562) o
    no parsea: en esos casos cualquier nombre puede existir en runtime y afirmar
    su ausencia seria una conjetura, no una medida.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
                    if t.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        names.update(e.value for e in node.value.elts
                                     if isinstance(e, ast.Constant) and isinstance(e.value, str))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                if a.name == "*":
                    return None  # star-import: indeterminable
                names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, (ast.Try, ast.If)):
            # imports condicionales / opcionales: no podemos enumerar con certeza
            for sub in ast.walk(node):
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    for a in sub.names:
                        if a.name == "*":
                            return None
                        names.add(a.asname or a.name.split(".")[0])
                elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(sub.name)
                elif isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            names.add(t.id)
    if "__getattr__" in names:
        return None
    return names


def phantom_symbols(root: pathlib.Path, from_symbols, idx, anywhere):
    """`from a.b import c` donde a.b existe pero c no.

    Punto ciego de segundo orden: comprobar la ruta punteada valida el modulo,
    no el nombre. Un subsistema alucinado suele acertar el modulo e inventar la
    clase. Conservador por diseno: solo reporta cuando el modulo es enumerable.
    """
    out = collections.defaultdict(list)
    cache = {}
    stdlib = set(sys.stdlib_module_names)
    for rel, lineno, mod, sym in from_symbols:
        top = mod.split(".")[0]
        if top not in anywhere:
            continue  # externo: no es nuestro
        if top in stdlib:
            continue  # colision de nombre con la stdlib: cual gana depende de sys.path
        key = (mod, sym)
        if key not in cache:
            mpath = resolve_dotted_path(mod, idx)
            if not mpath:
                cache[key] = False  # el modulo ya se reporta como fantasma
            else:
                full = root / mpath
                # si es paquete, el simbolo puede ser un submodulo
                if mpath.endswith("/__init__.py"):
                    base = mpath[: -len("/__init__.py")]
                    if any(q == f"{base}/{sym}.py" or q == f"{base}/{sym}"
                           or q.endswith(f"/{base}/{sym}.py") for q in idx):
                        cache[key] = False
                        continue
                binds = _module_bindings(full)
                cache[key] = binds is not None and sym not in binds
        if cache[key]:
            out[f"{mod}.{sym}"].append((rel, lineno, f"from {mod} import {sym}"))
    return out


def broken_local_paths(root: pathlib.Path, py_imports, local_top, anywhere=None):
    """Imports internos con ruta punteada que no resuelven.

    Punto ciego clasico: 'from babylon60.swarm.legion import X' pasa cualquier
    filtro de primer nivel porque 'babylon60' SI existe. Que exista el paquete
    raiz no dice nada sobre el submodulo. Aqui se resuelve la ruta completa.
    """
    broken = collections.defaultdict(list)
    idx = path_index(root)
    cache = {}
    # El gate debe usar el mismo criterio que el resolutor. Filtrar por
    # local_top (modulos en la RAIZ del repo) mientras resolve_dotted acepta
    # cualquier raiz del arbol desactiva el detector entero en src-layout y en
    # monorepos — justo donde vive el codigo real.
    known = set(local_top) | set(anywhere or {})
    for top, sites in py_imports.items():
        if top not in known:
            continue
        for rel, lineno, full in sites:
            if "." not in full:
                continue
            if full not in cache:
                cache[full] = resolve_dotted(full, idx)
            if not cache[full]:
                broken[full].append((rel, lineno, full))
    return broken


def declared_python(root: pathlib.Path):
    declared = set()
    pp = root / "pyproject.toml"
    if pp.exists():
        data = _load_toml(pp)
        proj = data.get("project", {}) or {}
        buckets = list(proj.get("dependencies", []) or [])
        for group in (proj.get("optional-dependencies", {}) or {}).values():
            buckets += list(group or [])
        for group in (data.get("dependency-groups", {}) or {}).values():
            buckets += [g for g in (group or []) if isinstance(g, str)]
        poetry = ((data.get("tool", {}) or {}).get("poetry", {}) or {}).get("dependencies", {}) or {}
        buckets += list(poetry.keys())
        for spec in buckets:
            if isinstance(spec, str):
                declared.add(norm(re.split(r"[<>=!~\[; ]", spec, 1)[0]))
    for req in walk(root, {".txt"}):
        if not req.name.startswith("requirements"):
            continue
        try:
            for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    declared.add(norm(re.split(r"[<>=!~\[; ]", line, 1)[0]))
        except Exception:
            pass
    declared.discard("")
    return declared


def packaging_excludes(root: pathlib.Path):
    """Rutas que el propio proyecto declara fuera de packaging/lint (legacy, vendorizado).

    Un import roto dentro de un arbol que el mantenedor ya excluyo explicitamente
    es deuda declarada, no un hallazgo. Ignorarlo produce falsos positivos que
    cualquier refutador tumbara con razon.
    """
    ex = set()
    pp = root / "pyproject.toml"
    if not pp.exists():
        return ex
    data = _load_toml(pp)
    if not data:
        return ex
    tool = data.get("tool", {}) or {}
    for pat in ((tool.get("setuptools", {}) or {}).get("packages", {}) or {}).get("find", {}).get("exclude", []) or []:
        ex.add(pat.replace(".*", "").replace("*", "").replace(".", "/").rstrip("/"))
    for pat in (tool.get("ruff", {}) or {}).get("extend-exclude", []) or []:
        ex.add(pat.strip("^$").rstrip("/"))
    for pat in (tool.get("mypy", {}) or {}).get("exclude", []) or []:
        ex.add(pat.strip("^$").rstrip("/"))
    return {e for e in ex if e}


def internal_looking(module: str, sites, root: pathlib.Path, phantoms: set, all_mods) -> tuple[bool, str]:
    """¿Este nombre pretende ser un modulo INTERNO del proyecto?

    Discriminador central. Un paquete conocido de PyPI sin declarar (httpx, rich)
    es higiene de packaging. Un nombre que el proyecto trata como suyo pero que
    resulta existir en PyPI es una trampa de dependency confusion: quien depure
    el ImportError instalara codigo ajeno creyendo que repara infraestructura propia.
    """
    # Señal 1: el repo ya referencia ese nombre como concepto propio
    #          (p.ej. 'from babylon60.swarm.legion import ...' junto a 'from legion import ...')
    if module in all_mods:
        return True, f"el repo lo trata como modulo propio ({all_mods[module][0]})"

    # Señal 2: co-ocurrencia con fantasmas confirmados en el mismo fichero.
    #          Los subsistemas alucinados se generan en bloque y comparten fichero.
    for f, _ln, _full in sites:
        try:
            src = (root / f).read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        companions = {p for p in phantoms if re.search(rf"\b(?:from|import)\s+{re.escape(p)}\b", src)}
        if companions:
            return True, f"co-ocurre en {f} con fantasma(s) confirmado(s): {', '.join(sorted(companions)[:3])}"

    # Señal 3: el import va precedido de sys.path.insert -> se espera un modulo
    #          de un arbol hermano privado, no un paquete publicado.
    for f, ln, _full in sites:
        try:
            lines = (root / f).read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        window = "\n".join(lines[max(0, ln - 15):ln])
        if "sys.path.insert" in window or "sys.path.append" in window:
            return True, f"precedido de manipulacion de sys.path en {f}:{ln} (se espera un arbol privado)"

    return False, ""


def declared_js(root: pathlib.Path):
    declared = set()
    for pkg in walk(root, {".json"}):
        if pkg.name != "package.json":
            continue
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            declared.update((data.get(key) or {}).keys())
    return declared


# ─────────────────────────────────────────────────────────────────────────────
# Oraculo 3: registro
# ─────────────────────────────────────────────────────────────────────────────

def probe(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return None if e.code != 404 else False
    except Exception:
        return None  # indeterminado: red caida, no concluir


def probe_json(url: str):
    """-> (200?, payload|None). None/None = indeterminado (red), no concluyente."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
            return True, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return (False, None) if e.code == 404 else (None, None)
    except Exception:
        return None, None


def _age_days(iso: str) -> float | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return (datetime.datetime.utcnow() - datetime.datetime.strptime(iso[:26], fmt)).days
        except ValueError:
            continue
    return None


def pypi_meta(payload: dict) -> dict:
    """Firma temporal. Un paquete recien creado, con una release y sin repo, cuyo
    nombre coincide con un import alucinado, no es una dependencia olvidada: es
    la forma que tiene el slopsquat de aparecer en el registro. Sin fecha, el
    escaner colapsa 'existe' con 'legitimo' y pierde el unico caso que importa.
    """
    info = payload.get("info", {}) or {}
    ups = [f.get("upload_time") for fs in (payload.get("releases") or {}).values()
           for f in (fs or []) if f.get("upload_time")]
    first = min(ups) if ups else None
    urls = info.get("project_urls") or {}
    return {
        "first_upload": first,
        "age_days": _age_days(first) if first else None,
        "release_count": len(payload.get("releases") or {}),
        "has_repo": any(k.lower() in ("repository", "source", "source code", "homepage", "code")
                        and v for k, v in urls.items()) or bool(info.get("home_page")),
        "summary": (info.get("summary") or "")[:120],
    }


def pypi_exists(import_name: str):
    cands = [DIST_ALIASES.get(import_name), import_name, import_name.replace("_", "-")]
    for c in dict.fromkeys(x for x in cands if x):
        got, payload = probe_json(f"https://pypi.org/pypi/{c}/json")
        if got is True:
            return True, c, pypi_meta(payload or {})
        if got is None:
            return None, c, {}
    return False, (cands[0] if cands else import_name), {}


def npm_exists(name: str):
    got, payload = probe_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}")
    meta = {}
    if got is True and payload:
        created = (payload.get("time") or {}).get("created")
        meta = {"first_upload": created, "age_days": _age_days(created) if created else None,
                "release_count": len(payload.get("versions") or {}),
                "has_repo": bool(payload.get("repository")),
                "summary": (payload.get("description") or "")[:120]}
    return got, name, meta


# ─────────────────────────────────────────────────────────────────────────────
# Severidad
# ─────────────────────────────────────────────────────────────────────────────

ENTRY_NAMES = {"__main__.py", "main.py", "app.py", "manage.py", "wsgi.py",
               "asgi.py", "cli.py", "server.py", "run.py", "worker.py"}


def module_index(root: pathlib.Path, pkg_roots: list[str]) -> dict:
    """rel-path -> nombre de modulo, segun las raices de paquete reales."""
    out = {}
    prefixes = sorted(pkg_roots, key=len, reverse=True) + [""]
    for p in walk(root, {".py"}):
        rel = p.relative_to(root).as_posix()
        for pre in prefixes:
            if pre and not rel.startswith(pre + "/"):
                continue
            body = rel[len(pre) + 1:] if pre else rel
            parts = body[:-3].split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if parts:
                out[rel] = ".".join(parts)
            break
    return out


def entrypoints(root: pathlib.Path, modmap: dict) -> set:
    """Ficheros desde los que el proceso realmente empieza."""
    rev = {}
    for rel, mod in modmap.items():
        rev.setdefault(mod, rel)
    eps = set()
    data = _load_toml(root / "pyproject.toml")
    proj = data.get("project", {}) if isinstance(data, dict) else {}
    targets = list((proj.get("scripts") or {}).values()) + \
              list((proj.get("gui-scripts") or {}).values())
    for group in (proj.get("entry-points") or {}).values():
        if isinstance(group, dict):
            targets += list(group.values())
    for t in targets:
        if isinstance(t, str) and (mod := t.split(":")[0]) in rev:
            eps.add(rev[mod])
    for rel in modmap:
        name = rel.rsplit("/", 1)[-1]
        if name in ENTRY_NAMES:
            eps.add(rel)
            continue
        try:
            if "__main__" in (root / rel).read_text(encoding="utf-8", errors="replace"):
                eps.add(rel)
        except Exception:
            pass
    return eps


def reachable_files(root: pathlib.Path, py_imports, pkg_roots, idx):
    """Ficheros alcanzables por grafo de imports desde un entrypoint real.

    Implementa el primer eje de la matriz de alcanzabilidad, que hasta ahora era
    doctrina sin instrumento: la severidad se asignaba por DONDE VIVE el fichero,
    y la propia SKILL.md advierte que ese criterio acierta al reves en los dos
    casos interesantes.

    Devuelve None si no se identifica ningun entrypoint. None significa
    'no medido', y el llamante debe caer al heuristico de ruta — nunca tratar
    'no alcanzable' y 'no medido' como lo mismo: eso convertiria un repo sin
    entrypoint reconocible en un informe entero de severidad informativa.
    """
    modmap = module_index(root, pkg_roots)
    eps = entrypoints(root, modmap)
    if not eps:
        return None, set()
    rev = {}
    for rel, mod in modmap.items():
        rev.setdefault(mod, rel)
    edges = collections.defaultdict(set)
    for sites in py_imports.values():
        for rel, _ln, full in sites:
            tgt = rev.get(full)
            if tgt is None:  # 'a.b.c' puede apuntar a un simbolo de a.b
                tgt = rev.get(full.rsplit(".", 1)[0]) if "." in full else None
            if tgt and tgt != rel:
                edges[rel].add(tgt)
    seen, stack = set(eps), list(eps)
    while stack:
        cur = stack.pop()
        for nxt in edges.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen, eps


FRESH_DAYS = 270


def is_fresh(meta: dict) -> bool:
    age = (meta or {}).get("age_days")
    if age is None:
        return False
    return age < FRESH_DAYS and (meta.get("release_count", 99) <= 3 or not meta.get("has_repo"))


def fresh_why(meta: dict) -> str:
    bits = [f"registrado hace {meta.get('age_days')} dias",
            f"{meta.get('release_count')} release(s)"]
    if not meta.get("has_repo"):
        bits.append("sin repositorio declarado")
    return ", ".join(bits)


DEMOTED = []


def rate(kind: str, sites, excluded=None, reach=None) -> str:
    """Severidad. Si la alcanzabilidad medida degrada el resultado respecto al
    heuristico de ubicacion, se anota en DEMOTED: un escaner que baja severidades
    sin decirlo produce exactamente la señal verde enganosa que intenta evitar."""
    sev = _rate(kind, sites, excluded, reach)
    if reach is not None:
        alt = _rate(kind, sites, excluded, None)
        if ORDER.get(sev, 9) > ORDER.get(alt, 9):
            DEMOTED.append((kind, sites[0][0] if sites else "?", alt, sev))
    return sev


def _rate(kind: str, sites, excluded=None, reach=None) -> str:
    excluded = excluded or []
    paths = [s[0] for s in sites]
    if reach is not None:
        # Alcanzabilidad medida: el fichero importador cuelga del grafo que
        # arranca en un entrypoint. Sustituye al indicio de ubicacion.
        live = any(p in reach and not any(p.startswith(x) for x in excluded)
                   for p in paths)
    else:
        live = any(
            not LOW_STAKES.search(p) and not any(p.startswith(x) for x in excluded)
            for p in paths
        )
    sensitive = any(
        SECURITY_SENSITIVE.search(p) and not any(p.startswith(x) for x in excluded)
        for p in paths
    )
    if kind in ("TRAMPA_SLOPSQUAT", "SLOPSQUAT_RECIENTE"):
        if sensitive:
            return "critico"
        return "alto" if live else "medio"
    if kind == "FANTASMA":
        if not live:
            return "informativo"
        return "alto" if sensitive else "medio"
    if kind == "LOCAL_DESALINEADO":
        return "alto" if live else "bajo"
    if kind == "NO_DECLARADO":
        return "medio" if len({s[0] for s in sites}) >= 5 else "bajo"
    return "informativo"


ORDER = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3, "informativo": 4}


# ─────────────────────────────────────────────────────────────────────────────
# Analisis
# ─────────────────────────────────────────────────────────────────────────────

def analyse(root: pathlib.Path, offline: bool, use_reach: bool = True):
    stdlib = set(sys.stdlib_module_names)
    py_imports, syn_err, from_syms, site_flags = extract_python(root)
    js_imports, js_broken = extract_js(root)
    local_top = local_python_modules(root)
    anywhere = all_python_modules(root)
    dec_py = declared_python(root)
    dec_js = declared_js(root)

    py_ext = {m: s for m, s in py_imports.items() if m not in stdlib and m not in local_top}
    js_ext = {m: s for m, s in js_imports.items() if m not in dec_js}

    # Consultas al registro, en paralelo.
    reg = {}
    if not offline:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            fut_py = {ex.submit(pypi_exists, m): ("py", m) for m in py_ext}
            fut_js = {ex.submit(npm_exists, m): ("js", m) for m in js_ext}
            for fut in concurrent.futures.as_completed({**fut_py, **fut_js}):
                eco, m = {**fut_py, **fut_js}[fut]
                try:
                    exists, probed, meta = fut.result()
                except Exception:
                    exists, probed, meta = None, m, {}
                reg[(eco, m)] = (exists, probed, meta)

    findings = []
    excl = packaging_excludes(root)
    pkg_roots = package_roots(root)
    reach, eps = reachable_files(root, py_imports, pkg_roots, None) if use_reach else (None, set())
    DEMOTED.clear()
    total_py = len(module_index(root, pkg_roots))

    # Paso 1: fijar el conjunto de fantasmas ANTES de clasificar el resto.
    # La co-ocurrencia con un fantasma es la señal que separa una trampa de
    # dependency confusion de un simple olvido en el manifiesto.
    phantoms = {
        m for m, sites in py_ext.items()
        if reg.get(("py", m), (None, m, {}))[0] is False and not anywhere.get(m)
    }

    # Paso 2: clasificar. Una entrada por modulo, sin solapamientos.
    for m, sites in py_ext.items():
        exists, probed, rmeta = reg.get(("py", m), (None, m, {}))
        declared = norm(DIST_ALIASES.get(m, m)) in dec_py or norm(m) in dec_py
        on_disk = anywhere.get(m, [])
        evidence = ""

        if exists is True and declared:
            continue  # OK: declarado y existe

        under_pkg_root = any(
            d == r or d.startswith(r + "/") for d in on_disk for r in pkg_roots)
        if on_disk and under_pkg_root and not declared:
            # Vive bajo una raiz de paquete declarada: al instalar el proyecto
            # entra en sys.path por construccion. No es desalineamiento.
            continue
        if on_disk:
            kind = "LOCAL_DESALINEADO"
            note = (f"existe en el repo ({', '.join(on_disk[:3])}) pero se importa como top-level; "
                    f"solo resuelve con el cwd/sys.path correcto")
            if exists is True:
                note += (f" | ADEMAS '{probed}' existe en PyPI con el mismo nombre: "
                         f"el orden de sys.path decide cual gana (shadowing)")
        elif exists is False:
            kind = "FANTASMA"
            note = "no existe ni en el repo ni en PyPI: el codigo que lo importa nunca se ha ejecutado"
        elif exists is True and not declared:
            internal, why = internal_looking(m, sites, root, phantoms, anywhere)
            if internal:
                kind = "TRAMPA_SLOPSQUAT"
                evidence = why
                note = (f"el proyecto lo trata como modulo propio, pero '{probed}' existe en PyPI. "
                        f"Reparar el ImportError con 'pip install {probed}' introduce codigo ajeno. Señal: {why}")
            elif is_fresh(rmeta):
                kind = "SLOPSQUAT_RECIENTE"
                evidence = fresh_why(rmeta)
                note = (f"'{probed}' existe en PyPI pero su huella temporal no es la de una "
                        f"dependencia establecida ({evidence}). Un nombre inventado por un modelo y "
                        f"registrado poco despues es el ciclo completo del slopsquat. "
                        f"Verifica el autor antes de instalar")
            else:
                kind = "NO_DECLARADO"
                note = (f"paquete real de PyPI ('{probed}') usado en {len({s[0] for s in sites})} "
                        f"fichero(s) y ausente del manifiesto: instalacion limpia rota")
        else:
            kind = "NO_VERIFICADO"
            note = ("registro no consultado (--offline)" if offline
                    else "registro indeterminado (red); no se concluye")

        sev = rate(kind, sites, excl, reach)
        only_excluded = bool(excl) and all(
            any(s[0].startswith(x) for x in excl) for s in sites
        )
        is_control = bool(SECURITY_CONTROL.search(m))
        if only_excluded and kind != "FANTASMA" and not is_control:
            sev = "informativo"
            note += " | mitigado: todos los puntos de import estan en un arbol que el propio pyproject excluye de packaging/lint (deuda declarada)"
        elif only_excluded and is_control:
            sev = sev if ORDER.get(sev, 9) <= ORDER["alto"] else "alto"
            note += (" | NO mitigado pese a estar en arbol legacy: el nombre del modulo lo identifica "
                     "como un control de seguridad, y un control ausente no es deuda declarada")

        marks = set().union(*(site_flags.get(s_, set()) for s_ in sites)) if sites else set()
        all_guarded = bool(sites) and all("guarded" in site_flags.get(s_, set()) for s_ in sites)
        if all_guarded and not is_control and ORDER.get(sev, 9) < ORDER["bajo"]:
            sev = "bajo"
            note += (" | todos los puntos de import estan envueltos en try/except ImportError: "
                     "degrada limpiamente. Es una trampa latente, no una vulnerabilidad activa")
        if "dinamico" in marks:
            note += " | detectado via importlib.import_module/__import__ con literal de cadena"
        findings.append({
            "ecosystem": "python", "module": m, "kind": kind, "severity": sev,
            "flags": sorted(marks),
            "note": note, "evidence": evidence, "declared": declared,
            "in_registry": exists, "registry_name": probed, "on_disk": on_disk[:5],
            "only_in_excluded_tree": only_excluded,
            "sites": [{"file": f, "line": ln, "imported": full} for f, ln, full in sites[:12]],
            "site_count": len(sites),
        })

    for m, sites in js_ext.items():
        if m in dec_js:
            continue
        exists, probed, rmeta = reg.get(("js", m), (None, m, {}))
        if exists is True:
            internal, why = internal_looking(m, sites, root, phantoms, anywhere)
            kind = "TRAMPA_SLOPSQUAT" if internal else "NO_DECLARADO"
        else:
            kind = "FANTASMA" if exists is False else "NO_VERIFICADO"
        findings.append({
            "ecosystem": "node", "module": m, "kind": kind, "severity": rate(kind, sites, excl, reach),
            "note": ("no declarado en package.json; existe en npm" if exists is True
                     else "no declarado y no existe en npm" if exists is False
                     else "no declarado; npm no consultado"),
            "declared": False, "in_registry": exists, "registry_name": probed, "on_disk": [],
            "flags": [],
            "sites": [{"file": f, "line": ln, "imported": full} for f, ln, full in sites[:12]],
            "site_count": len(sites),
        })

    # Paso 3: fantasmas internos — el paquete raiz existe, el submodulo no.
    for dotted, sites in broken_local_paths(root, py_imports, local_top, anywhere).items():
        sev = rate("FANTASMA", sites, excl, reach)
        only_excluded = bool(excl) and all(any(s[0].startswith(x) for x in excl) for s in sites)
        is_control = bool(SECURITY_CONTROL.search(dotted))
        if is_control:
            final_sev = sev if ORDER.get(sev, 9) <= ORDER["alto"] else "alto"
        elif only_excluded:
            final_sev = "informativo"
        else:
            final_sev = sev
        findings.append({
            "ecosystem": "python", "module": dotted, "kind": "FANTASMA_INTERNO",
            "severity": final_sev,
            "note": (f"el paquete raiz '{dotted.split('.')[0]}' existe, pero la ruta completa "
                     f"'{dotted.replace('.', '/')}' no resuelve a ningun modulo del repo"
                     + (" | CONTROL DE SEGURIDAD AUSENTE: el nombre identifica un guard/sandbox/validador. "
                        "La exclusion por arbol legacy no aplica — el codigo lo importa y la documentacion "
                        "lo anuncia, pero no existe." if is_control else "")),
            "evidence": "resolucion de ruta punteada contra el filesystem", "flags": [],
            "declared": True, "in_registry": None, "registry_name": None, "on_disk": [],
            "only_in_excluded_tree": only_excluded,
            "sites": [{"file": f, "line": ln, "imported": full} for f, ln, full in sites[:12]],
            "site_count": len(sites),
        })

    # Paso 3b: rutas locales JS que no existen en disco.
    for spec, sites in js_broken.items():
        findings.append({
            "ecosystem": "node", "module": spec, "kind": "FANTASMA_INTERNO",
            "severity": rate("FANTASMA", sites, excl),
            "note": ("la ruta no resuelve a ningun fichero del arbol (probadas extensiones "
                     "y /index.*, y los alias de tsconfig si los hay)"),
            "evidence": "resolucion de ruta local contra el filesystem",
            "declared": True, "in_registry": None, "registry_name": None, "on_disk": [],
            "only_in_excluded_tree": False, "flags": [],
            "sites": [{"file": f, "line": ln, "imported": sp} for f, ln, sp in sites[:12]],
            "site_count": len(sites),
        })

    # Paso 4: simbolos fantasma — el modulo existe, el nombre importado no.
    # Verificar la ruta punteada valida el modulo, nunca el nombre; un subsistema
    # alucinado acierta el modulo e inventa la clase.
    for dotted, sites in phantom_symbols(root, from_syms, path_index(root), anywhere).items():
        is_control = bool(SECURITY_CONTROL.search(dotted))
        sev = rate("FANTASMA", sites, excl, reach)
        if is_control and ORDER.get(sev, 9) > ORDER["alto"]:
            sev = "alto"
        mod, _, sym = dotted.rpartition(".")
        findings.append({
            "ecosystem": "python", "module": dotted, "kind": "SIMBOLO_FANTASMA",
            "severity": sev,
            "note": (f"el modulo '{mod}' existe y resuelve, pero no define ni reexporta "
                     f"'{sym}'. El import falla en runtime con ImportError, no ModuleNotFoundError"
                     + (" | CONTROL DE SEGURIDAD AUSENTE" if is_control else "")),
            "evidence": "enumeracion de bindings de nivel superior del modulo destino", "flags": [],
            "declared": True, "in_registry": None, "registry_name": None, "on_disk": [],
            "only_in_excluded_tree": False,
            "sites": [{"file": f, "line": ln, "imported": full} for f, ln, full in sites[:12]],
            "site_count": len(sites),
        })

    findings.sort(key=lambda f: (ORDER.get(f["severity"], 9), -f["site_count"]))
    return {
        "repo": str(root),
        "reachability": ("medida" if reach is not None else "no medida (sin entrypoint reconocible)"),
        "entrypoints": sorted(eps)[:20],
        "reachable_files": (len(reach) if reach is not None else None),
        "total_python_files": total_py,
        "demoted_by_reachability": [
            {"kind": k, "file": f, "sin_alcanzabilidad": a, "con_alcanzabilidad": b}
            for k, f, a, b in DEMOTED
        ],
        "syntax_errors": [{"file": f, "error": e} for f, e in syn_err],
        "counts": collections.Counter(f["kind"] for f in findings),
        "findings": findings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Salida
# ─────────────────────────────────────────────────────────────────────────────

BLOCKING = {"FANTASMA", "FANTASMA_INTERNO", "SIMBOLO_FANTASMA", "TRAMPA_SLOPSQUAT",
            "SLOPSQUAT_RECIENTE", "LOCAL_DESALINEADO"}


def render(rep, quiet=False):
    out = []
    c = rep["counts"]
    out.append("═" * 78)
    out.append(f"AUDITORIA DE HUECOS DE EXISTENCIA — {rep['repo']}")
    out.append("═" * 78)
    r = rep.get("reachability")
    if r:
        n = rep.get("reachable_files")
        tot = rep.get("total_python_files")
        out.append(f"\nAlcanzabilidad: {r}"
                   + (f" — {n}/{tot} ficheros cuelgan de "
                      f"{len(rep.get('entrypoints') or [])} entrypoint(s)"
                      if n is not None else ""))
        if r.startswith("no medida"):
            out.append("  La severidad cae al heuristico de ubicacion. Trata 'informativo' con reserva.")
        elif n is not None and tot and n / tot < 0.5:
            out.append(f"  AVISO: mas de la mitad del arbol no cuelga de ningun entrypoint "
                       f"reconocido. O el codigo esta muerto, o falta un entrypoint "
                       f"(libreria importada desde fuera, plugin, servicio arrancado por "
                       f"un runner externo). Revisa antes de fiarte de las degradaciones.")
        dem = rep.get("demoted_by_reachability") or []
        if dem:
            out.append(f"  {len(dem)} hallazgo(s) degradados por no ser alcanzables. "
                       f"No es lo mismo que ausentes:")
            for d in dem[:8]:
                out.append(f"    {d['kind']:18} {d['file']}  {d['sin_alcanzabilidad']} -> {d['con_alcanzabilidad']}")
    if rep["syntax_errors"]:
        out.append(f"\n⚠  {len(rep['syntax_errors'])} fichero(s) con error de sintaxis (no analizados):")
        for e in rep["syntax_errors"][:10]:
            out.append(f"     {e['file']}  {e['error']}")
    out.append("")
    for k in ("TRAMPA_SLOPSQUAT", "SLOPSQUAT_RECIENTE", "FANTASMA", "FANTASMA_INTERNO",
              "SIMBOLO_FANTASMA", "LOCAL_DESALINEADO", "NO_DECLARADO", "NO_VERIFICADO"):
        if c.get(k):
            out.append(f"  {k:20s} {c[k]:4d}")
    if not rep["findings"]:
        out.append("  Sin huecos de existencia. Todo import externo resuelve.")
    out.append("")
    for f in rep["findings"]:
        if quiet and f["severity"] in ("bajo", "informativo"):
            continue
        out.append("─" * 78)
        out.append(f"[{f['severity'].upper()}] {f['kind']} — {f['module']}  ({f['ecosystem']}, {f['site_count']} import(s))")
        out.append(f"  {f['note']}")
        for s in f["sites"][:6]:
            out.append(f"    → {s['file']}:{s['line']}  ({s['imported']})")
        if f["site_count"] > 6:
            out.append(f"    … y {f['site_count'] - 6} mas")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Detecta huecos de existencia en el grafo de imports.")
    ap.add_argument("repo")
    ap.add_argument("--json", help="escribe el informe completo en este fichero")
    ap.add_argument("--offline", action="store_true", help="omite las consultas al registro")
    ap.add_argument("--quiet", action="store_true", help="oculta severidad baja/informativa")
    ap.add_argument("--no-reach", action="store_true",
                    help="ignora el grafo de alcanzabilidad; severidad solo por ubicacion")
    ap.add_argument("--fail-on", default="", help="sale con codigo 1 si hay hallazgos de esta severidad o superior")
    args = ap.parse_args()

    root = pathlib.Path(args.repo).resolve()
    if not root.is_dir():
        sys.exit(f"no es un directorio: {root}")

    rep = analyse(root, args.offline, use_reach=not args.no_reach)
    print(render(rep, args.quiet))

    if args.json:
        rep_out = dict(rep, counts=dict(rep["counts"]))
        pathlib.Path(args.json).write_text(json.dumps(rep_out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nInforme JSON: {args.json}")

    if args.fail_on:
        thr = ORDER.get(args.fail_on, 99)
        bad = [f for f in rep["findings"]
               if ORDER.get(f["severity"], 9) <= thr and f["kind"] in BLOCKING]
        if bad:
            print(f"\n✗ {len(bad)} hallazgo(s) bloqueante(s) de severidad >= {args.fail_on}")
            sys.exit(1)
        print(f"\n✓ Sin hallazgos bloqueantes de severidad >= {args.fail_on}")
    sys.exit(0)


if __name__ == "__main__":
    import urllib.parse  # usado por npm_exists
    main()
