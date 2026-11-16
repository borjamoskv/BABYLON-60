#!/usr/bin/env python3
"""
Suite de regresion — verdad-terreno conocida, sin red.

El fixture se genera en un directorio temporal en vez de vivir en el repo: si
los ficheros-cebo estuvieran versionados, un escaneo de esta propia skill los
reportaria como fantasmas. Ademas, las consultas al registro se sustituyen por
un mapa fijo, para que un fallo de red no se lea como un fallo de deteccion.

    python3 tests/test_regression.py

Regla: si baja la sensibilidad, este fichero falla. Si sube, actualiza EXPECTED
en el mismo commit que el cambio de detector, nunca despues.
"""
from __future__ import annotations
import pathlib, shutil, sys, tempfile, textwrap

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import existence_gap as eg          # noqa: E402
import ci_supply_chain as ci        # noqa: E402

FILES = {
    "pyproject.toml": """
        [project]
        name = "demo"
        dependencies = ["httpx"]
        [tool.setuptools.packages.find]
        where = ["src"]
    """,
    "src/demo/__init__.py": "",
    "src/demo/core.py": """
        from .swarm import legion                 # A: relativo -> demo.swarm no existe
        from demo.utils import missing_fn         # B: modulo existe, simbolo no
        import demo.ghost.deep                    # C: ruta punteada fantasma
        from demo.utils import real_fn            # OK
        from .capability_guard import check       # D: control de seguridad ausente
    """,
    "src/demo/utils.py": "def real_fn(): ...\n",
    "src/demo/broken.py": "def f(:\n    import paquete_inventado_zzz9\n",  # E: rescate por regex
    "app.py": """
        import yaml
        import cv2
        import httpx
        from demo import core
        try:
            import opcional_inexistente_kk      # I: guardado -> degrada limpio
        except ImportError:
            opcional_inexistente_kk = None
        import importlib
        importlib.import_module("cargado_por_cadena_ww")   # J: dinamico
    """,
    "venv/lib/site-packages/foreign.py": "import no_es_nuestro_xyz\n",      # G: no debe contarse
    "scratch/junk.py": "import otro_inventado_qqq\n",                       # H: informativo

    # ── lado JS ──────────────────────────────────────────────────────────────
    "package.json": '{"dependencies": {"lodash": "^4"}}',
    "tsconfig.json": """
        {
          // tsconfig admite comentarios
          "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./web/*"] } }
        }
    """,
    "web/components/Boton.tsx": "export const Boton = () => null;\n",
    "web/helpers.ts": "export const h = 1;\n",
    "web/app.ts": """
        import fs from "node:fs";                       // builtin con prefijo
        import path from "path";                        // builtin desnudo
        import { Boton } from "@/components/Boton";     // alias que resuelve
        import { X } from "@/components/NoExiste";      // K: alias fantasma
        import { h } from "./helpers";                  // relativo que resuelve
        import { q } from "./no_existe_local";          // L: relativo fantasma
        import _ from "lodash";                         // declarado
        import z from "paquete-npm-inventado-zz";       // M: externo fantasma
        const lazy = await import("./tampoco_existe");  // N: dinamico fantasma
    """,
}

WORKFLOW = """
name: ci
on: [push, pull_request_target]
permissions: write-all
jobs:
  b:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - uses: nvida/setup-cuda@v1
      - uses: actionz/cache@v1
      - uses: actions/setup-python@39cd14951b08e74b54015e9e001cdefcf80e669f
      - run: echo "${{ github.event.pull_request.title }}"
"""

# Registro simulado: import-name -> existe en PyPI
FAKE_REGISTRY = {
    "yaml": True, "cv2": True, "httpx": True,
    "opcional_inexistente_kk": False, "cargado_por_cadena_ww": False,
    "paquete_inventado_zzz9": False, "otro_inventado_qqq": False,
    "no_es_nuestro_xyz": False,
}

