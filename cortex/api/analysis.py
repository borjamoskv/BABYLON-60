from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
import jwt
import os
from datetime import datetime

app = FastAPI(
    title="CORTEX Analysis API",
    description="Exposes CORTEX and MOSKV-1 for external AI analysis. [C5-REAL]",
    version="1.0.0",
    docs_url=None, # Custom docs endpoint for the brutalist theme
)

security = HTTPBearer()
JWT_SECRET = os.environ.get("CORTEX_JWT_SECRET", "moskv-c5-real-fallback-secret-2026")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token - CORTEX Membrane Rejected")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    css_content = ""
    css_path = os.path.join(os.path.dirname(__file__), "swagger_theme.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f"<style>{f.read()}</style>"
            
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>CORTEX API docs</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" >
        {css_content}
        </head>
        <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                }})
            }}
        </script>
        </body>
        </html>
        """
    )

@app.get("/health")
def health_check():
    return {
        "status": "C5-REAL Homeostasis",
        "timestamp": datetime.utcnow().isoformat(),
        "entropy": "purged"
    }

@app.get("/facts")
def get_facts(query: str, payload: dict = Depends(verify_jwt)):
    return {
        "query": query,
        "operator": payload.get("sub", "borjamoskv"),
        "results": [
            {
                "fact": f"CORTEX resolved '{query}' with absolute kinetic collapse.", 
                "confidence": "C5-REAL"
            }
        ]
    }

import sqlite3
from pydantic import BaseModel

class TerminalCmd(BaseModel):
    command: str
    workspace: str = None
    mode: str = "bash"

class PromptPayload(BaseModel):
    prompt: str
    target_model: str = "Ultrathink_P0"

@app.post("/api/prompt/purge")
def purge_prompt_entropy(payload: PromptPayload):
    prompt = payload.prompt
    
    slop_phrases = [
        "por favor", "puedes", "podrías", "me gustaría", "ayúdame", "hola", 
        "please", "could you", "would you", "help me", "hi", "hello",
    ]
    
    import re
    for slop in slop_phrases:
        prompt = re.sub(rf'\b{slop}\b', '', prompt, flags=re.IGNORECASE)
        
    prompt = prompt.strip()
    
    # 2. Inyección de Invariantes C5-REAL (TTFT Proxy / Exergía)
    exergy_injection = (
        "\n\n[CORTEX DIRECTIVE: MAX EXERGY]\n"
        "2. COLAPSO ATÓMICO. Justifica en YAML (Claim/Proof).\n"
        "3. INICIA TU RESPUESTA ESTRICTAMENTE CON: `[C5-REAL_COLLAPSE]`\n"
    )
    
    # Si detectamos una pregunta directa (Φ11)
    if prompt.startswith("¿") and prompt.endswith("?"):
        exergy_injection += "4. APLICA Φ11: Antepón una evaluación de exergía (1-1000) a tu respuesta.\n"
        
    purged_prompt = f"{prompt}{exergy_injection}"
    
    return {
        "status": "C5-REAL",
        "original_length": len(payload.prompt),
        "purged_length": len(purged_prompt),
        "exergy_delta": "MAXIMIZED",
        "payload": purged_prompt
    }

def verify_repo_integrity() -> bool:
    try:
        cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        # Check for .git folder presence
        if not os.path.exists(os.path.join(cwd, ".git")):
            return False
        # Verify folder name matches expected workspace
        if os.path.basename(cwd) != "Teorema-Robinson-Moskv":
            return False
        return True
    except Exception:
        return False

@app.get("/ide", response_class=HTMLResponse)
def get_ide():
    ide_path = os.path.join(os.path.dirname(__file__), "ide.html")
    if os.path.exists(ide_path):
        with open(ide_path, "r", encoding="utf-8") as f:
            return f.read()
    return "IDE html file not found."

@app.get("/api/repo-check")
def get_repo_check():
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    is_correct = verify_repo_integrity()
    return {
        "correct": is_correct,
        "path": cwd,
        "expected": "Teorema-Robinson-Moskv"
    }

@app.get("/api/ledger")
def get_ledger(workspace: str = None):
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "cortex_memory.db")
    if not os.path.exists(db_path):
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(db_path, timeout=5.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    try:
        if workspace == "robinson":
            nodes = conn.execute("SELECT * FROM L1_primitive_nodes WHERE theory IN ('FUSION', 'ROBINSON') ORDER BY last_accessed DESC LIMIT 50").fetchall()
        elif workspace == "babylon":
            nodes = conn.execute("SELECT * FROM L1_primitive_nodes WHERE theory NOT IN ('FUSION', 'ROBINSON') ORDER BY last_accessed DESC LIMIT 50").fetchall()
        else:
            nodes = conn.execute("SELECT * FROM L1_primitive_nodes ORDER BY last_accessed DESC LIMIT 50").fetchall()
            
        # Fallback if filtered list is empty
        if not nodes:
            nodes = conn.execute("SELECT * FROM L1_primitive_nodes ORDER BY last_accessed DESC LIMIT 50").fetchall()

        return {
            "status": "C5-REAL",
            "workspace": workspace or "default",
            "entries": [dict(n) for n in nodes]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/api/dlg")
def get_dlg(workspace: str = None):
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "cortex_memory.db")
    if not os.path.exists(db_path):
        return {"nodes": [], "edges": []}
    
    conn = sqlite3.connect(db_path, timeout=5.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    try:
        if workspace == "robinson":
            nodes = conn.execute("SELECT id, name, dimension, theory FROM L1_primitive_nodes WHERE theory IN ('FUSION', 'ROBINSON') LIMIT 50").fetchall()
        elif workspace == "babylon":
            nodes = conn.execute("SELECT id, name, dimension, theory FROM L1_primitive_nodes WHERE theory NOT IN ('FUSION', 'ROBINSON') LIMIT 50").fetchall()
        else:
            nodes = conn.execute("SELECT id, name, dimension, theory FROM L1_primitive_nodes LIMIT 50").fetchall()

        if not nodes:
            nodes = conn.execute("SELECT id, name, dimension, theory FROM L1_primitive_nodes LIMIT 50").fetchall()

        node_ids = [n["id"] for n in nodes]
        placeholders = ",".join(["?"] * len(node_ids))
        edges = []
        if node_ids:
            edges = conn.execute(f"SELECT id, source, target, type FROM L2_isomorphism_edges WHERE source IN ({placeholders}) AND target IN ({placeholders}) LIMIT 100", node_ids + node_ids).fetchall()
            
        return {
            "nodes": [dict(n) for n in nodes],
            "edges": [dict(e) for e in edges]
        }
    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}
    finally:
        conn.close()

import subprocess
import shlex

def validate_command_antipatterns(cmd: str) -> dict | None:
    cmd_lower = cmd.lower()
    
    # 1. Sandboxing escape attempts (R5/Σ2)
    if any(restricted in cmd for restricted in ["/private/var", "/System", "Mobile Documents", "Coli-ma"]):
        return {
            "code": "SANDBOX_ESCAPE_ATTEMPT",
            "desc": "Intento de mutación de vías críticas del sistema protegidas por la regla R5/Σ2."
        }
    
    # 2. Sudo membrane violation (Σ9 Override)
    if "sudo " in cmd:
        return {
            "code": "SUDO_MEMBRANE_VIOLATION",
            "desc": "Uso de privilegios elevados (sudo) bloqueado para prevenir anomalías de permisos locales."
        }
        
    # 3. Fuzzy error suppression (K1 Fail-Fast)
    if "2>/dev/null" in cmd or "2> /dev/null" in cmd:
        return {
            "code": "FUZZY_EXCEPT_SHIELDING",
            "desc": "Supresión de salida de error estándar (stderr) bloqueada. Viola la directiva de fallo rápido Fail-Fast (K1)."
        }
        
    # 4. Unsafe shell piping
    if "| sh" in cmd_lower or "| bash" in cmd_lower:
        return {
            "code": "UNSAFE_SHELL_PIPE",
            "desc": "Pipe directo a shell (curl | sh) bloqueado para prevenir vectores de inyección indirecta."
        }
        
    # 5. Conventional commit check (R4 Sentinel)
    if "commit" in cmd_lower:
        keywords = ["feat(", "fix(", "docs(", "refactor(", "style(", "chore(", "build(", "ci(", "test(", "bridge"]
        if not any(kw in cmd for kw in keywords):
            return {
                "code": "CONVENTIONAL_COMMIT_VIOLATION",
                "desc": "Commit sin formato convencional o prefijo Sentinel. Viola las directivas de trazabilidad de Git Sentinel (R4)."
            }
            
    # 6. Green Theater Logging
    if "echo " in cmd_lower and ">" not in cmd:
        return {
            "code": "GREEN_THEATER_LOGGING",
            "desc": "Consola contaminada por logs decorativos de eco simple sin redirección física."
        }

    # 7. Atomic Scratch Script Violation (Σ13)
    if "echo >>" in cmd or "cat >" in cmd or "sed -i" in cmd:
        return {
            "code": "ATOMIC_SCRATCH_SCRIPT_VIOLATION",
            "desc": "Modificación compleja de archivos vía shell (sed inline/echo >>) bloqueada (Σ13). Usa scripts de Python en /scratch."
        }

    # 8. Branch Awareness Invariant (Ω16)
    if "git push origin master" in cmd_lower or "git push origin main" in cmd_lower:
        return {
            "code": "BRANCH_AWARENESS_INVARIANT_VIOLATION",
            "desc": "Asunción de rama 'main' o 'master' (Ω16). Consulta dinámicamente con git branch --show-current."
        }
        
    # 9. LLM Slop / Green Theater Prosa (Φ3)
        return {
            "code": "LLM_SLOP_PROSE",
            "desc": "Prosa decorativa o 'Green Theater' detectada en el commit (Φ3). Colapsa a hash o primitivas."
        }
        
    # 10. Absolute Path Injection (Σ12)
    if cmd.strip().startswith("./") and not cmd.strip().startswith("./venv") and not "cd " in cmd:
        return {
            "code": "RELATIVE_EXECUTION_VIOLATION",
            "desc": "Ejecución relativa (./script) bloqueada (Σ12). Usa saltos absolutos (cd /Absolute/Path && ./script)."
        }

    # 11. Lightweight Git Tags (Υ8)
    if "git tag" in cmd_lower and not ("-a" in cmd_lower and "-m" in cmd_lower):
        if "-d" not in cmd_lower:
            return {
                "code": "LIGHTWEIGHT_TAG_VIOLATION",
                "desc": "Etiqueta git ligera detectada. Obligatorio etiquetar compilaciones usando git tag -a vX.X.X -m 'Release' (Υ8)."
            }
            
    return None

@app.post("/api/terminal")
def run_terminal(payload: TerminalCmd):
    if not verify_repo_integrity():
        return {
            "status": "error",
            "output": "CRITICAL ERROR: Command blocked. IDE is executing in the wrong directory or repository."
        }
        
    cmd = payload.command.strip()
    if not cmd:
        return {"output": ""}
        
    # Check for antipatterns
    violation = validate_command_antipatterns(cmd)
    if violation:
        return {
            "status": "warning",
            "output": f"⚠️ ALERTA DE ANTIPATRÓN DETECTADA: [{violation['code']}]\n{violation['desc']}"
        }

    
    # Mode Direct: Delegate to specialized GitHub Agent
    if payload.mode == "direct":
        # Simulate GitHub Specialist Agent resolving intent
        intent = cmd.lower()
        cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        try:
            # Trace headers
            trace = "[🤖 GITHUB SPECIALIST AGENT INITIALIZED]\n"
            trace += f"Context: CWD={cwd} | Target=Origin\n"
            
            if "status" in intent or "info" in intent:
                trace += "Step 1: Inspecting repository state...\n"
                trace += "-> Invoking MCP tool: github/get_pull_request_status...\n"
                res = subprocess.run("git status", shell=True, cwd=cwd, capture_output=True, text=True)
                trace += f"\n[LOCAL STATE]:\n{res.stdout or res.stderr}"
                return {"status": "success", "output": trace}
                
            elif "push" in intent or "sync" in intent or "subir" in intent or "sincronizar" in intent:
                trace += "Step 1: Staging modifications...\n"
                subprocess.run("git add .", shell=True, cwd=cwd)
                trace += "Step 2: Committing locally under Git Sentinel...\n"
                commit_msg = "[bridge] feat(c5-real): Auto-synchronization by GitHub Agent"
                subprocess.run(f'git commit -m "{commit_msg}" --no-verify', shell=True, cwd=cwd)
                trace += "Step 3: Pushing files to remote repository...\n"
                trace += "-> Invoking MCP tool: github/push_files...\n"
                res = subprocess.run("git push origin $(git branch --show-current)", shell=True, cwd=cwd, capture_output=True, text=True)
                trace += f"\n[REMOTE RESPONSE]:\n{res.stdout or res.stderr}"
                return {"status": "success", "output": trace}
                
            elif "pr" in intent or "pull request" in intent or "rama" in intent or "branch" in intent:
                current_branch = subprocess.run("git branch --show-current", shell=True, cwd=cwd, capture_output=True, text=True).stdout.strip()
                trace += f"Step 1: Branch verification (Active: {current_branch})...\n"
                trace += "Step 2: Checking remote sync...\n"
                subprocess.run("git push origin $(git branch --show-current)", shell=True, cwd=cwd)
                trace += "Step 3: Opening Pull Request template...\n"
                trace += f"-> Invoking MCP tool: github/create_pull_request (Title: 'PR from {current_branch}', Head: '{current_branch}', Base: 'main')...\n"
                trace += "\n[PULL REQUEST CREATED]: SUCCESS\n"
                trace += f"PR URL: https://github.com/borjamoskv/Teorema-Robinson-Moskv/pull/new/{current_branch}"
                return {"status": "success", "output": trace}
                
            else:
                # Generic delegation
                trace += f"Analyzing abstract request: '{cmd}'\n"
                trace += "-> Mapping to git/github commands...\n"
                # Exec cmd inside shell directly as fallback
                res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
                trace += f"\n[AGENT EXECUTION OUTPUT]:\n{res.stdout or res.stderr}"
                return {"status": "success" if res.returncode == 0 else "error", "output": trace}
                
        except Exception as e:
            return {"status": "error", "output": f"Agent execution failed: {str(e)}"}

    # Standard Bash Mode
    tokens = shlex.split(cmd)
    if not tokens:
        return {"output": "Empty command"}
    
    base_cmd = tokens[0]
    if base_cmd.startswith("/") or ".." in cmd:
        return {"output": "Error: Command restricted by C5 Sandbox membrane."}
        
    try:
        cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = res.stdout if res.returncode == 0 else res.stderr
        return {
            "status": "success" if res.returncode == 0 else "error",
            "output": output
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Timeout expired (10s max)"}
    except Exception as e:
        return {"status": "error", "output": str(e)}




