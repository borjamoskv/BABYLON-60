"""test_audit_subagents.py.

Verificación y Falsación en Silicio del Linter de Subagentes (Anti-Hang R1 Gate).
"""

import json
import subprocess
import sys
from pathlib import Path

# Asegurar raíz de proyecto en sys.path
PROJECT_ROOT = Path(__file__).absolute().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.c5_quality_gates.audit_subagent_declarations import (  # noqa: E402
    audit_subagent,
    parse_subagent_file,
)


def test_all_subagent_invariants():
    print("=== TEST SUITE: AUDITORÍA DE SUBAGENTES (ANTI-HANG R1 GATE) ===")
    tmp_dir = Path("/tmp/c5_subagent_test_harness")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Test subagente válido
    valid_content = """---
name: code-reviewer
description: Realiza revisiones estáticas de código y seguridad.
tools:
  - view_file
  - grep_search
  - run_command
mainAgent: true
subagent: true
model: pro
commandExecutionPolicy: sandbox
---
# System Prompt
Eres un revisor estricto.
"""
    p1 = tmp_dir / "code-reviewer.md"
    p1.write_text(valid_content, encoding="utf-8")
    fm, body, err = parse_subagent_file(p1)
    assert err is None
    assert fm is not None
    findings = audit_subagent(p1, fm, body)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert len(errors) == 0, f"Subagente válido tuvo errores: {errors}"
    print("  [PASS] Test 1: Subagente conforme pasa sin errores.")

    # 2. Test herramientas con erratas que causan R1 Hang Bug
    bad_content = """---
name: bad-agent
description: Agente con herramientas erróneas.
tools:
  - read_file
  - edit_file
  - bash
  - unknown_tool_xyz
---
# System Prompt
Instrucciones.
"""
    p2 = tmp_dir / "bad-agent.md"
    p2.write_text(bad_content, encoding="utf-8")
    fm, body, err = parse_subagent_file(p2)
    assert err is None
    findings = audit_subagent(p2, fm, body)
    errors = [f for f in findings if f.severity == "ERROR"]
    r1_errors = [e for e in errors if e.rule == "R1_HANG_UNMAPPED_TOOL"]
    assert len(r1_errors) == 4, f"Se esperaban 4 errores R1, se obtuvieron: {len(r1_errors)}"
    msg_combined = " ".join(e.remediation for e in r1_errors)
    assert "view_file" in msg_combined
    assert "replace_file_content" in msg_combined
    assert "run_command" in msg_combined
    print("  [PASS] Test 2: Detección exhaustiva de herramientas no mapeadas (R1 Hang Bug).")

    # 3. Test confinamiento de nodo hoja (d=1 limit)
    leaf_content = """---
name: moskvbot
description: Scavenger de borde.
tools:
  - view_file
  - search_web
  - invoke_subagent
mainAgent: false
subagent: true
---
# System Prompt
Eres moskvbot.
"""
    p3 = tmp_dir / "moskvbot.md"
    p3.write_text(leaf_content, encoding="utf-8")
    fm, body, err = parse_subagent_file(p3)
    findings = audit_subagent(p3, fm, body)
    errors = [f for f in findings if f.severity == "ERROR"]
    leaf_errors = [e for e in errors if e.rule == "LEAF_NODE_CONFINEMENT_D1"]
    assert len(leaf_errors) == 1
    assert "d=1 limit" in leaf_errors[0].message
    print("  [PASS] Test 3: Confinamiento de nodo hoja moskvbot (d=1) verificado.")

    # 4. Test modelo y política inválida
    inv_content = """---
name: invalid-agent
description: Configuración inválida.
tools:
  - view_file
model: gpt-4-turbo
commandExecutionPolicy: unconfined
---
# System
"""
    p4 = tmp_dir / "invalid-agent.md"
    p4.write_text(inv_content, encoding="utf-8")
    fm, body, err = parse_subagent_file(p4)
    findings = audit_subagent(p4, fm, body)
    rules = {f.rule for f in findings}
    assert "INVALID_MODEL_TIER" in rules
    assert "INVALID_COMMAND_POLICY" in rules
    print("  [PASS] Test 4: Rechazo de tiers de modelo y políticas no permitidas verificado.")

    # 5. Test CLI con salida JSON
    script_path = Path("scripts/c5_quality_gates/audit_subagent_declarations.py").absolute()
    res = subprocess.run(
        [sys.executable, str(script_path), "--global-only", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "status" in data
    assert data["status"] == "PASS"
    print("  [PASS] Test 5: Invocación CLI con --json verificada en subagentes globales.")

    print("\n[VEREDICTO]: TODOS LOS TESTS DE SILICIO PASARON (EXIT 0)")


if __name__ == "__main__":
    test_all_subagent_invariants()
