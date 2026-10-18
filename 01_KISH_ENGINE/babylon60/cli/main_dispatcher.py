# -*- coding: utf-8 -*-
"""
BABYLON-60 Sovereign Trust Kernel — Root CLI Dispatcher (C5-REAL / v5.0)
Root entrypoint for human operators and systems.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

VERSION = "5.0.0"
BABYLON_BASE_PATH = Path(os.getenv("BABYLON_HOME", str(Path.home() / ".babylon60")))
DEFAULT_CAUSAL_GATE_PATH = Path(
    os.getenv(
        "BABYLON_CAUSAL_GATE_DB",
        str(Path(__file__).resolve().parents[3] / ".cortex" / "causal_gate.db"),
    )
)
DEFAULT_LEDGER_PATH = BABYLON_BASE_PATH / "mcp_ledger.db"

# Bootstrap import path when run from repository checkout
_pkg_root = Path(__file__).resolve().parent.parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))


def cmd_status(args: argparse.Namespace) -> int:
    """Print kernel status, ledger state, and active claims."""
    print("=" * 60)
    print(f"BABYLON-60 Sovereign Trust Kernel v{VERSION}")
    print("Root Axiom: AX-0 (proposer != authorizer)")
    print("=" * 60)
    print(f"Base Directory: {BABYLON_BASE_PATH}")
    print(
        f"Causal Gate DB: {DEFAULT_CAUSAL_GATE_PATH} ({'EXISTS' if DEFAULT_CAUSAL_GATE_PATH.exists() else 'NOT FOUND'})"
    )
    print(f"BFT Ledger DB:  {DEFAULT_LEDGER_PATH} ({'EXISTS' if DEFAULT_LEDGER_PATH.exists() else 'NOT FOUND'})")

    from babylon60.verification.verification_gate import VerificationGate

    gate = VerificationGate(db_path=str(DEFAULT_CAUSAL_GATE_PATH))
    integrity = gate.verify_ledger_integrity()
    print(f"Gate Integrity: {'🟢 OK (Chain Verified)' if integrity else '🔴 CORRUPT / EMPTY'}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """Register an out-of-band operator authorization for a protected execution."""
    from babylon60.verification.verification_gate import InterventionChannel, RiskLevel, VerificationGate

    import json

    gate_path = Path(args.db) if args.db else DEFAULT_CAUSAL_GATE_PATH
    if args.decision == "REJECTED":
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate = VerificationGate(db_path=str(gate_path))
        gate.register_sign_off(
            args.execution_id, args.action or "revoke", RiskLevel.CRITICAL, "REJECTED", InterventionChannel.HARD_SURGERY
        )
        print("Authorization revoked.")
        return 0
    try:
        if not getattr(args, "task_file", None):
            raise ValueError("Approval requires --task-file with the complete proposed task")
        task = json.loads(Path(args.task_file).read_text())
        if not isinstance(task, dict) or task.get("execution_id") != args.execution_id:
            raise ValueError("Task execution_id does not match")
        action = task.get("action")
        if not isinstance(action, str) or not action or (args.action and args.action != action):
            raise ValueError("Task action is missing or does not match --action")
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate = VerificationGate(db_path=str(gate_path))
        if not gate.enforce_biometric_sign_off(args.execution_id, action, "Approve exact task", task_payload=task):
            print("Authorization denied: valid biometric evidence from the configured authority is required.")
            return 1
    except (OSError, ValueError) as exc:
        print(f"Authorization denied: {exc}")
        return 1
    print(f"Signed authorization registered for {args.execution_id}: {action} (valid for at most 300s).")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify causal gate and BFT ledger integrity."""
    from babylon60.verification.verification_gate import VerificationGate

    gate_path = Path(args.db) if args.db else DEFAULT_CAUSAL_GATE_PATH
    gate = VerificationGate(db_path=str(gate_path))
    ok = gate.verify_ledger_integrity()
    if ok:
        print(f"🟢 Causal Gate Ledger at {gate_path}: SHA-256 chain verified.")
        return 0
    else:
        print(f"🔴 Causal Gate Ledger at {gate_path}: integrity check failed.", file=sys.stderr)
        return 1


def cmd_onco(args: argparse.Namespace) -> int:
    """Delegate to Oncology / Boolean Network Transducer."""
    from babylon60.cli.onco_transducer import main as onco_main

    sys.argv = [sys.argv[0]] + (args.onco_args or [])
    onco_main()
    return 0


def cmd_compliance(args: argparse.Namespace) -> int:
    """Delegate to EU AI Act Compliance Exporter."""
    from babylon60.compliance_exporter.eu_ai_act import main_cli as compliance_main

    sys.argv = [sys.argv[0]] + (args.compliance_args or [])
    return int(compliance_main() or 0)


def cmd_license(args: argparse.Namespace) -> int:
    """Delegate to Sovereign License CLI."""
    from babylon60.cli.license_cli import main as license_main

    sys.argv = [sys.argv[0]] + (args.license_args or [])
    license_main()
    return 0


