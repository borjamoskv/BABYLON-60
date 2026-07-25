import logging
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from causal_isomorphism.transpiler import CausalIsomorphismTranspiler

def cmd_transpile(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        logging.info(f'❌ Source file not found: {source}', file=sys.stderr)
        return 1
    output_dir = Path(args.output) if args.output else None
    transpiler = CausalIsomorphismTranspiler()
    result = transpiler.transpile_file(source, output_dir)
    logging.info(result.full_report())
    if output_dir:
        logging.info(f'\n💾 Solidity: {result.solidity_path}')
        logging.info(f'💾 Rust:     {result.rust_path}')
        logging.info(f'💾 Report:   {result.report_path}')
    if args.print_sol:
        logging.info('\n── Generated Solidity ──')
        logging.info(result.solidity_output)
    if args.print_rust:
        logging.info('\n── Generated Rust ──')
        logging.info(result.rust_output)
    return 0 if result.is_valid else 1

def cmd_validate(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        logging.info(f'❌ Source file not found: {source}', file=sys.stderr)
        return 1
    transpiler = CausalIsomorphismTranspiler()
    result = transpiler.transpile_file(source)
    logging.info(result.full_report())
    return 0 if result.is_valid else 1

def cmd_inspect(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        logging.info(f'❌ Source file not found: {source}', file=sys.stderr)
        return 1
    from causal_isomorphism.parser_fsharp import FSharpParser
    parser = FSharpParser()
    ir_module = parser.parse_file(source)
    logging.info(f'Module: {ir_module.name}')
    logging.info(f'Source Layer: {ir_module.source_layer.value}')
    logging.info(f'Submodules: {len(ir_module.submodules)}')
    logging.info()
    for union in ir_module.unions:
        logging.info(f"  Union: {union.name} ({('simple enum' if union.is_simple_enum else 'tagged')})")
        for case in union.cases:
            if case.payload_fields:
                fields = ', '.join((f'{n}: {t}' for n, t in case.payload_fields))
                logging.info(f'    | {case.name} of {fields}')
            else:
                logging.info(f'    | {case.name}')
    for sub in ir_module.submodules:
        logging.info(f'\n  Submodule: {sub.name}')
        for union in sub.unions:
            logging.info(f"    Union: {union.name} ({('simple enum' if union.is_simple_enum else 'tagged')})")
            for case in union.cases:
                if case.payload_fields:
                    fields = ', '.join((f'{n}: {t}' for n, t in case.payload_fields))
                    logging.info(f'      | {case.name} of {fields}')
                else:
                    logging.info(f'      | {case.name}')
        for record in sub.records:
            logging.info(f'    Record: {record.name}')
            for fld in record.fields:
                logging.info(f'      {fld.name}: {fld.ir_type}')
        for func in sub.functions:
            logging.info(f'    Function: {func.name} [{func.classification.name}]')
    for func in ir_module.functions:
        logging.info(f'  Function: {func.name} [{func.classification.name}]')
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(prog='causal-isomorphism', description='Causal Isomorphism Transpiler — F# → {Solidity, Rust}')
    subparsers = parser.add_subparsers(dest='command', required=True)
    p_transpile = subparsers.add_parser('transpile', help='Transpile F# source to Solidity and Rust')
    p_transpile.add_argument('source', help='Path to F# source file')
    p_transpile.add_argument('-o', '--output', help='Output directory for generated files')
    p_transpile.add_argument('--print-sol', action='store_true', help='Print generated Solidity to stdout')
    p_transpile.add_argument('--print-rust', action='store_true', help='Print generated Rust to stdout')
    p_validate = subparsers.add_parser('validate', help='Validate F# source against Trilingual Regime')
    p_validate.add_argument('source', help='Path to F# source file')
    p_inspect = subparsers.add_parser('inspect', help='Inspect the IR generated from F# source')
    p_inspect.add_argument('source', help='Path to F# source file')
    args = parser.parse_args()
    handlers: dict[str, object] = {'transpile': cmd_transpile, 'validate': cmd_validate, 'inspect': cmd_inspect}
    handler = handlers[args.command]
    return handler(args)
if __name__ == '__main__':
    sys.exit(main())