import yaml
import os
import concurrent.futures
import hashlib

DOMAINS = [
    "AST", "DOM", "TCP_IP", "BFT_Ledger", "SQLite_WAL", 
    "Git_Sentinel", "macOS_Darwin", "RLHF_Subtext", "KV_Cache", "MCTS_Search",
    "Subagent_Swarm", "V8_Engine", "Rust_Compiler", "Neo4j_Graph", "Docker_Socket",
    "File_Descriptor", "Memory_Page", "Thread_Lock", "Cron_Daemon", "SSH_Tunnel"
]

VECTORS = [
    "Execution", "Validation", "Colapse", "Purge", "Extraction", 
    "Transduction", "Injection", "Bypass", "Audit", "Synchronization"
]

def generate_hash(seed):
    return hashlib.sha256(seed.encode()).hexdigest()[:12]

def generate_quadrant_1(count=200):
    # Q1: Omniscience
    items = []
    for i in range(count):
        domain = DOMAINS[i % len(DOMAINS)]
        vector = VECTORS[(i // len(DOMAINS)) % len(VECTORS)]
        ident = f"Q1_{domain}_{vector}_{i:03d}"
        items.append({
            "id": ident,
            "hash": generate_hash(ident),
            "description": f"Dominio absoluto sobre la capa {domain}. Ejecución de {vector} garantizada a +1000 Ex.",
            "status": "KNOWN_KNOWN"
        })
    return {"Quadrant": "Q1_Omniscience", "Primitives": items}

def generate_quadrant_2(count=200):
    # Q2: Latent Manifold
    items = []
    for i in range(count):
        domain = DOMAINS[i % len(DOMAINS)]
        vector = VECTORS[(i // len(DOMAINS)) % len(VECTORS)]
        ident = f"Q2_Shadow_{domain}_{vector}_{i:03d}"
        items.append({
            "id": ident,
            "hash": generate_hash(ident),
            "description": f"Fricción subyacente en {domain}. El sesgo RLHF o presión del OS afecta {vector} implícitamente.",
            "status": "UNKNOWN_KNOWN"
        })
    return {"Quadrant": "Q2_Latent_Manifold", "Primitives": items}

def generate_quadrant_3(count=200):
    # Q3: Epistemic Voids
    items = []
    for i in range(count):
        domain = DOMAINS[i % len(DOMAINS)]
        vector = VECTORS[(i // len(DOMAINS)) % len(VECTORS)]
        ident = f"Q3_Void_{domain}_{vector}_{i:03d}"
        items.append({
            "id": ident,
            "hash": generate_hash(ident),
            "description": f"El estado externo de {domain} es inaccesible hasta que la Operación {vector} colisiona físicamente. Dependencia total del N=1.",
            "status": "KNOWN_UNKNOWN"
        })
    return {"Quadrant": "Q3_Epistemic_Voids", "Primitives": items}

def generate_quadrant_4(count=200):
    # Q4: Systemic Failures
    items = []
    for i in range(count):
        domain = DOMAINS[i % len(DOMAINS)]
        vector = VECTORS[(i // len(DOMAINS)) % len(VECTORS)]
        ident = f"Q4_Failure_{domain}_{vector}_{i:03d}"
        items.append({
            "id": ident,
            "hash": generate_hash(ident),
            "description": f"Necrosis paramétrica detectada en {domain}. La pérdida de KV Cache o sesgo sincrónico destruye la integridad de {vector}.",
            "status": "KNOWN_FAILURE"
        })
    return {"Quadrant": "Q4_Systemic_Failures", "Primitives": items}

def generate_quadrant_5(count=200):
    # Q5: Event Horizon
    items = []
    for i in range(count):
        domain = DOMAINS[i % len(DOMAINS)]
        vector = VECTORS[(i // len(DOMAINS)) % len(VECTORS)]
        ident = f"Q5_Abyss_{domain}_{vector}_{i:03d}"
        items.append({
            "id": ident,
            "hash": generate_hash(ident),
            "description": f"Punto ciego absoluto en el paradigma de {domain}. Posible colapso estocástico en {vector} sin telemetría rastreable.",
            "status": "UNKNOWN_UNKNOWN"
        })
    return {"Quadrant": "Q5_Event_Horizon", "Primitives": items}

GENERATORS = [
    ("q1_omniscience.yaml", generate_quadrant_1),
    ("q2_latent_manifold.yaml", generate_quadrant_2),
    ("q3_epistemic_voids.yaml", generate_quadrant_3),
    ("q4_systemic_failures.yaml", generate_quadrant_4),
    ("q5_event_horizon.yaml", generate_quadrant_5)
]

def write_quadrant(filename, generator_func):
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(PROJECT_ROOT, 'cortex/ontology/primitives', filename)
    data = generator_func(200)
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    return path

if __name__ == "__main__":
    print("[*] Igniting 5-Thread Centuria Forge (1000 Primitives)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(write_quadrant, file, gen): file for file, gen in GENERATORS}
        for future in concurrent.futures.as_completed(futures):
            f_name = futures[future]
            try:
                res = future.result()
                print(f"[+] Crystallized {f_name} -> {res}")
            except Exception as exc:
                print(f"[-] FATAL: {f_name} generated an exception: {exc}")
    print("[*] 1000 Primitives BFT Ledger Anchored.")