def cmd_bridge(args: argparse.Namespace) -> int:
    """Delegate to Sovereign Bridge CLI."""
    from babylon60.cli.bridge import main as bridge_main

    argv = [sys.argv[0]]
    if getattr(args, "action", None):
        argv.append(str(args.action))
    if getattr(args, "status", False):
        argv.append("--status")
    if getattr(args, "check", False):
        argv.append("--check")
    if getattr(args, "bridge_args", None):
        argv.extend(args.bridge_args)
    sys.argv = argv
    bridge_main()
    return 0


def cmd_attest(args: argparse.Namespace) -> int:
    """Delegate to LLM Attestation CLI."""
    from babylon60.cli.llm_attest import main as attest_main

    sys.argv = [sys.argv[0]] + (args.attest_args or [])
    attest_main()
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    """Run Cortex MCP server."""
    from babylon60.mcp.cortex_mcp_server import main as mcp_main

    sys.argv = [sys.argv[0]] + (getattr(args, "mcp_args", None) or [])
    mcp_main()
    return 0


def cmd_mcp_bomb(args: argparse.Namespace) -> int:
    """Synthesize, execute over stdio sandbox, and detonate a single-use ephemeral MCP (Burn-After-Use)."""
    import json
    from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager

    raw_args = getattr(args, "args", "{}")
    try:
        call_arguments = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
    except Exception as exc:
        print(f"[🔴 ERROR] Argumentos inválidos (debe ser JSON): {exc}")
        return 1

    lifecycle = McpLifecycleManager()
    receipt = lifecycle.synthesize_and_detonate_bomb(
        domain_name=args.domain,
        implementation_body=args.code,
        call_arguments=call_arguments,
        description=getattr(args, "desc", None),
        timeout_seconds=float(getattr(args, "timeout", 5.0)),
    )

    as_json = bool(getattr(args, "json", False))
    if as_json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    else:
        status_icon = "🟢" if receipt.get("status") == "SUCCESS" else "🔴"
        print(f"{status_icon} [MCP BOMBA] Servidor: {receipt.get('server_name')} -> Tool: {receipt.get('tool_name')}")
        print(f"   Status:                 {receipt.get('status')}")
        print(f"   Code Hash (BLAKE3):     {receipt.get('code_hash')}")
        print(
            f"   Autodestrucción (Disk): {'✓ VERIFICADA (CERO HUELLA)' if receipt.get('self_destruct_verified') else '✗ FALLIDA'}"
        )
        print(f"   Latencia:               {receipt.get('latency_ms', 0):.2f} ms")
        print(f"   Resultado:              {json.dumps(receipt.get('tool_output'), ensure_ascii=False)}")

    return 0 if receipt.get("status") == "SUCCESS" else 1


def cmd_tools(args: argparse.Namespace) -> int:
    """Inspect all MCP tools and resources exposed by Cortex BFT and Kernel Harness servers."""
    import json

    from babylon60.mcp.cortex_mcp_server import RESOURCES, TOOLS

    server_filter = getattr(args, "server", "all")
    as_json = bool(getattr(args, "json", False))

    cortex_tools: list[dict[str, object]] = []
    if server_filter in {"all", "cortex"}:
        for t in TOOLS:
            desc = str(t.get("description", ""))
            clean_desc = desc.split("] ", 1)[-1] if desc.startswith("[Alias:") else desc
            name = str(t.get("name", ""))
            cortex_tools.append(
                {
                    "server": "cortex",
                    "canonical_alias": str(t.get("canonical_alias", name)),
                    "name": name,
                    "read_only": name
                    in {
                        "bft_query_ledger",
                        "bft_verify_merkle_root",
                        "causal_evaluate_task_risk",
                        "causal_verify_ledger",
                    },
                    "summary": clean_desc.split(". ")[0] + ".",
                }
            )
        cortex_tools.append(
            {
                "server": "cortex",
                "canonical_alias": "cortex_mail_send",
                "name": "bft_send_sovereign_mail",
                "read_only": False,
                "summary": "Record and dispatch an immutable sovereign mail event (optional --mail-ledger).",
            }
        )

    kernel_tools: list[dict[str, object]] = []
    if server_filter in {"all", "kernel"}:
        kernel_specs = [
            (
                "kernel_source_read",
                "read_source",
                True,
                "Read up to 200 lines of a tracked source file with BLAKE3 revision.",
            ),
            (
                "kernel_patch_apply",
                "apply_atomic_patch",
                False,
                "Replace one exact block guarded by an expected BLAKE3 revision (--allow-patches).",
            ),
            (
                "kernel_tests_run",
                "run_nemesis_and_cargo",
                False,
                "Run adversarial_nemesis target in offline/locked mode (--allow-execution).",
            ),
            (
                "kernel_miri_audit",
                "audit_spsc_miri_arm64",
                False,
                "Run NEMESIS SPSC tests under Miri for aarch64-apple-darwin with strict provenance.",
            ),
            (
                "kernel_lean4_verify",
                "verify_lean4_bijection",
                False,
                "Preflight tracked proof/lean sources for forbidden tokens and run Lake build.",
            ),
            (
                "kernel_sqlite_inspect",
                "inspect_sqlite_l0_invariants",
                True,
                "Inspect an offline checkpointed SQLite export in memory without WAL/SHM sidecars.",
            ),
        ]
        for alias, legacy, ro, summary in kernel_specs:
            kernel_tools.append(
                {
                    "server": "kernel",
                    "canonical_alias": alias,
                    "name": legacy,
                    "read_only": ro,
                    "summary": summary,
                }
            )

    all_tools = cortex_tools + kernel_tools
    resources_list = (
        [
            {
                "canonical_alias": str(r.get("canonical_alias", r["uri"])),
                "uri": str(r["uri"]),
                "name": str(r["name"]),
                "mimeType": str(r["mimeType"]),
            }
            for r in RESOURCES
        ]
        if server_filter in {"all", "cortex"}
        else []
    )

    if as_json:
        print(json.dumps({"tools": all_tools, "resources": resources_list}, indent=2, ensure_ascii=False))
        return 0

    print("=" * 92)
    print(f"BABYLON-60 MCP TOOL & RESOURCE CATALOG v{VERSION} (B1: Canonical Alias <-> Legacy Name)")
    print("=" * 92)
    print(f"{'SERVER':<8} | {'CANONICAL ALIAS':<28} | {'LEGACY NAME':<28} | {'MODE':<6}")
    print("-" * 92)
    for item in all_tools:
        mode = "RO" if item["read_only"] else "RW/EX"
        print(f"{str(item['server']):<8} | {str(item['canonical_alias']):<28} | {str(item['name']):<28} | {mode:<6}")
    if resources_list:
        print("-" * 92)
        print("MCP RESOURCES (cortex):")
        for r in resources_list:
            print(f"  • {r['canonical_alias']:<28} (legacy: {r['uri']}) — {r['name']}")
    print("=" * 92)
    return 0


