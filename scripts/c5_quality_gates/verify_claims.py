#!/usr/bin/env python3
"""
BABYLON-60 — Epistemic Claims Invariant Verifier (C5-REAL / v5.0)
Gobernanza determinista fail-closed: Todo claim en CLAIMS.toml es auditado contra evidencia en silicio.
Si cualquier claim requerido o verificado falla su evidencia o ejecuta 0 tests en algún subcomando,
el proceso finaliza con código de salida 1 (Fail-Closed).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def parse_simple_toml(content: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {"claim": {}, "metadata": {}}
    current_section: Optional[str] = None
    current_claim: Optional[str] = None

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[metadata]"):
            current_section = "metadata"
            continue
        if line.startswith("[claim."):
            current_section = "claim"
            claim_id = line[len("[claim.") : -1]
            current_claim = claim_id
            data["claim"][claim_id] = {}
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if current_section == "metadata":
                data["metadata"][key] = val
            elif current_section == "claim" and current_claim:
                if val.lower() in ("true", "false"):
                    data["claim"][current_claim][key] = val.lower() == "true"
                else:
                    data["claim"][current_claim][key] = val

    return data


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sh(cmd: List[str], cwd: Path) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True).stdout.strip()
    except OSError as e:
        return f"unavailable: {e}"


def sh_bytes(cmd: List[str], cwd: Path) -> bytes:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=False).stdout
    except OSError as e:
        return f"unavailable: {e}".encode("utf-8")


GENERATED_EVIDENCE = {
    "evidence.json",
    "claims.lock",
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST.json.sig",
    "RELEASE_MANIFEST.json.ots",
    "evidence.json.ots",
    "sbom.cargo.cdx.json",
    "sbom.python.cdx.json",
    "scripts/c5_quality_gates/claims_sitrep.json",
}

VAULT_ONLY_PREFIXES = (
    ".agents/rules/",
    ".agents/mcp_config.json",
    ".playwright-mcp/",
    "docs/security/evidence/",
    "tools/skill_library/",
    "tests/test_skill_intent_routing.py",
    "tests/test_skill_library_convergence.py",
    "tests/test_skill_maintenance.py",
    "tests/test_project_skills_regressions.py",
    "tests/test_swarm100_lot1_regressions_vault.py",
    "tests/test_swarm100_lot2_regressions_vault.py",
    "tests/test_swarm100_lot12_s5_regressions_vault.py",
    "tests/test_swarm100_round2_regressions_vault.py",
    "tests/test_regulatory_native_validation_vault.py",
    "assets/brand/github-art-brut.svg",
    "assets/AppIcon.icns",
    "assets/babylon60_brutalist_logo_1024.png",
)


def is_excluded_from_public_tree(relative: str) -> bool:
    return relative in GENERATED_EVIDENCE or relative.startswith(VAULT_ONLY_PREFIXES)


def source_commit(cwd: Path) -> str:
    head = sh(["git", "rev-parse", "HEAD"], cwd)
    raw_status = sh(["git", "status", "--porcelain", "--untracked-files=no"], cwd)
    dirty_lines = [
        parts[1]
        for line in raw_status.splitlines()
        for parts in [line.strip().split(None, 1)]
        if len(parts) > 1 and not is_excluded_from_public_tree(parts[1])
    ]
    if dirty_lines:
        tracked_diff = sh_bytes(["git", "diff", "HEAD"], cwd)
        return head + "+dirty:" + sha256(tracked_diff)[:16]
    return head


def source_tree_digest(cwd: Path) -> str:
    """Bind evidence to tracked public-projection source bytes, excluding generated evidence and Vault-only blobs."""
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=cwd).split(b"\0")
    digest = hashlib.sha256()
    for raw_path in sorted(path for path in files if path):
        relative = raw_path.decode("utf-8")
        if is_excluded_from_public_tree(relative):
            continue
        path = cwd / relative
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
        except OSError:
            if path.is_symlink():
                payload = str(path.readlink()).encode("utf-8")
            else:
                raise
        else:
            with os.fdopen(fd, "rb") as stream:
                payload = stream.read()
        digest.update(raw_path + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def environment_digest(cwd: Path) -> Tuple[str, Dict[str, str]]:
    env = {
        "rustc": sh(["rustc", "-V"], cwd),
        "cargo": sh(["cargo", "-V"], cwd),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
    return sha256(json.dumps(env, sort_keys=True)), env


def count_executed_tests(output: str) -> Optional[int]:
    """Suma los tests realmente ejecutados según cargo/pytest.

    Si hay múltiples bloques `running N test`, exige que N > 0 en cada bloque
    para evitar que un comando encadenado con `&&` oculte un filtro vacío (0 tests).
    """
    total = 0
    recognised = False
    cargo_blocks = [int(m.group(1)) for m in re.finditer(r"running (\d+) tests?", output)]
    if cargo_blocks:
        recognised = True
        if any(n == 0 for n in cargo_blocks):
            return 0
        total += sum(cargo_blocks)
    m = re.search(r"(\d+) passed", output)
    if m:
        recognised = True
        total += int(m.group(1))
    if re.search(r"collected 0 items|no tests ran", output):
        return 0
    return total if recognised else None


ERROR_SUMMARY_LIMIT = 1000
_SUMMARY_LINE_LIMIT = 240
_PANIC_MESSAGE_LINES = 3
_OMITTED_LINES = "[... +{count} líneas omitidas]"

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
# Artefactos locales o aleatorios sin valor causal: usuario, temporales de pytest y de claims, id de hilo.
_LOCAL_ARTIFACT_RULES = (
    (re.compile(r"(?<![\w.-])/(Users|home)/[^/\s'\"`]+"), r"/\1/<user>"),
    (re.compile(r"pytest-of-[^/\s'\"`]+"), "pytest-of-<user>"),
    (re.compile(r"(?<=/)pytest-\d+(?=/)"), "pytest-<n>"),
    (re.compile(r"b60_claim_\w+"), "b60_claim_<rand>"),
    (re.compile(r"^(thread '[^'\n]*') \(\d+\)(?= panicked at )", re.MULTILINE), r"\1 (<tid>)"),
)
_SEPARATOR_RE = re.compile(r"^([=!_-])\1* (.+?) \1+$")
_PYTEST_HEADER_RE = re.compile(r"^(?:platform |collect|hypothesis |Using |(?!error:|warning:)[a-z][\w-]*: )")
_CARGO_PROGRESS_RE = re.compile(
    r"^\s+(?:Compiling|Checking|Finished|Running|Doc-tests|Fresh|Blocking|Downloading|Downloaded|Updating"
    r"|Locking|Adding|Building|Documenting|Waiting)\b"
)
_RUST_NOISE_BLOCK_RE = re.compile(r"^(?:warning(?:\[\w+\])?: |stack backtrace:)")
_DIAGNOSTIC_CONTINUATION_RE = re.compile(r"^(?:\s|\d+\s*\||\.\.\.)")
_PRIMARY_CAUSE_RE = re.compile(
    r"^(?:FAILED|ERROR) \S"  # pytest: FAILED/ERROR <nodeid> [- mensaje]
    r"|^ERROR: "  # pytest: error de uso o de colección
    r"|^E {2,}\S"  # pytest: excepción y explicación de la aserción
    r"|^Interrupted: "  # pytest: sesión interrumpida (p. ej. errores de colección)
    r"|^(?:no tests ran|\d+ \w+(?:, \d+ \w+)*) in \d+\.\d\ds(?: \(\d+:\d\d:\d\d\))?$"  # pytest: recuento final
    r"|^test result: FAILED"  # libtest
    r"|^error: (?:(?:doc)?test failed|could not compile|process didn't exit successfully|\d+ targets? failed)"
)
_SECONDARY_CAUSE_RE = re.compile(r"^error(?:\[E\d+\])?: |^Error: |^\S+:\d+:\d+: error\b")
_PANIC_RE = re.compile(r"^thread '[^']*'(?: \(\S+\))? panicked at ")
_PANIC_STOP_RE = re.compile(r"^(?:note: |stack backtrace:|thread '|failures:|test result: )")


def local_path_redactions(repo_root: Path) -> List[Tuple[str, str]]:
    """Prefijos absolutos de esta máquina con su marcador neutro: raíz del repo, temporal y HOME."""
    import tempfile

    pairs = [(str(repo_root), "<repo>"), (tempfile.gettempdir(), "<tmp>"), (os.path.expanduser("~"), "~")]
    pairs = [(prefix, label) for prefix, label in pairs if os.path.isabs(prefix)]
    pairs += [(os.path.realpath(prefix), label) for prefix, label in pairs]
    return [(prefix, label) for prefix, label in dict.fromkeys(pairs) if prefix.rstrip("/")]


def _normalize_local_artifacts(text: str, redactions: Sequence[Tuple[str, str]]) -> str:
    """Quita escapes ANSI y sustituye prefijos locales y artefactos aleatorios por marcadores neutros."""
    text = _ANSI_ESCAPE_RE.sub("", text)
    for prefix, label in sorted(redactions, key=lambda item: len(item[0]), reverse=True):
        prefix = prefix.rstrip("/")
        if prefix:
            boundary = re.compile(r"(?<![\w.-])" + re.escape(prefix) + r"(?![\w.-])")
            text = boundary.sub(lambda _match: label, text)
    for rule, replacement in _LOCAL_ARTIFACT_RULES:
        text = rule.sub(replacement, text)
    return text


def _drop_noise(text: str) -> List[str]:
    """Quita encabezado de sesión pytest, progreso de cargo, avisos de rustc y backtraces; compacta separadores."""
    kept: List[str] = []
    skip = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        separator = _SEPARATOR_RE.match(line)
        if separator:
            line = f"{separator.group(1)} {separator.group(2)} {separator.group(1)}"
        if skip == "header" and _PYTEST_HEADER_RE.match(line):
            continue
        if skip == "block" and line and _DIAGNOSTIC_CONTINUATION_RE.match(line):
            continue
        skip = ""
        if separator and separator.group(2) == "test session starts":
            skip = "header"
        elif _RUST_NOISE_BLOCK_RE.match(line):
            skip = "block"
        elif not _CARGO_PROGRESS_RE.match(line) and (line or (kept and kept[-1])):
            kept.append(line)
    while kept and not kept[-1]:
        kept.pop()
    return kept


def _key_units(lines: List[str]) -> List[Tuple[int, List[int]]]:
    """Bloques de causa como (prioridad, índices); un pánico de Rust se toma con su mensaje."""
    units: List[Tuple[int, List[int]]] = []
    index = 0
    while index < len(lines):
        if _PANIC_RE.match(lines[index]):
            block = [index]
            while (
                len(block) <= _PANIC_MESSAGE_LINES
                and index + len(block) < len(lines)
                and lines[index + len(block)]
                and not _PANIC_STOP_RE.match(lines[index + len(block)])
            ):
                block.append(index + len(block))
            units.append((0, block))
            index += len(block)
            continue
        separator = _SEPARATOR_RE.match(lines[index])
        content = separator.group(2) if separator else lines[index]
        if _PRIMARY_CAUSE_RE.match(content):
            units.append((0, [index]))
        elif _SECONDARY_CAUSE_RE.match(content):
            units.append((1, [index]))
        index += 1
    return units


def _condense(lines: List[str]) -> str:
    """Bloques de causa seguidos de la cola de la salida, sin superar ERROR_SUMMARY_LIMIT."""
    lines = [line if len(line) <= _SUMMARY_LINE_LIMIT else line[: _SUMMARY_LINE_LIMIT - 3] + "..." for line in lines]
    budget = ERROR_SUMMARY_LIMIT - len(_OMITTED_LINES.format(count=len(lines))) - 1
    tail_start, tail_cost = len(lines), 0
    while tail_start > 0 and tail_cost + len(lines[tail_start - 1]) + 1 <= budget // 2:
        tail_start -= 1
        tail_cost += len(lines[tail_start]) + 1
    head: List[int] = []
    head_cost = 0
    for _, block in sorted(unit for unit in _key_units(lines) if unit[1][-1] < tail_start):
        block_cost = sum(len(lines[i]) + 1 for i in block)
        if head_cost + block_cost + tail_cost <= budget:
            head.extend(block)
            head_cost += block_cost
    floor = max(head, default=-1) + 1
    while tail_start > floor and head_cost + tail_cost + len(lines[tail_start - 1]) + 1 <= budget:
        tail_start -= 1
        tail_cost += len(lines[tail_start]) + 1
    omitted = tail_start - len(head)
    marker = [_OMITTED_LINES.format(count=omitted)] if omitted else []
    return "\n".join([lines[i] for i in sorted(head)] + marker + lines[tail_start:])


def extract_failure_summary(output: str, *, redactions: Sequence[Tuple[str, str]] = ()) -> str:
    """Causa de un fallo de evidencia, determinista y acotada a ERROR_SUMMARY_LIMIT caracteres.

    Normaliza rutas locales (`redactions`, HOME de usuarios, temporales de pytest y de claims) y quita
    el encabezado de sesión de pytest, el progreso de cargo, los avisos de rustc y los backtraces. Si el
    resultado cabe se devuelve completo; si no, se conservan los bloques de causa (FAILED/ERROR, E,
    recuento final, pánicos, test result, error:) seguidos de la cola de la salida.
    """
    text = _normalize_local_artifacts(output, redactions)
    lines = _drop_noise(text) or text.strip().splitlines()
    summary = "\n".join(lines)
    return summary if len(summary) <= ERROR_SUMMARY_LIMIT else _condense(lines)


DISALLOWED_SHELL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bcurl\b",
        r"\bwget\b",
        r"\bnc\b",
        r"\bnetcat\b",
        r"\bbash\s+-i\b",
        r"\brm\s+-rf\b",
        r"/dev/tcp",
        r"\beval\b",
        r"\bbase64\s+-d\b",
        r"\bpython.*socket",
        r"\bchmod\s+[+]s\b",
        r"\bsudo\b",
        r"\bcat\s+/etc",
        r"\benv\b\s*\|",
    ]
]


ALLOWED_CLAIM_EXECUTABLES = {"cargo", "pytest", "lean", "uv", "python", "python3"}


def _parse_safe_step(step_str: str, temp_dir: Path) -> Tuple[List[str], Dict[str, str]]:
    """Parsea un paso individual en (argv, env_overrides) sin invocar un shell (`shell=False`)."""
    import shlex

    expanded = step_str.replace("$(mktemp -d)", str(temp_dir)).replace("$D", str(temp_dir / "run"))
    tokens = shlex.split(expanded)
    env_overrides: Dict[str, str] = {}
    idx = 0
    while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
        k, v = tokens[idx].split("=", 1)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
            env_overrides[k] = v
            idx += 1
        else:
            break
    argv = tokens[idx:]
    return (argv, env_overrides)


def run_command(cmd: str, cwd: Path, timeout: int = 300) -> Tuple[bool, str, float]:
    """Ejecuta la evidencia con `shell=False` y lista blanca de ejecutables. Fail-closed."""
    import tempfile

    t0 = time.perf_counter()
    if not cmd or not cmd.strip():
        return (False, "EVIDENCE_MISSING: claim sin comando de evidencia ejecutable", 0.0)
    for pattern in DISALLOWED_SHELL_PATTERNS:
        if pattern.search(cmd):
            return (False, f"SECURITY_POLICY_REJECTED: token prohibido {pattern.pattern}", 0.0)
    if any(tok in cmd for tok in [";", "|", "`", ">", "<"]):
        return (False, "SECURITY_POLICY_REJECTED: operador de shell no permitido", 0.0)
    try:
        steps = [s.strip() for s in cmd.split("&&") if s.strip()]
        combined_outputs: List[str] = []
        with tempfile.TemporaryDirectory(prefix="b60_claim_") as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            persisted_env: Dict[str, str] = {}
            for step in steps:
                argv, step_env = _parse_safe_step(step, tmp_dir)
                persisted_env.update(step_env)
                if not argv:
                    continue
                exe = Path(argv[0]).name
                if exe not in ALLOWED_CLAIM_EXECUTABLES:
                    return (
                        False,
                        f"SECURITY_POLICY_REJECTED: ejecutable no permitido '{exe}'",
                        time.perf_counter() - t0,
                    )
                run_env = os.environ.copy()
                run_env.update(persisted_env)
                res = subprocess.run(
                    argv,
                    shell=False,
                    cwd=str(cwd),
                    env=run_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                )
                step_out = (res.stdout + "\n" + res.stderr).strip()
                if step_out:
                    combined_outputs.append(step_out)
                if res.returncode != 0:
                    return (False, "\n".join(combined_outputs), time.perf_counter() - t0)
        duration = time.perf_counter() - t0
        output = "\n".join(combined_outputs).strip()
        executed = count_executed_tests(output)
        if executed == 0:
            return (False, "VACUOUS_EVIDENCE: el comando salió con 0 pero ejecutó 0 tests", duration)
        return (True, output, duration)
    except Exception as e:
        duration = time.perf_counter() - t0
        return (False, str(e), duration)


def main() -> int:
    repo_root = Path(__file__).absolute().parent.parent.parent
    claims_file = repo_root / "CLAIMS.toml"

    if not claims_file.exists():
        print(f"[FATAL] No se encontró {claims_file}")
        return 1

    content = claims_file.read_text(encoding="utf-8")
    if tomllib is not None:
        manifest = tomllib.loads(content)
    else:
        manifest = parse_simple_toml(content)

    claims = manifest.get("claim", {})
    metadata = manifest.get("metadata", {})
    list_only = "--list" in sys.argv

    if list_only:
        for cid, c in sorted(claims.items()):
            cmd = c.get("evidence_suite", c.get("evidence", ""))
            req = " [REQUIRED]" if c.get("required_for_release", False) else ""
            lvl = c.get("evidence_level", "UNSPECIFIED")
            print(f"[DECLARED] {cid}{req}  (declared: {c.get('status', 'unknown')} | level: {lvl})")
            print(f"    statement : {c.get('statement', '')}")
            print(f"    evidence  : {cmd or '<none>'}")
        print("Declared claims listed. No outcome asserted.")
        return 0

    print("=" * 80)
    print("BABYLON-60 · AUDITORÍA DE CLAIMS EN SILICIO (SWARM-21 / v5.0 · ITERACIÓN Ω)")
    print(f"Raíz Axiomática: {metadata.get('root_axiom', 'N/A')}")
    print(f"Total Claims Registrados: {len(claims)}")
    print("=" * 80)

    commit = source_commit(repo_root)
    env_digest, env_info = environment_digest(repo_root)
    manifest_digest = sha256(claims_file.read_bytes())
    tree_digest = source_tree_digest(repo_root)
    redactions = local_path_redactions(repo_root)

    valid_evidence_levels = {"L1_FORMAL", "L2_IMPLEMENTATION", "L3_ISOLATION", "L4_EXPERIMENTAL"}

    results: List[Dict[str, Any]] = []
    verified_count = 0
    experimental_count = 0
    partial_count = 0
    failed_claims: List[str] = []

    for claim_id, data in claims.items():
        statement = data.get("statement", "")
        evidence_cmd = data.get("evidence") or data.get("evidence_suite", "")
        expected_status = data.get("status", "experimental")
        evidence_level = data.get("evidence_level", "L2_IMPLEMENTATION")
        component = data.get("component", "UNKNOWN")
        required = bool(data.get("required_for_release", True))
        notes = data.get("notes", "")
        timeout = int(data.get("timeout_seconds", 300))

        print(f"\n[CLAIM] {claim_id} ({component}) [{evidence_level}]")
        print(f"  Declaración : {statement}")
        print(f"  Evidencia   : {evidence_cmd}")

        if evidence_level not in valid_evidence_levels:
            print(f"  Dictamen    : [NIVEL DE EVIDENCIA INVÁLIDO: {evidence_level}]")
            failed_claims.append(claim_id)
            continue

        if expected_status in ["partial_trace", "verified_in_memory", "verified_local"]:
            executed_ok, out, dur = run_command(evidence_cmd, repo_root, timeout=timeout)
            if not executed_ok:
                error_summary = extract_failure_summary(out, redactions=redactions)
                print(f"  Dictamen    : [FALLO DE EVIDENCIA -> EXPERIMENTAL] ({dur:.2f}s)")
                print("  Error Detalle:\n" + textwrap.indent(error_summary, "    "))
                experimental_count += 1
                if required or expected_status != "experimental":
                    failed_claims.append(claim_id)
                results.append(
                    {
                        "id": claim_id,
                        "statement": statement,
                        "status": "experimental",
                        "evidence_level": evidence_level,
                        "verified": False,
                        "suite_passed": False,
                        "duration_s": round(dur, 3),
                        "component": component,
                        "error": error_summary,
                    }
                )
                continue
            print(
                f"  Estado Base : {expected_status.upper()} [{evidence_level}] (evidencia ejecutada OK, {dur:.2f}s; alcance acotado)"
            )
            if notes:
                print(f"  Nota Causal : {notes}")
            partial_count += 1
            results.append(
                {
                    "id": claim_id,
                    "statement": statement,
                    "status": expected_status,
                    "evidence_level": evidence_level,
                    "verified": False,
                    "suite_passed": True,
                    "duration_s": round(dur, 3),
                    "component": component,
                }
            )
            continue

        success, out, dur = run_command(evidence_cmd, repo_root, timeout=timeout)

        if success:
            print(f"  Dictamen    : [VERIFICADO EN SILICIO · {evidence_level}] ({dur:.2f}s)")
            verified_count += 1
            results.append(
                {
                    "id": claim_id,
                    "statement": statement,
                    "status": "verified",
                    "evidence_level": evidence_level,
                    "verified": True,
                    "suite_passed": True,
                    "duration_s": round(dur, 3),
                    "component": component,
                }
            )
        else:
            error_summary = extract_failure_summary(out, redactions=redactions)
            print(f"  Dictamen    : [FALLO DE EVIDENCIA -> EXPERIMENTAL] ({dur:.2f}s)")
            print("  Error Detalle:\n" + textwrap.indent(error_summary, "    "))
            experimental_count += 1
            if required or expected_status != "experimental":
                failed_claims.append(claim_id)
            results.append(
                {
                    "id": claim_id,
                    "statement": statement,
                    "status": "experimental",
                    "evidence_level": evidence_level,
                    "verified": False,
                    "suite_passed": False,
                    "duration_s": round(dur, 3),
                    "component": component,
                    "error": error_summary,
                }
            )

    print("\n" + "=" * 80)
    print("RESUMEN EPISÓDICO DE VERIFICACIÓN (CLAIMS.toml)")
    print(f"  Verificados Rigurosos : {verified_count}")
    print(f"  Acotados / Parciales  : {partial_count}")
    print(f"  Degradados a Experim. : {experimental_count}")
    print(f"  Total Auditados       : {len(claims)}")
    print("=" * 80)

    sitrep_path = repo_root / "scripts" / "c5_quality_gates" / "claims_sitrep.json"
    sitrep_path.write_text(
        json.dumps(
            {
                "timestamp": time.time(),
                "source_commit": commit,
                "source_tree_digest": tree_digest,
                "environment_digest": env_digest,
                "environment": env_info,
                "claims_manifest_digest": manifest_digest,
                "total_claims": len(claims),
                "verified": verified_count,
                "partial": partial_count,
                "experimental": experimental_count,
                "failed_claims": failed_claims,
                "claims": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[✓] Sitrep criptográfico exportado a: {sitrep_path.relative_to(repo_root)}")

    if failed_claims:
        print(
            f"[FAIL-CLOSED] {len(failed_claims)} claim(s) fallaron su evidencia en silicio: {', '.join(failed_claims)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
