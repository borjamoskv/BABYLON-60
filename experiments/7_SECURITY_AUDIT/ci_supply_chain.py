#!/usr/bin/env python3
"""
ci_supply_chain.py — Huecos de existencia en la superficie de CI.

El escaner de imports mira el codigo que corre en la maquina del desarrollador.
Este mira el que corre en el runner, con el token del repositorio en el entorno.
Es la superficie de mayor privilegio y la que menos se audita: una `uses:` con
una errata en la organizacion se resuelve contra un namespace que cualquiera
puede registrar, y se ejecuta en cada push.

Clases:
  ACCION_FANTASMA       el namespace org/repo no existe -> registrable por terceros
  ACCION_TYPOSQUAT      a distancia 1 de una accion conocida (nvida vs nvidia)
  PIN_MUTABLE           referencia a rama/tag movil en vez de SHA
  INYECCION_EXPRESION   ${{ github.event.* }} interpolado dentro de un `run:`
  PRIVILEGIO_PR_TARGET  pull_request_target haciendo checkout del head del PR
  PERMISO_EXCESIVO      write-all o scopes de escritura sensibles

Solo stdlib. Sin dependencias.
    python3 ci_supply_chain.py <repo> [--json informe.json] [--offline]

GITHUB_TOKEN en el entorno sube el limite de 60 a 5000 consultas/hora.
"""
from __future__ import annotations

import argparse, json, os, pathlib, re, sys, urllib.error, urllib.request
import concurrent.futures

TIMEOUT = 12
UA = {"User-Agent": "existence-gap-audit/2.0", "Accept": "application/vnd.github+json"}

# Organizaciones de acciones de uso masivo. La lista no pretende ser exhaustiva:
# sirve como referencia para distancia de edicion, no como allowlist.
KNOWN_ORGS = {
    "actions", "github", "docker", "aws-actions", "azure", "google-github-actions",
    "hashicorp", "codecov", "softprops", "peter-evans", "dawidd6", "JamesIves",
    "pypa", "astral-sh", "denoland", "oven-sh", "ruby", "gradle", "nvidia",
    "sigstore", "slsa-framework", "step-security", "ossf", "anchore", "aquasecurity",
    "treosh", "reviewdog", "golangci", "actions-rs", "dtolnay", "Swatinem",
}

USES_RE = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"\s#]+)", re.M)
RUN_BLOCK_RE = re.compile(r"^([ \t]*)-?\s*run:\s*[|>]?-?\s*\n((?:\1[ \t]+.*\n?)*)", re.M)
RUN_INLINE_RE = re.compile(r"^\s*-?\s*run:\s*(?![|>])(.+)$", re.M)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
# Contextos controlables por un tercero sin permisos de escritura en el repo.
TAINTED = re.compile(
    r"\$\{\{\s*(github\.event\.(issue|pull_request|comment|discussion|review)"
    r"[\w.]*(title|body|login|ref|label|name)|github\.head_ref|"
    r"github\.event\.head_commit\.message|github\.event\.pages)", re.I)
PERM_WRITE = re.compile(
    r"^\s*(contents|packages|id-token|actions|deployments|security-events|"
    r"pull-requests|issues):\s*write", re.M)


def lev1(a: str, b: str) -> bool:
    """¿Distancia de edicion <= 1? Suficiente para typosquat de namespace."""
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    i = j = 0
    diff = 0
    while i < la and j < lb:
        if a[i] != b[j]:
            diff += 1
            if diff > 1:
                return False
            if la > lb:
                i += 1
            elif lb > la:
                j += 1
            else:
                i += 1; j += 1
        else:
            i += 1; j += 1
    return True


def gh_exists(slug: str):
    """True / False / None. None = indeterminado (red, rate-limit, auth).

    Distinguir 403 de 404 no es un detalle: reportar 'namespace libre' porque la
    API respondio 429 convierte el informe en ruido y quema su credibilidad.
    """
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    h = dict(UA)
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    try:
        with urllib.request.urlopen(
                urllib.request.Request(f"https://api.github.com/repos/{slug}", headers=h),
                timeout=TIMEOUT) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code == 404 else None
    except Exception:
        return None


def workflow_files(root: pathlib.Path):
    for pat in (".github/workflows/*.yml", ".github/workflows/*.yaml",
                ".github/actions/**/action.yml", ".github/actions/**/action.yaml",
                "action.yml", "action.yaml"):
        yield from root.glob(pat)


