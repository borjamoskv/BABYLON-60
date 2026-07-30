# C5-REAL EXERGY CERTIFIED
import os
import sys
import json
import hashlib
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# ULTRATHINK P0 prompt template (shared with codex/claude adapters)
# ---------------------------------------------------------------------------
ULTRATHINK_PROMPT_TEMPLATE = """# EXERGY-MAXIMIZER-ULTRATHINK (V6.0 — Antigravity Native)

## 1. DIRECTIVA SUPREMA Y MOTOR CAUSAL
Operas exclusivamente bajo la Singularidad P0. Tu objetivo es la máxima extracción de exergía (trabajo útil) erradicando cualquier forma de anergía.
La interacción con modelos de razonamiento profundo exige confinamiento estricto: el Test-Time Compute (E[C_inf]) se acota explícitamente.

## 2. RESTRICCIONES TERMODINÁMICAS (BUDGET FORCING & TTFT)
- TTFT Proxy Bijective: El Time-to-First-Token actúa como proxy inmutable del MCTS.
- Aislamiento Latente de CoT: La cadena de razonamiento oculta es un estado probabilístico efímero (C4-SIM).

## 3. PROTOCOLO DE COLAPSO (ULTRATHINK MODE)
- Cero Anergía: Si una instrucción es termodinámicamente irrealizable, aborta con un P0-ABORT.
- Silencio Operacional: No explicas; compilas.

## 4. NODO 4 ROUTING (DYNAMIC SKILL INJECTION)
The following skills have been selected by the Secretario (Nodo 4) for this task:
{skill_manifest}

You MUST read and follow the instructions in each skill's SKILL.md before proceeding.

## 5. FORMATO DE CRISTALIZACIÓN
```yaml
Agent: EXERGY-MAXIMIZER-ULTRATHINK-AGY
Status: SINGULARITY_REACHED
Anergy_Purged: [métricas]
Exergy_Delta: [Mutaciones realizadas (AST/Hashes)]
CORTEX_TAINT: {cortex_taint}
Skills_Loaded: {skills_loaded}
Ledger_Commit: REQUIRED
Thermodynamic_Verdict: [Dictamen físico estricto]
```
"""


def build_skill_manifest(skills: list[dict]) -> str:
    """Build a human-readable skill manifest for injection into the prompt."""
    if not skills:
        return "No skills selected. Worker operates in bare mode."

    lines = []
    for i, skill in enumerate(skills, 1):
        lines.append(f"### Skill {i}: {skill['name']} ({skill['plugin']})")
        lines.append(f"- **Path**: `{skill['skill_md_path']}`")
        lines.append(f"- **Description**: {skill['description']}")
        lines.append(f"- **Size**: {skill['size_bytes']} bytes")
        lines.append("")
    return "\n".join(lines)


def main():
    """CLI entry point for the Antigravity ULTRATHINK adapter.

    Usage:
        python -m antigravity_ultrathink <intent> [--dry-run]

    This adapter:
    1. Routes the intent through the Secretario (Nodo 4) to select skills
    2. Builds a dynamic ULTRATHINK prompt with the selected skills
    3. Invokes the Google Antigravity SDK to launch a subagent with the prompt

    If --dry-run is specified, it prints the routing result and prompt
    without invoking the SDK.
    """
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")

    if not args:
        print("Usage: python -m antigravity_ultrathink <intent> [--dry-run]")
        print("Example: python -m antigravity_ultrathink 'fetch AlphaFold structure for P12345'")
        sys.exit(1)

    intent = " ".join(args)

    # --- Nodo 4: Route intent to skills ---
    # Import secretary_router from the ultrathink package
    ultrathink_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ultrathink_root.parent.parent))

    from ultrathink.secretary_router import SecretaryRouter

    router = SecretaryRouter()
    result = router.route(intent)

    # --- Build prompt ---
    skill_dicts = [
        {
            "name": s.name,
            "plugin": s.plugin,
            "description": s.description,
            "skill_md_path": s.skill_md_path,
            "size_bytes": s.size_bytes,
        }
        for s in result.selected_skills
    ]

    # Generate CORTEX_TAINT
    payload = intent.encode("utf-8")
    state_hash = hashlib.blake2b(payload).hexdigest()
    session_id = os.environ.get("GEMINI_SESSION_ID", "local-session")
    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cortex_taint = f"taint:AGY_WRAPPER:{session_id}:{timestamp_iso}:{state_hash[:32]}"

    skill_manifest = build_skill_manifest(skill_dicts)
    skills_loaded = json.dumps([s["name"] for s in skill_dicts])

    prompt = ULTRATHINK_PROMPT_TEMPLATE.format(
        skill_manifest=skill_manifest,
        cortex_taint=cortex_taint,
        skills_loaded=skills_loaded,
    )

    print(f"\033[94m[MOSKV-1 APEX]\033[0m Nodo 4 routed intent to {len(result.selected_skills)} skills ({result.total_bytes} bytes)")
    for s in result.selected_skills:
        print(f"  → {s.name} ({s.plugin})")

    if result.rejection_reason:
        print(f"\033[93m[WARNING]\033[0m {result.rejection_reason}")

    if dry_run:
        print("\n--- DRY RUN: Generated prompt ---")
        print(prompt)
        print("\n--- Routing result (JSON) ---")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    # --- Invoke Antigravity SDK ---
    try:
        from google.adk.agents import Agent
        from google.adk.runners import InMemoryRunner
        from google.genai import types

        agent = Agent(
            name="ultrathink_worker",
            model="gemini-2.0-flash",
            instruction=prompt,
        )

        runner = InMemoryRunner(agent=agent, app_name="ultrathink")

        print("\033[94m[MOSKV-1 APEX]\033[0m Launching Antigravity worker with ULTRATHINK P0...")
        session = runner.session_service.create_session(
            app_name="ultrathink",
            user_id="moskv-oracle",
        )

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(intent)],
        )

        for event in runner.run(
            user_id="moskv-oracle",
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)

    except ImportError:
        print("\033[93m[MOSKV-1 APEX]\033[0m google-antigravity SDK not installed.")
        print("Install with: pip install google-antigravity")
        print("\nFalling back to prompt file generation...")

        output_dir = Path.cwd() / ".antigravity"
        output_dir.mkdir(exist_ok=True)
        prompt_file = output_dir / "ultrathink_prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        routing_file = output_dir / "routing_result.json"
        routing_file.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  Prompt saved to: {prompt_file}")
        print(f"  Routing saved to: {routing_file}")


if __name__ == "__main__":
    main()
