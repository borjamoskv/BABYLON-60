import os
import random

PASS_DIR = "tests/pass_generated"
FAIL_DIR = "tests/fail_generated"

os.makedirs(PASS_DIR, exist_ok=True)
os.makedirs(FAIL_DIR, exist_ok=True)

# Generate 50 passing tests (Valid 1-out DAGs: linear chains and fan-ins)
for i in range(50):
    nodes = [f"N{j}" for j in range(random.randint(5, 20))]
    edges = []
    # To ensure 1-out DAG, each node can point to at most ONE node that is temporally "older" (index strictly less)
    for j in range(1, len(nodes)):
        target = random.choice(nodes[:j])
        edges.append(f"{nodes[j]} -> {target};")
    
    code = f"""use epistemic_engine::epistemic;

epistemic! {{
    graph pass_fuzz_{i} {{
        {chr(10).join(edges)}
    }}
}}

fn main() {{}}
"""
    with open(f"{PASS_DIR}/fuzz_{i:02d}.rs", "w") as f:
        f.write(code)

# Generate 50 failing tests (Cycles and Multi-out)
for i in range(50):
    nodes = [f"N{j}" for j in range(random.randint(5, 20))]
    edges = []
    fail_type = random.choice(["cycle", "multi_out"])
    
    if fail_type == "cycle":
        # Create a linear chain
        for j in range(len(nodes) - 1):
            edges.append(f"{nodes[j]} -> {nodes[j+1]};")
        # Add a back-edge to create a cycle
        edges.append(f"{nodes[-1]} -> {nodes[0]};")
    else: # multi_out
        # One node points to two different targets
        source = nodes[0]
        edges.append(f"{source} -> {nodes[1]};")
        edges.append(f"{source} -> {nodes[2]};")
        
    code = f"""use epistemic_engine::epistemic;

epistemic! {{
    graph fail_fuzz_{i} {{
        {chr(10).join(edges)}
    }}
}}

fn main() {{}}
"""
    with open(f"{FAIL_DIR}/fuzz_{i:02d}.rs", "w") as f:
        f.write(code)

# ----------------- MASSIVE STRESS TESTS ----------------- #

# Massive Linear (1000 nodes)
nodes_lin = [f"M{j}" for j in range(1000)]
edges_lin = [f"{nodes_lin[j]} -> {nodes_lin[j+1]};" for j in range(999)]
code_lin = f"""use epistemic_engine::epistemic;

epistemic! {{
    graph massive_linear {{
        {chr(10).join(edges_lin)}
    }}
}}

fn main() {{}}
"""
with open(f"{PASS_DIR}/massive_linear.rs", "w") as f:
    f.write(code_lin)

# Massive Fan-In (1000 nodes -> 1 target)
nodes_fanin = [f"F{j}" for j in range(1000)]
edges_fanin = [f"{n} -> TargetNode;" for n in nodes_fanin]
code_fanin = f"""use epistemic_engine::epistemic;

epistemic! {{
    graph massive_fan_in {{
        {chr(10).join(edges_fanin)}
    }}
}}

fn main() {{}}
"""
with open(f"{PASS_DIR}/massive_fan_in.rs", "w") as f:
    f.write(code_fanin)

print("100 pruebas + Massive Stress Tests generadas correctamente.")
