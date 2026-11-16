"""Isolated in-memory review fixtures. No product entrypoints or native effects."""

import ast
import asyncio
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]


def load_selected(path, names=None):
    tree = ast.parse((ROOT / path).read_text())
    if names is not None:
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    namespace = {"__name__": "isolated_review_fixture"}
    exec(compile(tree, path, "exec"), namespace)
    return namespace


async def main():
    results = {}
    pager_type = load_selected("scripts/c5_sharur/agent_beeper.py")["AgentPager"]
    pager = pager_type()
    task = asyncio.create_task(pager.wait_for_beep(7))
    await asyncio.sleep(0)
    pager.beep_agent(7, "addressed")
    await asyncio.sleep(0)
    unicast_woke = task.done()
    assert not unicast_woke
    pager.beep_swarm("broadcast")
    after_broadcast = await task
    assert after_broadcast == "addressed"
    results["SW100-C0278"] = {"unicast_woke_waiter": unicast_woke, "result_after_broadcast": after_broadcast}
    first = await pager.wait_for_beep(7)
    second = await pager.wait_for_beep(7)
    assert first == second == "broadcast"
    results["SW100-C0279"] = {"successive_wait_results": [first, second], "scope": "Observed persistent latch; whether reuse is intended remains unvalidated."}

    engine_type = load_selected("01_KISH_ENGINE/babylon60/engine/__init__.py")["CortexEngine"]
    engine = engine_type(capacity=2)
    engine.store_sync("a", "old")
    engine.store_sync("a", "updated")
    before = [(x["key"], x["payload"]) for x in engine.query()]
    engine.store_sync("b", "new")
    after = [(x["key"], x["payload"]) for x in engine.query()]
    assert before == [("a", "updated"), ("a", "updated")]
    assert after == [("b", "new")]
    results["SW100-C0407"] = {"before_eviction": before, "after_eviction": after}

    parse_yaml = load_selected("01_KISH_ENGINE/babylon60/primitives/yaml_parser.py")["parse_yaml"]
    parsed = parse_yaml('color: "#ffffff"\nvalue: "abc#def"\n')
    assert parsed == {"color": "", "value": '"abc'}
    results["SW100-C0313"] = {"parsed": parsed}

    tonnetz_path = "tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/examples/Neo_Riemannian_Tonnetz.py"
    transforms = load_selected(tonnetz_path, {"p_transform", "r_transform"})
    relative, major = transforms["r_transform"]([60, 64, 67], True)
    parallel, major = transforms["p_transform"](relative, major)
    assert relative == [60, 64, 69]
    assert parallel == [60, 65, 69]
    results["SW100-C0058"] = {"relative": relative, "parallel_after_relative": parallel, "expected_a_major_pitch_classes": [1, 4, 9]}

    # Mathematical witness only; does not execute the Rust gate.
    first_bytes = (1).to_bytes(8, "little") + b"ab" + b"c"
    second_bytes = (1).to_bytes(8, "little") + b"a" + b"bc"
    assert first_bytes == second_bytes
    results["SW100-C0477"] = {"same_hash_input": True, "sha256": hashlib.sha256(first_bytes).hexdigest(), "rust_executed": False}

    # Arithmetic witness to the documentary theorem, not product execution.
    score = min(1000, (12 * 12 * 0.01 * 1 * 1) / 0.04 * 0.23)
    assert score < 700
    results["SW100-C0117"] = {"G": 12, "L": 12, "A": 0.01, "B": 1, "P": 1, "M_p": 1, "E_base": 0.04, "T_w": 1, "T_n": 0.23, "score": score}

    report = json.loads((ROOT / "scripts/c5_sharur/garbage_collection_sitrep.json").read_text())
    details = report["agent_details"]
    total = sum(x["bytes_found"] for x in details)
    assert total == report["total_anergy_bytes"]
    left, right = details[0], details[6]
    duplicate = all(left[k] == right[k] for k in ("target", "pattern", "samples", "bytes_found"))
    assert duplicate
    results["SW100-C0309"] = {"total_equals_sum_of_repeated_scans": total, "duplicate_agents": [left["agent_id"], right["agent_id"]], "equal_target_pattern_samples_bytes": duplicate, "operator_files_accessed": False}

    bad_render_dir = (ROOT / "scripts/c5_demos/c5_transduction_engine.py").resolve().parent.parent / "01_KISH_ENGINE/transducers/video_remotion"
    results["SW100-C0041"] = {"configured_path_exists": bad_render_dir.exists(), "actual_entry_exists": (ROOT / "01_KISH_ENGINE/cortex/transducers/video_remotion/src/index.ts").is_file()}
    assert not bad_render_dir.exists()
    print(json.dumps({"scope": "Pure Python in-memory fixtures and repository metadata only; no native, protected, network, or operator-data execution.", "results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