def cmd_skills(args: argparse.Namespace) -> int:
    """Inspect, list, and route CORTEX declarative skills (SKILL.md fleet)."""
    import json
    import re
    import yaml

    repo_root = Path(__file__).resolve().parents[3]
    ws_skills_dir = repo_root / ".agents" / "skills"
    skills_json_path = repo_root / "docs" / "skills.json"

    scope_filter = getattr(args, "scope", "workspace")
    role_filter = getattr(args, "role", "all")
    query = getattr(args, "query", None)
    action = getattr(args, "skills_action", None) or ("route" if query else "status")
    as_json = bool(getattr(args, "json", False))

    loaded_skills: dict[str, dict[str, object]] = {}
    adjacency_count = 0

    # 1. Load workspace skills from .agents/skills/*/SKILL.md
    if ws_skills_dir.exists():
        for skill_dir in sorted(ws_skills_dir.iterdir()):
            md_path = skill_dir / "SKILL.md"
            if not (skill_dir.is_dir() and md_path.exists()):
                continue
            text = md_path.read_text(encoding="utf-8", errors="ignore")
            fm: dict[str, object] = {}
            parts = text.split("---", 2)
            if text.startswith("---") and len(parts) >= 3:
                parsed = yaml.safe_load(parts[1])
                if isinstance(parsed, dict):
                    fm = parsed
            name = str(fm.get("name", skill_dir.name))
            canonical_alias = str(fm.get("canonical_alias", "")).strip()
            desc = str(fm.get("description", ""))
            role = str(fm.get("role", "ejecutor"))
            raw_directives = fm.get("directives")
            directives: dict[str, object] = raw_directives if isinstance(raw_directives, dict) else {}
            phase = str(directives.get("phase", "implementation"))
            worktree_mode = str(directives.get("worktree_mode", "read-write"))
            raw_handoff = directives.get("handoff")
            handoff: dict[str, object] = raw_handoff if isinstance(raw_handoff, dict) else {}
            upstream = str(handoff.get("upstream", "operador"))
            downstream = str(handoff.get("downstream", "auditor"))

            triggers: set[str] = {name.lower()}
            if canonical_alias:
                triggers.add(canonical_alias.lower())
            disp_m = re.search(r"(?:dispara con|triggers?|disparadores)[\s:]*([^\n]+)", desc, re.IGNORECASE)
            if disp_m:
                triggers.update(
                    q.strip().lower() for q in re.findall(r"[\"']([^\"']+)[\"']", disp_m.group(1)) if len(q.strip()) > 2
                )

            loaded_skills[name] = {
                "name": name,
                "canonical_alias": canonical_alias,
                "display_name": str(fm.get("display_name", name)),
                "description": desc,
                "role": role,
                "scope": "workspace",
                "phase": phase,
                "worktree_mode": worktree_mode,
                "upstream": upstream,
                "downstream": downstream,
                "path": str(md_path.relative_to(repo_root)),
                "triggers": sorted(triggers),
            }

    # 2. Enrich with catalog entries from docs/skills.json when scope != workspace
    if skills_json_path.exists():
        try:
            catalog = json.loads(skills_json_path.read_text(encoding="utf-8"))
            adjacency_count = len(catalog.get("adjacency", []))
            entries = catalog.get("entries", []) if scope_filter != "workspace" else []
            for entry in entries:
                ename = str(entry.get("name", ""))
                if not ename or ename in loaded_skills:
                    continue
                escope = str(entry.get("scope", "global"))
                ealias = str(entry.get("canonical_alias", ename))
                edesc = str(entry.get("description", ""))
                etrigs = [str(t).lower() for t in entry.get("triggers", [])]
                if ealias.lower() not in etrigs:
                    etrigs.append(ealias.lower())
                loaded_skills[ename] = {
                    "name": ename,
                    "canonical_alias": ealias,
                    "display_name": str(entry.get("display_name", ename)),
                    "description": edesc,
                    "role": str(entry.get("role", "ejecutor")),
                    "scope": escope,
                    "phase": "catalog",
                    "worktree_mode": "read-only",
                    "upstream": "operador",
                    "downstream": "auditor",
                    "path": str(entry.get("path", "")),
                    "triggers": etrigs,
                }
        except Exception:
            pass

    if action == "route":
        if not query:
            print("Error: 'babylon60 skills route' requires --query <intent>.", file=sys.stderr)
            return 1
        q_norm = query.lower().strip()
        q_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", q_norm))
        best_skill: dict[str, object] | None = None
        best_score = 0.0
        for s in loaded_skills.values():
            if scope_filter != "all" and s["scope"] != scope_filter:
                continue
            score = 0.0
            if q_norm in {str(s["name"]).lower(), str(s["canonical_alias"]).lower()}:
                score += 50.0
            for trig in cast_str_list(s.get("triggers", [])):
                if trig in q_norm:
                    score += 15.0
                else:
                    common = set(trig.split()).intersection(q_words)
                    score += len(common) * 3.0
            name_words = set(str(s["name"]).replace("-", " ").split()) | set(
                str(s["canonical_alias"]).replace("-", " ").split()
            )
            score += len(name_words.intersection(q_words)) * 2.5
            desc_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", str(s["description"]).lower()))
            score += len(desc_words.intersection(q_words)) * 0.5
            if score > best_score:
                best_score = score
                best_skill = s

        if not best_skill:
            if as_json:
                print(json.dumps({"query": query, "elected": None}, indent=2, ensure_ascii=False))
            else:
                print(f"[!] No skill matched query: {query}")
            return 1
        alias_out = str(best_skill["canonical_alias"] or best_skill["name"])
        payload = {
            "query": query,
            "name": best_skill["name"],
            "canonical_alias": alias_out,
            "display_name": best_skill["display_name"],
            "role": best_skill["role"],
            "scope": best_skill["scope"],
            "phase": best_skill["phase"],
            "worktree_mode": best_skill["worktree_mode"],
            "handoff": {"upstream": best_skill["upstream"], "downstream": best_skill["downstream"]},
            "path": best_skill["path"],
        }
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"[+] Intent:          {query}")
            print(f"[+] Elected Skill:   {alias_out} (id: {best_skill['name']})")
            print(f"[+] Role / Phase:    {best_skill['role']} / {best_skill['phase']} ({best_skill['worktree_mode']})")
            print(f"[+] Scope / Path:    {best_skill['scope']} ({best_skill['path']})")
            print(
                f"[+] Handoff Chain:   {best_skill['upstream']} -> {best_skill['role']} -> {best_skill['downstream']}"
            )
        return 0

    skills = list(loaded_skills.values())
    if scope_filter != "all":
        skills = [s for s in skills if s["scope"] == scope_filter]
    if role_filter != "all":
        skills = [s for s in skills if s["role"] == role_filter]
    skills.sort(key=lambda s: (str(s["scope"]), str(s["canonical_alias"] or s["name"])))

    if action == "list":
        items = [
            {
                "name": s["name"],
                "canonical_alias": s["canonical_alias"] or s["name"],
                "role": s["role"],
                "scope": s["scope"],
                "phase": s["phase"],
                "worktree_mode": s["worktree_mode"],
            }
            for s in skills
        ]
        if as_json:
            print(json.dumps({"total": len(items), "skills": items}, indent=2, ensure_ascii=False))
            return 0
        print("=" * 96)
        print(f"BABYLON-60 CORTEX SKILLS FLEET ({len(items)} matched)")
        print("=" * 96)
        print(f"{'CANONICAL ALIAS':<32} | {'SKILL ID (NAME)':<34} | {'ROLE':<10} | {'SCOPE':<9}")
        print("-" * 96)
        for item in items:
            print(
                f"{str(item['canonical_alias']):<32} | {str(item['name']):<34} | "
                f"{str(item['role']):<10} | {str(item['scope']):<9}"
            )
        print("=" * 96)
        return 0

    # Default: status
    by_scope: dict[str, int] = {}
    by_role: dict[str, int] = {}
    ws_total = 0
    ws_aliased = 0
    for s in skills:
        sc = str(s["scope"])
        rl = str(s["role"])
        by_scope[sc] = by_scope.get(sc, 0) + 1
        by_role[rl] = by_role.get(rl, 0) + 1
        if sc == "workspace":
            ws_total += 1
            if s["canonical_alias"]:
                ws_aliased += 1

    status_payload = {
        "total_skills": len(skills),
        "by_scope": by_scope,
        "by_role": by_role,
        "workspace_canonical_alias_coverage": f"{ws_aliased}/{ws_total}",
        "functorial_dag_edges": adjacency_count,
    }
    if as_json:
        print(json.dumps(status_payload, indent=2, ensure_ascii=False))
        return 0

    print("=" * 64)
    print("BABYLON-60 CORTEX DECLARATIVE SKILLS STATUS")
    print("=" * 64)
    print(f"Total Loaded Skills:          {len(skills)}")
    print(f"Workspace Canonical Aliases:  {ws_aliased}/{ws_total}")
    print(f"Functorial Handoff DAG Edges: {status_payload['functorial_dag_edges']}")
    print("By Scope:                     " + ", ".join(f"{k}={v}" for k, v in sorted(by_scope.items())))
    print("By Role:                      " + ", ".join(f"{k}={v}" for k, v in sorted(by_role.items())))
    print("=" * 64)
    return 0


