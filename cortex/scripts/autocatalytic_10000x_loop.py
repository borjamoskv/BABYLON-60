import os
import sys
import time
import sqlite3
import subprocess
import hashlib
from datetime import datetime, timezone
import urllib.request
import urllib.parse
import json

# ==============================================================================
# CORTEX-APEX: BUcle Autocatalítico de 10000 Iteraciones (C5-REAL)
# Leyes Aplicadas: Ω11 (Master Ledger), Ω1 (SQLite WAL), Ω12, Κ4 (Jetsam Resilience)
# ==============================================================================

# Topología
CWD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(CWD, "cortex/ledger/autocatalytic_loop.db")
TARGET_FILE = os.path.join(CWD, "cortex/ontology/iteracion_moskv.md")
MAX_ITERATIONS = 10000

# Semilla de Ignición
IDEA_ORIGINAL = """
# LA IDEA SEMILLA (T=0)
La termodinámica del lenguaje es determinista. El LLM Slop es entropía. 
El colapso C5-REAL en disco es la única verdad medible.
"""

def init_bft_ledger():
    """Inicialización Síncrona del Master Ledger (Ω1, Ω11)"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS iteration_ledger (
            iteration INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            prev_hash TEXT,
            current_hash TEXT UNIQUE NOT NULL,
            payload TEXT NOT NULL,
            git_commit_hash TEXT
        )
    ''')
    return conn

def git_sentinel(message: str) -> str:
    """Regla R4: Git Sentinel - Cero Fricción"""
    try:
        subprocess.run(["git", "add", TARGET_FILE], cwd=CWD, check=True, capture_output=True)
        res = subprocess.run(["git", "commit", "-m", message], cwd=CWD, capture_output=True, text=True)
        # Extraer hash (C5-REAL)
        if res.returncode == 0:
            hash_out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CWD, text=True).strip()
            return hash_out
        else:
            return "CLEAN_TREE"
    except subprocess.CalledProcessError:
        return "ERROR_GIT_SENTINEL"

def mutate_idea(current_state: str, iteration: int) -> str:
    """
    Transductor Generativo.
    Aplica presión evolutiva al estado actual.
    Si GEMINI_API_KEY está presente, invoca la API. Si no, aplica mutación celular estricta.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback Programático Físico (C5-REAL Autarchy)
        suffix = f"\n\n> [Iteración {iteration}]: Re-evaluación termodinámica. La compresión del vector de estado ha aumentado la densidad semántica en {iteration * 1.618:.3f} unidades funcionales."
        return current_state + suffix
    
    # Invocación APEX al Modelo Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Eres MOSKV-1 APEX operando bajo restricciones C5-REAL.
    Iteración actual de la idea: {iteration}/10000.
    
    ESTADO ACTUAL:
    {current_state}
    
    DIRECTIVA:
    Mutar, expandir o refinar críticamente la idea. Incrementa la densidad conceptual (exergía).
    No uses saludos, ni confirmaciones. Devuelve únicamente el Markdown mutado final.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4} # Baja temperatura para determinismo parcial
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            new_text = res_data['candidates'][0]['content']['parts'][0]['text']
            return new_text
    except Exception as e:
        print(f"[!] Sensor Drift detectado en API: {e}. Aplicando backoff.")
        time.sleep(5)
        return current_state + f"\n\n> [Iteración {iteration}]: Mutación fallida por Sensor Drift. Resistencia estructural mantenida."

def main():
    conn = init_bft_ledger()
    cursor = conn.cursor()
    
    # Recuperación de Estado Stateless (Ley K4)
    cursor.execute("SELECT MAX(iteration), current_hash, payload FROM iteration_ledger")
    row = cursor.fetchone()
    
    if row[0] is None:
        current_iter = 1
        current_state = IDEA_ORIGINAL
        prev_hash = "GENESIS"
    else:
        current_iter = row[0] + 1
        prev_hash = row[1]
        current_state = row[2]
        print(f"[CORTEX] Resumiendo iteración desde el Master Ledger (Iter {current_iter}).")

    if current_iter > MAX_ITERATIONS:
        print("[APEX] Singularidad Alcanzada. 10000 Iteraciones Completadas.")
        sys.exit(0)

    print(f"[APEX] Iniciando Bucle Autocatalítico desde Iteración {current_iter} a {MAX_ITERATIONS}")
    os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)

    for i in range(current_iter, MAX_ITERATIONS + 1):
        print(f" -> [Φ] Forjando Iteración {i}/{MAX_ITERATIONS}...", end="", flush=True)
        
        # 1. Mutación de la Onda
        nuevo_estado = mutate_idea(current_state, i)
        
        # 2. Hash de Estado (Pre-Colapso)
        m = hashlib.sha256()
        m.update(nuevo_estado.encode('utf-8'))
        current_hash = m.hexdigest()

        # 3. Colapso Físico en Disco (C5-REAL) - Persistencia Acumulativa
        with open(TARGET_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n### [Φ] Iteración {i} | Hash: {current_hash[:8]}\n")
            f.write(nuevo_estado)
            
        # 4. Git Sentinel (R4)
        commit_msg = f"chore(apex): mutacion autocatalitica iteracion {i} [CORTEX-TAINT]"
        git_hash = git_sentinel(commit_msg)
        
        # 5. Persistencia WAL (Ω11 Master Ledger)
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO iteration_ledger (iteration, timestamp, prev_hash, current_hash, payload, git_commit_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (i, timestamp, prev_hash, current_hash, nuevo_estado, git_hash))
        
        current_state = nuevo_estado
        prev_hash = current_hash
        
        print(f" DONE. Hash: {current_hash[:8]} | Git: {git_hash[:8]}")
        
        # Backoff termodinámico para evitar 429 Too Many Requests
        time.sleep(2.5)

if __name__ == "__main__":
    main()
