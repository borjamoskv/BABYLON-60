"""
Test suite para el Kimi K3 Swarm Sovereign Orchestrator v2.0

Ejecutar:
  python3 test_swarm.py                    # Test Moonshot API (remoto)
  python3 test_swarm.py --backend local_vllm  # Test vLLM local (air-gapped)
  python3 test_swarm.py --p 2 --s 2        # Test con topología 2x2
"""

import asyncio
import argparse
from swarm_orchestrator import run_swarm_orchestrator


PROMPTS = {
    "simple": "Resume en 3 puntos clave la importancia de la topología PxS para evitar thrashing en sistemas de memoria unificada.",
    "research": "Investiga las diferencias arquitectónicas entre Kimi K3, Claude Opus 4 y GPT-5.6 Sol en cuanto a: (1) escalado de expertos MoE, (2) longitud de contexto, (3) capacidades multimodales.",
    "code_audit": "Analiza las vulnerabilidades potenciales de un servidor MCP que usa stdio como transporte: inyección de comandos, deserialización insegura y falta de autenticación.",
}


async def main():
    parser = argparse.ArgumentParser(description="Test Kimi Swarm Orchestrator v2.0")
    parser.add_argument("--p", type=int, default=2, help="Procesos (P cores)")
    parser.add_argument("--s", type=int, default=1, help="Hilos por proceso (S threads)")
    parser.add_argument("--backend", default="moonshot", choices=["moonshot", "local_vllm", "local_mlx"])
    parser.add_argument("--prompt", default="simple", choices=list(PROMPTS.keys()) + ["custom"])
    parser.add_argument("--custom", type=str, default=None, help="Prompt personalizado")
    args = parser.parse_args()

    prompt = args.custom if args.prompt == "custom" and args.custom else PROMPTS.get(args.prompt, PROMPTS["simple"])

    print(f"""
╔══════════════════════════════════════════════════════╗
║  🌌 KIMI K3 SWARM — TEST DE COLAPSO CUÁNTICO v2.0  ║
╠══════════════════════════════════════════════════════╣
║  Backend:   {args.backend:<40} ║
║  Topología: P={args.p} × S={args.s} (max {args.p * args.s} subagentes)    {' ' * (25 - len(str(args.p * args.s)))}║
║  Prompt:    {args.prompt:<40} ║
╚══════════════════════════════════════════════════════╝
""")

    def on_progress(task_id, status, elapsed):
        icon = "✅" if status == "OK" else "❌"
        print(f"  {icon} Subagente {task_id}: {status} ({elapsed:.1f}s)")

    result = await run_swarm_orchestrator(
        prompt=prompt,
        p_cores=args.p,
        s_threads=args.s,
        backend=args.backend,
        on_progress=on_progress
    )

    print("\n" + "=" * 60)
    print("📋 RESULTADO FINAL (Síntesis + Telemetría)")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