def cast_str_list(val: object) -> list[str]:
    if isinstance(val, list):
        return [str(x) for x in val]
    return []


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Run Exergy Dashboard server."""
    from babylon60.dashboard.server import main as dash_main

    dash_main()
    return 0


def cmd_autodidact(args: argparse.Namespace) -> int:
    """Run AUTODIDACT-Ω Epistemic Engine (C5-REAL)."""
    from babylon60.autodidact import AutodidactOmegaEngine, Modality, Obligation

    engine = AutodidactOmegaEngine()

    if args.action == "status":
        st = engine.status()
        print("=" * 60)
        print("AUTODIDACT-Ω Sovereign Engine Status (C5-REAL)")
        print("=" * 60)
        print(f"Active Statements:       {st['active_statements']}")
        print(f"Verified Statements:     {st['verified_statements']}")
        print(f"Falsified Nogoods:       {st['falsified_nogoods']}")
        print(f"Falsification Tests Run: {st['falsification_tests_run']}")
        print(f"Native Cortex Bridge:    {'ENABLED' if st['native_cortex_bridge'] else 'FALLBACK (PURE PYTHON)'}")
        print(f"Native Hume Guillotine:  {'ENABLED' if st.get('native_hume_guillotine') else 'FALLBACK'}")
        print(f"Native Statement Hasher: {'ENABLED' if st.get('native_statement_hasher') else 'FALLBACK'}")
        return 0

    elif args.action == "falsify":
        claim = args.claim
        print(f"[*] Sometiendo a falsación Popperiana: '{claim}'")
        # Test canario: evaluación determinista de expresión o claim
        expr = args.expr
        test_fn = (lambda: eval(expr)) if expr else (lambda: True)
        expected = args.expected
        verdict = engine.falsifier.falsify_assertion(
            engine.assert_hypothesis(claim, Modality.EPISTEMIC).statement,
            test_fn=test_fn,
            expected_output=eval(expected) if expected else None,
        )
        print(f"[+] Veredicto: {verdict.verdict}")
        print(f"[+] Nodo Contradicción: {verdict.contradiction_node or 'None'}")
        print(f"[+] Telemetría: {verdict.telemetry}")
        return 0 if not verdict.falsified else 1

    elif args.action == "research":
        topic = args.topic
        print(f"[*] Iniciando investigación AUTODIDACT-Ω sobre: '{topic}'")
        if getattr(args, "query_arxiv", False):
            print("[*] Consultando literatura en arXiv y repositorio local...")
            evidences = engine.fetch_literature(topic, max_results=3, query_arxiv=True)
            print(f"[+] Evidencias recolectadas: {len(evidences)}")
            for idx, ev in enumerate(evidences, 1):
                p = ev.raw_payload
                if isinstance(p, dict) and "title" in p:
                    engine.assert_hypothesis(
                        content=f"Literatura #{idx} ({p.get('arxiv_id', 'local')}): {p.get('title')}",
                        modality=Modality.EPISTEMIC,
                        obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY],
                    )

        engine.assert_hypothesis(
            content=f"El dominio '{topic}' exhibe propiedades de conservación exergética.",
            modality=Modality.EPISTEMIC,
            obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY],
        )
        engine.assert_hypothesis(
            content=f"La compresión de estados en '{topic}' converge asintóticamente al límite de Fisher.",
            modality=Modality.EPISTEMIC,
            obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY],
        )
        crystal = engine.compile_crystal(topic=topic, thesis=f"Análisis estructural de frontera sobre {topic}.")
        print("[+] Cristal compilado exitosamente.")
        print(f"[+] Merkle Root: {crystal.merkle_root}")
        print(f"[+] Autor: {crystal.author} ({crystal.affiliation})")

        out_md = getattr(args, "output_md", None) or getattr(args, "output", None)
        if out_md:
            with open(out_md, "w", encoding="utf-8") as f:
                f.write(crystal.markdown_content)
            print(f"[+] Cristal Markdown guardado en: {out_md}")

        out_json = getattr(args, "output_json", None)
        if out_json:
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(engine.compiler.export_json(crystal))
            print(f"[+] Cristal JSON canónico guardado en: {out_json}")
        return 0

    elif args.action == "verify-crystal":
        path = args.path
        print(f"[*] Auditando integridad criptográfica del Cristal: {path}")
        from babylon60.autodidact import CrystalCompiler

        is_valid, msg = CrystalCompiler.verify_crystal_integrity(path)
        if is_valid:
            print(f"[🟢 OK] {msg}")
            return 0
        else:
            print(f"[🔴 FAILED] {msg}")
            return 1

    print("Acción no especificada. Usa: babylon60 autodidact {status, research, falsify, verify-crystal}")
    return 1


def cmd_presentation(args: argparse.Namespace) -> int:
    """Print the same presentation contract delivered during MCP initialization."""
    import json

    guide = (Path(__file__).absolute().parents[1] / "presentation.md").read_text(encoding="utf-8")
    if args.json:
        print(
            json.dumps(
                {"uri": "babylon://presentation/guide", "mimeType": "text/markdown", "text": guide},
                ensure_ascii=False,
            )
        )
    else:
        print(guide, end="")
    return 0


def cmd_signature(args: argparse.Namespace) -> int:
    """Render one supplied observation without inferring the active model or host."""
    import json
    from typing import cast

    from babylon60.response_signature import SIGNATURE_SCHEMA, render_signature

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON value: {value}")

    try:
        if args.schema:
            output = json.dumps(SIGNATURE_SCHEMA, ensure_ascii=False, indent=2)
        else:
            if args.input == "-":
                raw = sys.stdin.read()
            else:
                descriptor = os.open(args.input, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(descriptor, "r", encoding="utf-8") as source:
                    raw = source.read()
            payload: object = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
            if not isinstance(payload, dict):
                raise ValueError("signature input must be a JSON object")
            format_name = "text" if args.format == "auto" else args.format
            output = render_signature(cast(dict[str, object], payload), format_name)
            if format_name == "html":
                output = (
                    '<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                    '<meta name="color-scheme" content="light dark">\n'
                    "<title>MOSKV-1 · Firma de respuesta</title>\n</head>\n<body>\n"
                    f"{output}\n</body>\n</html>"
                )
        output = output.rstrip("\n") + "\n"
        if args.output and args.output != "-":
            # Note: .cortex_thermal_lock is not required for local signature HTML export
            encoded = output.encode("utf-8")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(args.output, flags, 0o600)
            with os.fdopen(descriptor, "wb") as destination:
                destination.write(encoded)
        else:
            sys.stdout.write(output)
    except (OSError, ValueError, TypeError) as exc:
        print(f"signature: {exc}", file=sys.stderr)
        return 2
    return 0


def cmd_consolidate21(args: argparse.Namespace) -> int:
    """Execute or inspect the 21-Agent BABYLON-60 Consolidation Topology (BABYLON-21)."""
    import asyncio
    import json

    repo_root = Path(__file__).resolve().parents[3]
    swarms_root = repo_root / "02_EDIN_SWARMS"
    if str(swarms_root) not in sys.path:
        sys.path.insert(0, str(swarms_root))

    from agents_archi.topologies import Babylon21ConsolidationTopology

    topology = Babylon21ConsolidationTopology(max_concurrency=max(1, int(args.concurrency)))
    evaluator = (
        topology.create_subprocess_gate_evaluator(cwd=str(repo_root), timeout_s=float(args.timeout))
        if args.execute
        else None
    )
    receipt = asyncio.run(topology.execute_consolidation(logical_tick=int(args.tick), gate_evaluator=evaluator))

    payload = {
        "logical_tick": receipt.logical_tick,
        "total_agents": receipt.total_agents,
        "verified_count": receipt.verified_count,
        "consolidated": receipt.consolidated,
        "merkle_root_hex": receipt.merkle_root_hex,
        "squad_digests": dict(receipt.squad_digests),
        "failed_agents": list(receipt.failed_agents),
        "outcomes": [
            {
                "agent_id": out.agent_id.value,
                "canonical_name": out.canonical_name,
                "verified": out.verified,
                "evidence_digest": out.evidence_digest,
                "detail": out.detail,
            }
            for out in receipt.outcomes
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        mode_str = "SILICON_SUBPROCESS" if args.execute else "TOPOLOGY_SPEC"
        print(
            f"[BABYLON-21] mode={mode_str} tick={receipt.logical_tick} "
            f"verified={receipt.verified_count}/{receipt.total_agents} "
            f"consolidated={receipt.consolidated} merkle_root={receipt.merkle_root_hex}"
        )
        for out in receipt.outcomes:
            mark = "PASS" if out.verified else "FAIL"
            print(f"  {out.agent_id.value} [{mark}] {out.canonical_name}: {out.detail}")

    return 0 if receipt.consolidated else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="babylon60",
        description=f"BABYLON-60 Sovereign Trust Kernel v{VERSION} (C5-REAL)",
        epilog="Agents: read `babylon60 presentation` for the shared response presentation contract.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    p_consolidate21 = subparsers.add_parser(
        "consolidate-21",
        aliases=["babylon-21", "babylon21"],
        help="Run or inspect the 21-Agent BABYLON-60 Consolidation Swarm (3x7 squads)",
    )
    p_consolidate21.add_argument(
        "--execute",
        action="store_true",
        help="Execute all 21 silicon gate commands in subprocess waves",
    )
    p_consolidate21.add_argument("--tick", type=int, default=60, help="Canonical logical tick (default: 60)")
    p_consolidate21.add_argument("--concurrency", type=int, default=4, help="Max concurrent agents per wave")
    p_consolidate21.add_argument("--timeout", type=float, default=90.0, help="Per-agent gate timeout in seconds")
    p_consolidate21.add_argument("--json", action="store_true", help="Output ConsolidationSealReceipt as JSON")
    p_consolidate21.set_defaults(func=cmd_consolidate21)

    p_presentation = subparsers.add_parser("presentation", help="Read the shared agent presentation contract")
    p_presentation.add_argument("--json", action="store_true", help="Return the contract as structured JSON")
    p_presentation.set_defaults(func=cmd_presentation)

    p_signature = subparsers.add_parser("signature", help="Render a portable signature from observed turn data")
    signature_input = p_signature.add_mutually_exclusive_group(required=True)
    signature_input.add_argument("--input", metavar="FILE", help="Observation JSON file, or - for stdin")
    signature_input.add_argument("--schema", action="store_true", help="Print the JSON input schema")
    p_signature.add_argument(
        "--format",
        choices=["auto", "html", "markdown", "text", "json"],
        default="auto",
        help="Explicit rendering capability; auto uses plain text",
    )
    p_signature.add_argument(
        "--output", metavar="FILE", help="Create a new file exclusively; omitted or - writes to stdout"
    )
    p_signature.set_defaults(func=cmd_signature)

    # status
    p_status = subparsers.add_parser("status", help="Inspect kernel and ledger status")
    p_status.set_defaults(func=cmd_status)

    # approve
    p_approve = subparsers.add_parser("approve", help="Out-of-band operator sign-off for critical actions")
    p_approve.add_argument("execution_id", help="Execution ID being authorized")
    p_approve.add_argument("--action", default="", help="Action name")
    p_approve.add_argument("--decision", choices=["APPROVED", "REJECTED"], default="APPROVED", help="Decision")
    p_approve.add_argument(
        "--risk", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], default="CRITICAL", help="Risk level"
    )
    p_approve.add_argument("--task-file", help="JSON file containing the complete proposed task")
    p_approve.add_argument("--db", default=None, help="Path to causal gate database")
    p_approve.set_defaults(func=cmd_approve)

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify cryptographic integrity of audit ledgers")
    p_verify.add_argument("--db", default=None, help="Path to causal gate database")
    p_verify.set_defaults(func=cmd_verify)

    # onco / boolean-sim
    p_onco = subparsers.add_parser(
        "onco", aliases=["boolean-sim"], help="Run Boolean Network Simulator (Onco Transducer)"
    )
    p_onco.add_argument("onco_args", nargs=argparse.REMAINDER, help="Arguments passed to boolean network simulator")
    p_onco.set_defaults(func=cmd_onco)

    # compliance
    p_compliance = subparsers.add_parser(
        "compliance", help="Generate EU AI Act (Reg. 2024/1689) cryptographic compliance reports"
    )
    p_compliance.add_argument("compliance_args", nargs=argparse.REMAINDER, help="Arguments passed to compliance CLI")
    p_compliance.set_defaults(func=cmd_compliance)

    # license
    p_license = subparsers.add_parser("license", help="Verify and manage Sovereign Dual-License status")
    p_license.add_argument("license_args", nargs=argparse.REMAINDER, help="Arguments passed to license CLI")
    p_license.set_defaults(func=cmd_license)

    # bridge
    p_bridge = subparsers.add_parser("bridge", help="Run Sovereign IPC & Adapter Bridge")
    p_bridge.add_argument(
        "action",
        nargs="?",
        choices=["status", "check", "run"],
        default=None,
        help="Bridge action: status, check, or run",
    )
    p_bridge.add_argument("--status", action="store_true", help="Inspect Sovereign Kernel status")
    p_bridge.add_argument(
        "--check",
        "--dry-run",
        dest="check",
        action="store_true",
        help="Verify Tauri manifest and paths without launching cargo run",
    )
    p_bridge.add_argument("bridge_args", nargs=argparse.REMAINDER, help="Arguments passed to bridge CLI")
    p_bridge.set_defaults(func=cmd_bridge)

    # attest
    p_attest = subparsers.add_parser("attest", help="Generate or verify LLM cryptographic attestations")
    p_attest.add_argument("attest_args", nargs=argparse.REMAINDER, help="Arguments passed to attest CLI")
    p_attest.set_defaults(func=cmd_attest)

    # tools
    p_tools = subparsers.add_parser("tools", help="Inspect MCP tools and resources (canonical <-> legacy names)")
    p_tools.add_argument(
        "--server",
        choices=["all", "cortex", "kernel"],
        default="all",
        help="Filter tools by MCP server (default: all)",
    )
    p_tools.add_argument("--json", action="store_true", help="Output catalog as JSON")
    p_tools.set_defaults(func=cmd_tools)

    # skills
    p_skills = subparsers.add_parser("skills", help="Inspect, list, and route CORTEX declarative skills")
    p_skills.add_argument(
        "skills_action",
        nargs="?",
        choices=["status", "list", "route"],
        default=None,
        help="Action: status (default), list, or route",
    )
    p_skills.add_argument(
        "--scope",
        choices=["all", "workspace", "global", "kernel"],
        default="workspace",
        help="Filter skills by scope (default: workspace)",
    )
    p_skills.add_argument(
        "--role",
        choices=["all", "arquitecto", "ejecutor", "auditor"],
        default="all",
        help="Filter skills by role triad (default: all)",
    )
    p_skills.add_argument("--query", default=None, help="Intent query to route to the optimal skill")
    p_skills.add_argument("--json", action="store_true", help="Output result as JSON")
    p_skills.set_defaults(func=cmd_skills)

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Launch Cortex MCP server over stdio")
    p_mcp.add_argument("mcp_args", nargs=argparse.REMAINDER, help="Arguments forwarded to Cortex MCP server")
    p_mcp.set_defaults(func=cmd_mcp)

    # mcp-bomb
    p_bomb = subparsers.add_parser(
        "mcp-bomb",
        aliases=["bomb"],
        help="Synthesize, execute over isolated stdio, and detonate a single-use MCP (Burn-After-Use)",
    )
    p_bomb.add_argument("--domain", required=True, help="Domain name identifier (e.g. 'PrimeSieve')")
    p_bomb.add_argument("--code", required=True, help="Python implementation body returning result")
    p_bomb.add_argument("--args", default="{}", help="JSON string of tool call arguments")
    p_bomb.add_argument("--desc", default=None, help="Optional tool description")
    p_bomb.add_argument("--timeout", type=float, default=5.0, help="Execution timeout in seconds")
    p_bomb.add_argument("--json", action="store_true", help="Output raw receipt as JSON")
    p_bomb.set_defaults(func=cmd_mcp_bomb)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Start Exergy Dashboard server")
    p_dash.set_defaults(func=cmd_dashboard)

    # autodidact
    p_autodidact = subparsers.add_parser("autodidact", help="AUTODIDACT-Ω Epistemic Engine (C5-REAL)")
    sub_autodidact = p_autodidact.add_subparsers(dest="action", required=True)

    # autodidact status
    p_ad_status = sub_autodidact.add_parser("status", help="Inspect active hypotheses, nogoods and verified theorems")
    p_ad_status.set_defaults(func=cmd_autodidact)

    # autodidact research
    p_ad_research = sub_autodidact.add_parser("research", help="Run autonomous research loop and compile crystal")
    p_ad_research.add_argument("--topic", required=True, help="Research topic or target domain")
    p_ad_research.add_argument("--output", default=None, help="Path to save compiled Epistemic Crystal (.md)")
    p_ad_research.add_argument("--output-md", default=None, help="Path to save compiled Epistemic Crystal Markdown")
    p_ad_research.add_argument("--output-json", default=None, help="Path to save compiled Epistemic Crystal JSON")
    p_ad_research.add_argument("--query-arxiv", action="store_true", help="Fetch primary literature from arXiv")
    p_ad_research.set_defaults(func=cmd_autodidact)

    # autodidact falsify
    p_ad_falsify = sub_autodidact.add_parser("falsify", help="Submit a claim to Popperian silicon falsification")
    p_ad_falsify.add_argument("--claim", required=True, help="Statement or hypothesis to test")
    p_ad_falsify.add_argument("--expr", default=None, help="Python boolean expression to evaluate")
    p_ad_falsify.add_argument("--expected", default=None, help="Expected result of expression")
    p_ad_falsify.set_defaults(func=cmd_autodidact)

    # autodidact verify-crystal
    p_ad_verify = sub_autodidact.add_parser(
        "verify-crystal", help="Verify cryptographic integrity of an Epistemic Crystal (.json or .md)"
    )
    p_ad_verify.add_argument("path", help="Path to Epistemic Crystal file (.json or .md)")
    p_ad_verify.set_defaults(func=cmd_autodidact)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
