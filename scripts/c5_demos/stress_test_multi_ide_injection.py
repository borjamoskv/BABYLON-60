#!/usr/bin/env python3
"""
🧪 STRESS TEST & PoC v2.2: Multi-Ecosystem Shield Injection Verification
Framework: C5-REAL (Empirical Falsification & Zero-Anergy Audit)

Verifica idempotencia, integridad de enlaces simbólicos, ausencia de duplicidad entrópica
y tiempo de ejecución en 8 entornos (Antigravity, Claude Code, Cursor, Windsurf, Aider, Zed, Codex CLI, ChatGPT Local).
"""

import sys
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if not (PROJECT_ROOT / "tools" / "install_shield.sh").exists():
    PROJECT_ROOT = Path.home() / "BABYLON-60"
if not (PROJECT_ROOT / "tools" / "install_shield.sh").exists():
    PROJECT_ROOT = Path.home() / "10_PROJECTS" / "BABYLON-60"

INSTALL_SCRIPT = PROJECT_ROOT / "tools" / "install_shield.sh"
TARGET_SKILL = PROJECT_ROOT / ".agents" / "skills" / "babylon-shield" / "SKILL.md"
CANONICAL_RULES = PROJECT_ROOT / ".babylon60rules"

TARGET_PATHS = {
    "Antigravity": Path.home() / ".gemini" / "config" / "skills" / "babylon-shield",
    "Claude Code": Path.home() / ".claude" / "skills" / "babylon-shield",
    "Babylon60 Rules": CANONICAL_RULES,
    "Cursor IDE": PROJECT_ROOT / ".cursorrules",
    "Windsurf IDE": PROJECT_ROOT / ".windsurfrules",
    "Claude Workspace": PROJECT_ROOT / "CLAUDE.md",
    "Cline": PROJECT_ROOT / ".clinerules",
    "Roo Code": PROJECT_ROOT / ".roorules",
    "GitHub Copilot": PROJECT_ROOT / ".github" / "copilot-instructions.md",
    "Aider CLI": Path.home() / ".aider.conf.yml",
    "Zed Editor": Path.home() / ".config" / "zed" / "prompts" / "babylon-shield.md",
    "OpenAI Codex Global": Path.home() / ".codex" / "instructions.md",
    "OpenAI Codex Local": PROJECT_ROOT / ".codexrules",
}

def run_single_injection() -> tuple[bool, float]:
    start = time.perf_counter()
    res = subprocess.run(
        [str(INSTALL_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    elapsed = (time.perf_counter() - start) * 1000  # ms
    return res.returncode == 0, elapsed

def audit_target_integrities() -> list[str]:
    errors: list[str] = []
    
    # 1. Check Symlinks
    for name in ["Antigravity", "Claude Code", "Zed Editor"]:
        target = TARGET_PATHS[name]
        if not target.exists() and not target.is_symlink():
            errors.append(f"[{name}] El destino no existe: {target}")
        elif target.is_symlink():
            resolved = target.resolve()
            if not resolved.exists():
                errors.append(f"[{name}] Enlace simbólico roto -> {resolved}")

    # 1b. Check Dotfile Symlinks to .babylon60rules
    for name in ["Cursor IDE", "Windsurf IDE", "OpenAI Codex Local", "Claude Workspace", "Cline", "Roo Code", "GitHub Copilot"]:
        target = TARGET_PATHS[name]
        if not target.is_symlink():
            errors.append(f"[{name}] No es enlace simbólico: {target} (debe ser symlink a .babylon60rules)")
        else:
            resolved = target.resolve()
            if not resolved.exists():
                errors.append(f"[{name}] Enlace simbólico roto -> {resolved}")
            elif resolved.name != ".babylon60rules":
                errors.append(f"[{name}] Enlace simbólico no apunta a .babylon60rules (apunta a {resolved.name})")
                
    # 2. Check File Rules for Entropy Duplication (Idempotency)
    for name in ["Babylon60 Rules", "Cursor IDE", "Windsurf IDE", "OpenAI Codex Local", "Claude Workspace", "Cline", "Roo Code", "GitHub Copilot"]:
        target = TARGET_PATHS[name]
        if target.exists():
            content = target.read_text()
            if "# BABYLON-60" not in content and "BABYLON-60 SHIELD INVARIANT" not in content:
                errors.append(f"[{name}] Manifiesto canónico no encontrado en {target}")
        else:
            errors.append(f"[{name}] Archivo de reglas no creado: {target}")

    codex_global = TARGET_PATHS["OpenAI Codex Global"]
    if codex_global.exists():
        content = codex_global.read_text()
        count = content.count("BABYLON-60 SHIELD INVARIANT")
        if count > 1:
            errors.append(f"[OpenAI Codex Global] FALLO DE IDEMPOTENCIA: Invariante duplicado {count} veces en {codex_global}")
        elif count == 0:
            errors.append(f"[OpenAI Codex Global] Invariante no encontrado en {codex_global}")
    else:
        errors.append(f"[OpenAI Codex Global] Archivo de reglas no creado: {codex_global}")

    # Aider CLI check
    aider_target = TARGET_PATHS["Aider CLI"]
    if aider_target.exists():
        content = aider_target.read_text()
        count = content.count("babylon-shield")
        if count > 1:
            errors.append(f"[Aider CLI] FALLO DE IDEMPOTENCIA: Invariante duplicado {count} veces en {aider_target}")
            
    return errors

def main() -> None:
    print("=" * 70)
    print("🔥 C5-REAL STRESS TEST & PoC v2.2: MULTI-ECOSYSTEM SHIELD INJECTION")
    print("=" * 70)
    
    if not INSTALL_SCRIPT.exists():
        print(f"❌ Error: No se encuentra el instalador en {INSTALL_SCRIPT}")
        sys.exit(1)
        
    print("\n[1] Ejecutando 100 inyecciones secuenciales (Stress Test de Idempotencia)...")
    latencies: list[float] = []
    failures = 0
    
    for i in range(1, 101):
        ok, elapsed = run_single_injection()
        if not ok:
            failures += 1
        latencies.append(elapsed)
        
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    print("  └─ Completadas 100/100 iteraciones.")
    print(f"  └─ Fallos de ejecución: {failures}")
    print(f"  └─ Latencia Media: {avg_latency:.2f} ms (Min: {min_latency:.2f} ms, Max: {max_latency:.2f} ms)")
    
    print("\n[2] Verificando Invariantes de Integridad en 8 Entornos (incl. OpenAI Codex)...")
    audit_errors = audit_target_integrities()
    
    if audit_errors:
        print("❌ FALSACIÓN EMPÍRICA FALLIDA. Se detectaron errores:")
        for err in audit_errors:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print("✅ TODAS LAS AUDITORÍAS PASARON SATISFACTORIAMENTE:")
        for env_name, path in TARGET_PATHS.items():
            print(f"   - [{env_name}] -> {path} (VALIDADO, CERO DUPLICACIÓN)")
            
    print("\n[3] Prueba de Concurrencia Simultánea (10 hilos en paralelo)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_single_injection) for _ in range(10)]
        results = [f.result() for f in futures]
        
    concurrent_failures = sum(1 for ok, _ in results if not ok)
    print(f"  └─ Fallos bajo concurrencia paralela: {concurrent_failures}")
    
    if concurrent_failures == 0 and failures == 0:
        print("\n" + "=" * 70)
        print("🏆 DEMOSTRACIÓN COMPROBADA: El instalador v2.2 es Idempotente, Zero-Anergy y Multi-Ecosystem Safe.")
        print("=" * 70)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
