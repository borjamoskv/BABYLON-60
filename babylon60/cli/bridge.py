import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from babylon60.skills.compiler import SkillASTCompiler
from babylon60.skills.recorder import SkillSessionRecorder
from babylon60.skills.replay import SkillReplayEngine
from babylon60.skills.types import InteractionType, SkillDefinition, SkillTelemetrySession


def _find_tauri_root() -> Path | None:
    candidates = (Path.cwd() / "src-tauri", Path(__file__).resolve().parent.parent.parent / "src-tauri")
    for candidate in candidates:
        if (candidate / "Cargo.toml").exists():
            return candidate
    return None


def handle_skill_cli(args: argparse.Namespace) -> None:
    storage_dir = Path.home() / ".gemini" / "config" / ".cortex" / "skills"
    storage_dir.mkdir(parents=True, exist_ok=True)

    if args.skill_action == "record":
        recorder = SkillSessionRecorder(name=args.name)
        recorder.start()
        print(f"🟢 [SKILL-RECORDER] Iniciando grabación de sesión C5-REAL: '{args.name}' (Session ID: {recorder.session_id})")
        recorder.record_event(
            event_type=InteractionType.NAVIGATE,
            selector="window",
            value=args.target_url or "https://babylon60.local",
        )
        recorder.record_event(
            event_type=InteractionType.CLICK,
            selector="#main-action-btn",
            target_text="Ejecutar",
        )
        session = recorder.stop()
        session_file = storage_dir / f"session_{session.session_id}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)
        print(f"💾 [SKILL-RECORDER] Sesión guardada en {session_file}")
        print(f"   Eventos capturados: {len(session.events)} | Hash: {session.compute_hash()[:16]}...")

    elif args.skill_action == "compile":
        session_file = storage_dir / f"session_{args.session_id}.json"
        if not session_file.exists():
            print(f"🔴 [FATAL] Sesión {args.session_id} no encontrada en {storage_dir}", file=sys.stderr)
            sys.exit(1)
        with open(session_file, encoding="utf-8") as f:
            session_data = json.load(f)
        session = SkillTelemetrySession.from_dict(session_data)
        compiler = SkillASTCompiler()
        skill = compiler.compile(session)
        skill_file = storage_dir / f"skill_{skill.metadata.skill_id}.json"
        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump(skill.to_dict(), f, indent=2)
        print(f"🟢 [SKILL-COMPILER] Skill compilada con éxito: '{skill.metadata.name}' (ID: {skill.metadata.skill_id})")
        print(f"   AST Nodes: {len(skill.ast_nodes)} | Digest: {skill.compute_digest()[:16]}...")

    elif args.skill_action == "replay":
        skill_file = storage_dir / f"skill_{args.skill_id}.json"
        if not skill_file.exists():
            print(f"🔴 [FATAL] Skill {args.skill_id} no encontrada en {storage_dir}", file=sys.stderr)
            sys.exit(1)
        with open(skill_file, encoding="utf-8") as f:
            skill_data = json.load(f)
        skill = SkillDefinition.from_dict(skill_data)
        engine = SkillReplayEngine()
        report = engine.execute(skill)
        print(f"🟢 [SKILL-REPLAY] Ejecución finalizada: Passed={report.passed}")
        print(f"   Pasos exitosos: {report.successful_steps}/{report.total_steps} | Duración: {report.total_duration_ms}ms")

    elif args.skill_action == "list":
        session_files = list(storage_dir.glob("session_*.json"))
        skill_files = list(storage_dir.glob("skill_*.json"))
        print(f"🟢 [SKILL-REGISTRY] {len(session_files)} sesiones grabadas | {len(skill_files)} skills compiladas")
        for sf in skill_files:
            print(f"  • {sf.stem}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cortex-bridge",
        description="Ignición del Puente CORTEX y BABYLON-60 Skill Synthesizer Kernel.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    skill_parser = subparsers.add_parser("skill", help="BABYLON-60 Record-a-Skill commands")
    skill_sub = skill_parser.add_subparsers(dest="skill_action", required=True)

    rec = skill_sub.add_parser("record", help="Grabar sesión de habilidades")
    rec.add_argument("--name", required=True, help="Nombre de la habilidad")
    rec.add_argument("--target-url", default="", help="URL inicial de la sesión")

    comp = skill_sub.add_parser("compile", help="Compilar sesión a Skill AST")
    comp.add_argument("--session-id", required=True, help="ID de la sesión grabada")

    rep = skill_sub.add_parser("replay", help="Replicar habilidad compilada")
    rep.add_argument("--skill-id", required=True, help="ID de la habilidad a replicar")

    skill_sub.add_parser("list", help="Listar habilidades y sesiones grabadas")

    args = parser.parse_args()

    if args.subcommand == "skill":
        handle_skill_cli(args)
        return

    tauri_dir = _find_tauri_root()
    if tauri_dir is None:
        print(
            "🔴 [FATAL] No se pudo localizar el root físico C5-REAL (src-tauri/Cargo.toml).\n    cortex-bridge requiere el checkout completo del monorepo BABYLON-60\n    (no funciona desde una instalación aislada `pip install cortex-persist`).\n    Clona el repositorio completo: git clone git@github.com:borjamoskv/BABYLON-60.git",
            file=sys.stderr,
        )
        sys.exit(1)
    cargo_toml = tauri_dir / "Cargo.toml"
    print("🟢 [CORTEX-BRIDGE] Transducción iniciada. Ignición C5-REAL del VoidLedger Rust.")
    try:
        bft_key = os.environ.get("CORTEX_BFT_KEY") or os.environ.get("CORTEX_VAULT_KEY")
        if not bft_key:
            print(
                "🟡 [WARNING] CORTEX_BFT_KEY o CORTEX_VAULT_KEY no detectada. El núcleo Rust fallará (Zero Static HMAC Invariant).",
                file=sys.stderr,
            )
        subprocess.run(["cargo", "run", "--manifest-path", str(cargo_toml)], check=True)
    except FileNotFoundError:
        print(
            "🔴 [FATAL] 'cargo' no está instalado o no está en PATH. Instala Rust: https://rustup.rs", file=sys.stderr
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"🔴 [FATAL] El Puente CORTEX colapsó termodinámicamente. Exit Code: {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n💥 [SIGKILL] Puente CORTEX desconectado. Anergía purgada.")
        sys.exit(0)


if __name__ == "__main__":
    main()