def scan(root: pathlib.Path, offline: bool):
    findings = []
    actions = {}          # slug -> [(file, line, ref)]
    for f in workflow_files(root):
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")

        for m in USES_RE.finditer(text):
            spec = m.group(1)
            line = text[: m.start()].count("\n") + 1
            if spec.startswith("./") or spec.startswith("docker://"):
                continue
            slug, _, ref = spec.partition("@")
            slug = "/".join(slug.split("/")[:2])   # org/repo[/subdir]
            if "/" not in slug:
                continue
            actions.setdefault(slug, []).append((rel, line, ref))

        # Inyeccion de expresiones en bloques run
        for rx in (RUN_BLOCK_RE, RUN_INLINE_RE):
            for m in rx.finditer(text):
                body = m.group(2) if rx is RUN_BLOCK_RE else m.group(1)
                for t in TAINTED.finditer(body or ""):
                    findings.append({
                        "kind": "INYECCION_EXPRESION", "severity": "critico",
                        "target": t.group(0), "file": rel,
                        "line": text[: m.start()].count("\n") + 1 + (body or "")[: t.start()].count("\n"),
                        "note": ("contexto controlable por un tercero interpolado directamente en el shell "
                                 "del runner. El valor se sustituye ANTES de ejecutar: comillas y escapes "
                                 "del shell no protegen. Pasalo por env: y referencia \"$VAR\""),
                    })

        # pull_request_target con checkout del head del PR
        if "pull_request_target" in text and re.search(
                r"ref:\s*\$\{\{\s*github\.event\.pull_request\.head", text):
            findings.append({
                "kind": "PRIVILEGIO_PR_TARGET", "severity": "critico",
                "target": "pull_request_target + checkout head", "file": rel, "line": 1,
                "note": ("pull_request_target corre con el token del repositorio base y secretos; "
                         "hacer checkout del head del PR ejecuta codigo del proponente con ese privilegio"),
            })

        for m in PERM_WRITE.finditer(text):
            scope = m.group(1)
            if scope in ("security-events", "id-token", "contents", "packages", "actions"):
                findings.append({
                    "kind": "PERMISO_EXCESIVO", "severity": "medio",
                    "target": f"{scope}: write", "file": rel,
                    "line": text[: m.start()].count("\n") + 1,
                    "note": "scope de escritura; comprueba que ningun paso del job ejecute codigo no confiable",
                })
        if re.search(r"permissions:\s*write-all", text):
            findings.append({"kind": "PERMISO_EXCESIVO", "severity": "alto",
                             "target": "write-all", "file": rel, "line": 1,
                             "note": "write-all concede todos los scopes al token del runner"})

    # Existencia de namespaces, en paralelo
    reg = {}
    if not offline and actions:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(gh_exists, s): s for s in actions}
            for fu in concurrent.futures.as_completed(futs):
                try:
                    reg[futs[fu]] = fu.result()
                except Exception:
                    reg[futs[fu]] = None

    for slug, sites in sorted(actions.items()):
        org, _, repo = slug.partition("/")
        exists = reg.get(slug)
        near = [k for k in KNOWN_ORGS if lev1(org.lower(), k.lower())]

        if exists is False:
            findings.append({
                "kind": "ACCION_FANTASMA", "severity": "critico", "target": slug,
                "file": sites[0][0], "line": sites[0][1],
                "note": (f"el namespace '{slug}' no existe en GitHub. Cualquiera puede registrarlo y su "
                         f"codigo se ejecutara en el runner con el token del repositorio en cada disparo"
                         + (f" | a distancia 1 de: {', '.join(near)}" if near else "")),
                "sites": sites,
            })
        elif near and exists is not True:
            findings.append({
                "kind": "ACCION_TYPOSQUAT", "severity": "alto", "target": slug,
                "file": sites[0][0], "line": sites[0][1],
                "note": f"'{org}' esta a una edicion de {', '.join(near)}; verifica cual querias",
                "sites": sites,
            })
        elif near and exists is True:
            findings.append({
                "kind": "ACCION_TYPOSQUAT", "severity": "medio", "target": slug,
                "file": sites[0][0], "line": sites[0][1],
                "note": (f"'{org}' existe pero esta a una edicion de {', '.join(near)}: "
                         f"typosquat registrado, o coincidencia. Comprueba el propietario"),
                "sites": sites,
            })
        elif exists is None and not offline:
            findings.append({
                "kind": "NO_VERIFICADO", "severity": "informativo", "target": slug,
                "file": sites[0][0], "line": sites[0][1],
                "note": "GitHub no respondio de forma concluyente (rate-limit sin GITHUB_TOKEN o red)",
                "sites": sites,
            })

        for rel, line, ref in sites:
            if ref and not SHA_RE.match(ref):
                findings.append({
                    "kind": "PIN_MUTABLE", "severity": "bajo", "target": f"{slug}@{ref}",
                    "file": rel, "line": line,
                    "note": ("referencia movil: el propietario puede reescribir el tag y cambiar lo que "
                             "ejecuta tu runner sin que cambie tu repo. Fija el SHA de 40 caracteres"),
                })

    ORDER = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3, "informativo": 4}
    findings.sort(key=lambda f: ORDER.get(f["severity"], 9))
    return {"repo": str(root), "actions_seen": len(actions), "findings": findings}


def render(rep):
    print("=" * 78)
    print(f"SUPERFICIE DE CI — {rep['repo']}   ({rep['actions_seen']} accion(es) referenciadas)")
    print("=" * 78)
    if not rep["findings"]:
        print("\nSin hallazgos.")
        return
    counts = {}
    for f in rep["findings"]:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    print()
    for k, v in sorted(counts.items()):
        print(f"  {k:22} {v}")
    for f in rep["findings"]:
        print("\n" + "-" * 78)
        print(f"[{f['severity'].upper()}] {f['kind']} — {f['target']}")
        print(f"  {f['file']}:{f['line']}")
        print(f"  {f['note']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--fail-on", choices=["critico", "alto", "medio", "bajo"])
    a = ap.parse_args()
    rep = scan(pathlib.Path(a.repo).resolve(), a.offline)
    render(rep)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    if a.fail_on:
        ORDER = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3, "informativo": 4}
        lim = ORDER[a.fail_on]
        if any(ORDER.get(f["severity"], 9) <= lim for f in rep["findings"]):
            sys.exit(2)


if __name__ == "__main__":
    main()
