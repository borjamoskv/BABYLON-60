import sys
import re
import json
import z3
import subprocess
from pathlib import Path

def parse_dot(dot_file: str) -> dict:
    edges = {}
    with open(dot_file, 'r') as f:
        for line in f:
            # Match: Hypothesis_Hypothesis -> Intervention_SandboxDeployment [label="0.95"];
            match = re.search(r'(\w+)\s*->\s*(\w+)\s*\[label="([\d\.]+)"\]', line)
            if match:
                src, dst, weight = match.groups()
                # Store edge without prefixes for generic mapping if needed, or exact
                # But notice the source code has "Hypothesis Hypothesis -> Intervention SandboxDeployment [0.95]"
                # The dot node names are joined by underscore
                edges[(src, dst)] = float(weight)
    return edges

def solve_invariants(edges: dict, telemetry: dict):
    print("\n[SANEDRIN SMT] Bootstrapping Z3 Bayesian Topological Solver...")
    solver = z3.Solver()
    
    # We create real variables for each node's confidence
    nodes = set()
    for (src, dst) in edges.keys():
        nodes.add(src)
        nodes.add(dst)
        
    conf = {n: z3.Real(n) for n in nodes}
    
    # 0 <= conf <= 1
    for n in nodes:
        solver.add(conf[n] >= 0.0, conf[n] <= 1.0)
        
    # Root nodes have confidence 1.0
    destinations = {dst for (_, dst) in edges.keys()}
    roots = nodes - destinations
    for r in roots:
        solver.add(conf[r] == 1.0)
        
    # Edges define propagation
    # C(dst) = C(src) * W
    for (src, dst), weight in edges.items():
        solver.add(conf[dst] == conf[src] * weight)
        
    # Check empirical telemetries
    falsifications = []
    
    for (src, dst), original_weight in edges.items():
        # Check if telemetry has a different empirical weight
        # Format: "Type_Name -> Type_Name" or just by generic match
        # To match source code for cortex_mutate.py, we need the exact names used in Rust macro.
        # "Intervention_SandboxDeployment" -> kind="Intervention", name="SandboxDeployment"
        src_kind, src_name = src.split('_', 1)
        dst_kind, dst_name = dst.split('_', 1)
        
        telemetry_key = f"{src_kind} {src_name} -> {dst_kind} {dst_name}"
        
        if telemetry_key in telemetry:
            empirical_weight = telemetry[telemetry_key]
            
            # SMT Check: Does the original graph deviate?
            # E.g. we add constraint that weight must equal empirical
            solver.push()
            solver.add(z3.RealVal(original_weight) == z3.RealVal(empirical_weight))
            result = solver.check()
            if result == z3.unsat:
                print(f"[SANEDRIN VERDICT] Falsification detected on edge: {telemetry_key}")
                print(f"  - Theoretical DAG: {original_weight}")
                print(f"  - Empirical Telemetry: {empirical_weight}")
                print(f"  - Delta: {empirical_weight - original_weight:.3f}")
                falsifications.append({
                    "src_name": src_name,
                    "dst_name": dst_name,
                    "old_weight": original_weight,
                    "new_weight": empirical_weight
                })
            solver.pop()
            
    return falsifications

def mutate_and_push(falsifications):
    if not falsifications:
        print("[SANEDRIN] Topology is thermodynamically stable. Zero falsifications.")
        return
        
    print(f"\n[OUROBOROS] Initializing physical mutation of {len(falsifications)} edges...")
    
    cortex_mutate = Path(__file__).parent / "cortex_mutate.py"
    
    for falsi in falsifications:
        cmd = [
            "python3", str(cortex_mutate),
            "--file", "examples/poc_science.rs",
            "--edge", f"{falsi['src_name']} -> {falsi['dst_name']}",
            "--weight", str(falsi["new_weight"])
        ]
        print(f"  -> Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    print("\n[OUROBOROS] Mutation complete. Git Sentinel triggered via cortex_mutate.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sanedrin_solver.py <path_to.dot> <path_to_telemetry.json>")
        sys.exit(1)
        
    dot_path = sys.argv[1]
    telemetry_path = sys.argv[2]
    
    with open(telemetry_path, 'r') as f:
        telemetry = json.load(f)
        
    edges = parse_dot(dot_path)
    falsifications = solve_invariants(edges, telemetry)
    mutate_and_push(falsifications)
