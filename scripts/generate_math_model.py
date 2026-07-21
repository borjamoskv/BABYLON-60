import os
import json
from collections import defaultdict


def summarize_graphs() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.join(project_root, "cortex", "artifacts", "reports")

    # 1. Load Call Graph (Dependency DAG)
    try:
        with open(f"{base_dir}/BABYLON_60_CALL_GRAPH.json", "r") as f:
            call_graph = json.load(f)
    except FileNotFoundError:
        call_graph = {}

    # 2. Load IPC Graph (State/Execution DAG hints)
    try:
        with open(f"{base_dir}/BABYLON_60_RUNTIME_IPC.json", "r") as f:
            ipc_graph = json.load(f)
    except FileNotFoundError:
        ipc_graph = {}

    modules = set(call_graph.keys())
    for cat in ipc_graph.values():
        for item in cat:
            modules.add(item["file"])

    fan_out: dict[str, int] = defaultdict(int)
    fan_in: dict[str, int] = defaultdict(int)

    # Build a simple dependency edge list (module -> called functions)
    edges = []
    for mod, data in call_graph.items():
        calls = set()
        for funcs in data.get("functions", {}).values():
            calls.update(funcs)
        calls.update(data.get("module_level_calls", []))
        fan_out[mod] = len(calls)
        for c in calls:
            fan_in[c] += 1
            edges.append((mod, c))

    # Kernel calculation: Highest fan-in, part of IPC / Core
    kernel_candidates = sorted(fan_in.items(), key=lambda x: x[1], reverse=True)[:20]

    summary = {
        "V": len(modules),
        "E": len(edges),
        "top_fan_in": kernel_candidates,
        "top_fan_out": sorted(fan_out.items(), key=lambda x: x[1], reverse=True)[:10],
        "ffi_nodes": len(ipc_graph.get("ffi_bindings", [])),
        "wal_nodes": len(ipc_graph.get("database_locks", [])),
        "network_nodes": len(ipc_graph.get("network_endpoints", [])),
    }

    with open(f"{base_dir}/BABYLON_60_MATH_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary written to {base_dir}/BABYLON_60_MATH_SUMMARY.json")


if __name__ == "__main__":
    summarize_graphs()
