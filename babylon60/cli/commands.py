import argparse
import logging

from babylon60.commands.autodidact import run_autodidact
from babylon60.commands.ethos import run_ethos
from babylon60.commands.itera import run_itera
from babylon60.commands.logos import run_logos
from babylon60.commands.mythos import run_mythos
from babylon60.commands.purge import run_purge
from babylon60.commands.seal import run_seal
from babylon60.commands.ship import run_ship
from babylon60.commands.swarm import run_swarm
from babylon60.commands.ultrathink import run_ultrathink
from babylon60.commands.verify import run_verify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("babylon60.cli.commands")

def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 C5-REAL Native Commands CLI (High-Exergy Aliases Enabled)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ultrathink
    ut_parser = subparsers.add_parser("ultrathink", aliases=["ut", "apex"], help="Absolute Sovereignty & Nocturnal Orchestration")
    ut_parser.add_argument("goal", type=str, help="The complex architectural target")
    ut_parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")

    # autodidact
    ad_parser = subparsers.add_parser("autodidact", aliases=["ad", "omega"], help="Autopoiesis & AST Rewrite")
    ad_parser.add_argument("--target", type=str, default=".", help="Target path to audit")

    # purge
    subparsers.add_parser("purge", aliases=["p", "brutalismo"], help="Kinetic Brutalism: Wipes entropy and kills daemons")

    # seal
    seal_parser = subparsers.add_parser("seal", aliases=["sl", "collapse"], help="Terminal State Collapse / P0 Singularity")
    seal_parser.add_argument("--tag", type=str, default="v1.0.0", help="Annotated Git Tag")

    # itera
    it_parser = subparsers.add_parser("itera", aliases=["it", "mejoralo"], help="Long-Horizon Execution & Multi-Step Optimization")
    it_parser.add_argument("--steps", type=int, default=5, help="Number of iterations")

    # logos
    lo_parser = subparsers.add_parser("logos", aliases=["lg", "transduce"], help="Semantic Transduction & Entropy Extraction")
    lo_parser.add_argument("entropy", type=str, help="Raw Operator Intent")

    # ethos
    et_parser = subparsers.add_parser("ethos", aliases=["et", "zk"], help="Zero-Knowledge Validation & Structural Integrity")
    et_parser.add_argument("payload", type=str, help="Invariant payload to validate")

    # mythos
    subparsers.add_parser("mythos", aliases=["my", "graph"], help="Narrative & Ledger Compression")

    # ship
    sh_parser = subparsers.add_parser("ship", aliases=["sh", "commit"], help="Payload Delivery & Ledger Append")
    sh_parser.add_argument("payload", type=str, help="Validated invariant payload")

    # swarm
    sw_parser = subparsers.add_parser("swarm", aliases=["sw", "mitosis"], help="Isolated Swarm Mitosis & Multi-Agent Handoff")
    sw_parser.add_argument("task", type=str, help="Task description")
    sw_parser.add_argument("--count", type=int, default=3, help="Subagent worker count")

    # verify
    subparsers.add_parser("verify", aliases=["vf", "audit"], help="BFT Ledger Cryptographic Verification")

    args = parser.parse_args()

    cmd = args.command
    if cmd in ["ultrathink", "ut", "apex"]:
        run_ultrathink(args.goal, args.timeout)
    elif cmd in ["autodidact", "ad", "omega"]:
        run_autodidact(args.target)
    elif cmd in ["purge", "p", "brutalismo"]:
        run_purge()
    elif cmd in ["seal", "sl", "collapse"]:
        run_seal(args.tag)
    elif cmd in ["itera", "it", "mejoralo"]:
        run_itera(args.steps)
    elif cmd in ["logos", "lg", "transduce"]:
        run_logos(args.entropy)
    elif cmd in ["ethos", "et", "zk"]:
        run_ethos(args.payload)
    elif cmd in ["mythos", "my", "graph"]:
        run_mythos()
    elif cmd in ["ship", "sh", "commit"]:
        run_ship(args.payload)
    elif cmd in ["swarm", "sw", "mitosis"]:
        run_swarm(args.task, args.count)
    elif cmd in ["verify", "vf", "audit"]:
        run_verify()

if __name__ == "__main__":
    main()