EXPECTED = {
    ("FANTASMA_INTERNO", "demo.swarm"),
    ("FANTASMA_INTERNO", "demo.ghost.deep"),
    ("FANTASMA_INTERNO", "demo.capability_guard"),
    ("SIMBOLO_FANTASMA", "demo.utils.missing_fn"),
    ("FANTASMA", "paquete_inventado_zzz9"),
    ("FANTASMA", "otro_inventado_qqq"),
    ("FANTASMA", "cargado_por_cadena_ww"),   # solo visible con captura de import dinamico
    ("FANTASMA", "opcional_inexistente_kk"),
    ("FANTASMA_INTERNO", "@/components/NoExiste"),
    ("FANTASMA_INTERNO", "./no_existe_local"),
    ("FANTASMA_INTERNO", "./tampoco_existe"),
    ("FANTASMA", "paquete-npm-inventado-zz"),
}
FORBIDDEN_MODULES = {
    "no_es_nuestro_xyz",   # vive en venv/: no es codigo del repo
    "demo",                # src-layout declarado: no es LOCAL_DESALINEADO
    "fs", "path", "node:fs",           # builtins de Node
    "@/components", "@/components/Boton",  # alias de tsconfig que resuelve
    "./helpers",                       # relativo que resuelve
    "lodash",                          # declarado en package.json
}
EXPECTED_CI = {
    ("PRIVILEGIO_PR_TARGET", "critico"),
    ("INYECCION_EXPRESION", "critico"),
    # namespace inexistente a distancia 1: prima FANTASMA (mas grave) sobre TYPOSQUAT
    ("ACCION_FANTASMA", "critico"),
    # namespace a distancia 1 que SI existe: alguien ya lo registro
    ("ACCION_TYPOSQUAT", "medio"),
    ("PERMISO_EXCESIVO", "alto"),
    ("PIN_MUTABLE", "bajo"),
}


def build(tmp: pathlib.Path):
    for rel, body in FILES.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body).lstrip())
    wf = tmp / ".github" / "workflows" / "ci.yml"
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(WORKFLOW)


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="egap-fixture-"))
    fails = []
    try:
        build(tmp)
        eg.pypi_exists = lambda n: (FAKE_REGISTRY.get(n), n, {})
        eg.npm_exists = lambda n: ({"lodash": True}.get(n, False), n, {})
        rep = eg.analyse(tmp, offline=False)

        got = {(f["kind"], f["module"]) for f in rep["findings"]}
        for exp in sorted(EXPECTED):
            if exp not in got:
                fails.append(f"NO DETECTADO  {exp[0]:18} {exp[1]}")
        for f in rep["findings"]:
            if f["module"] in FORBIDDEN_MODULES:
                fails.append(f"FALSO POSITIVO  {f['kind']:18} {f['module']}  ({f['severity']})")
        if not rep["syntax_errors"]:
            fails.append("NO REPORTADO  fichero con error de sintaxis (silencio = cobertura falsa)")
        ctrl = [f for f in rep["findings"] if f["module"] == "demo.capability_guard"]
        if ctrl and ctrl[0]["severity"] not in ("alto", "critico"):
            fails.append(f"SEVERIDAD BAJA  control ausente reportado como {ctrl[0]['severity']}")

        by_mod = {f["module"]: f for f in rep["findings"]}
        g = by_mod.get("opcional_inexistente_kk")
        if g and "guarded" not in g.get("flags", []):
            fails.append("NO MARCADO  import envuelto en try/except sin flag 'guarded'")
        if g and g["severity"] not in ("bajo", "informativo"):
            fails.append(f"SEVERIDAD ALTA  fantasma que degrada limpiamente como {g['severity']}")
        d = by_mod.get("cargado_por_cadena_ww")
        if d and "dinamico" not in d.get("flags", []):
            fails.append("NO MARCADO  import dinamico sin flag 'dinamico'")
        if rep.get("reachability") != "medida":
            fails.append(f"ALCANZABILIDAD  esperada 'medida', obtenida {rep.get('reachability')!r}")

        ci.gh_exists = lambda slug: {"actions/checkout": True, "actions/setup-python": True,
                                     "actionz/cache": True}.get(slug, False)
        cirep = ci.scan(tmp, offline=False)
        ci_got = {(f["kind"], f["severity"]) for f in cirep["findings"]}
        ci_kinds = {k for k, _ in ci_got}
        for kind, sev in sorted(EXPECTED_CI, key=lambda x: x[0]):
            if sev is None:
                if kind not in ci_kinds:
                    fails.append(f"CI NO DETECTADO  {kind}")
            elif (kind, sev) not in ci_got:
                fails.append(f"CI NO DETECTADO  {kind} @ {sev}")

        print(f"python : {len(rep['findings'])} hallazgos, "
              f"{len(EXPECTED - {(k, m) for k, m in got})}/{len(EXPECTED)} esperados ausentes")
        print(f"ci     : {len(cirep['findings'])} hallazgos")
        if fails:
            print("\nFALLOS:")
            for f in fails:
                print("  " + f)
            return 1
        print("\nOK — sensibilidad y ausencia de falsos positivos intactas.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
