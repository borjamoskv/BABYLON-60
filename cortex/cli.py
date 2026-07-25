# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
MOSKV-1 APEX C5-REAL Categorical Logic 896 Primitives CLI
=========================================================
Command line interface for morphism cost evaluation, diagrammatic collision audits,
and primitive indexing.
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cortex.categorical_896_engine import Categorical896Engine

def main() -> None:
    parser = argparse.ArgumentParser(description="C5-REAL Categorical Logic 896 Primitives Transducer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate morphism cost mu(alpha)")
    eval_parser.add_argument("--ids", nargs="+", type=int, required=True, help="Primitive sequence IDs")
    eval_parser.add_argument("--friction", type=float, default=0.0, help="Overhead friction delta")

    # Command: collisions
    col_parser = subparsers.add_parser("collisions", help="Audit diagrammatic collisions")
    col_parser.add_argument("--active-ids", nargs="+", type=int, required=True, help="Active primitive IDs")

    # Command: query
    query_parser = subparsers.add_parser("query", help="Query primitive definition")
    query_parser.add_argument("--id", type=int, help="Primitive ID")
    query_parser.add_argument("--code", type=str, help="Primitive code")

    args = parser.parse_args()
    yaml_path = os.path.join(os.path.dirname(__file__), "../primitives/896_categorical_logic_primitives.yml")
    engine = Categorical896Engine(yaml_path=os.path.abspath(yaml_path))

    if args.command == "evaluate":
        cost = engine.evaluate_morphism_cost(args.ids, friction=args.friction)
        res = {"sequence": args.ids, "friction": args.friction, "morphism_cost_mu": cost, "status": "VALIDATED_C5_REAL"}
        print(json.dumps(res, indent=2))

    elif args.command == "collisions":
        active_set = set(args.active_ids)
        collisions = engine.detect_diagrammatic_collisions(active_set)
        res = {
            "active_ids": args.active_ids,
            "collision_count": len(collisions),
            "collisions": collisions,
            "status": "COLLISION_AUDIT_COMPLETE",
        }
        print(json.dumps(res, indent=2))

    elif args.command == "query":
        prim = None
        if args.id and args.id in engine.primitives:
            prim = engine.primitives[args.id]
        elif args.code and args.code in engine.code_index:
            prim = engine.code_index[args.code]

        if prim:
            print(json.dumps(prim.__dict__, indent=2))
        else:
            print(json.dumps({"error": "Primitive not found"}, indent=2))
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
