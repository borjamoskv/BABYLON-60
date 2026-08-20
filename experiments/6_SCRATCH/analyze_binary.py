# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ CLI BINARY ANALYZER EXPERIMENT | STATE: C5-REAL
# ============================================================================
"""
analyze_binary.py — Interactive CLI tool for testing SovereignBinaryAnalyzer on local binaries.
Usage:
    python3 experiments/analyze_binary.py [path_to_binary] [--limit 100] [--out report.html]
"""

import os
import sys
import argparse

# Add src/ to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kernel.sovereign_binary_analyzer import SovereignBinaryAnalyzer


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Sovereign Binary Analyzer & CFG Generator")
    parser.add_argument("binary", nargs="?", default="/bin/ls", help="Path to executable binary (default: /bin/ls)")
    parser.add_argument("--limit", type=int, default=100, help="Max instructions to disassemble (default: 100)")
    parser.add_argument("--out", type=str, default="cfg_report.html", help="Output HTML report path")
    args = parser.parse_args()

    binary_path = os.path.abspath(args.binary)
    if not os.path.isfile(binary_path):
        print(f"❌ Error: File not found at {binary_path}")
        sys.exit(1)

    print("============================================================================")
    print(" █ BABYLON-60 SOVEREIGN BINARY ANALYZER & CFG ENGINE")
    print("============================================================================")
    print(f"Target Binary : {binary_path}")

    analyzer = SovereignBinaryAnalyzer(binary_path)
    meta = analyzer.metadata

    print(f"Format        : {meta.format}")
    print(f"Architecture  : {meta.architecture}")
    print(f"Sections Count: {len(meta.sections)}")
    print(f"Entry Point   : {hex(meta.entry_point) if meta.entry_point else 'N/A'}")
    print("----------------------------------------------------------------------------")

    # Disassemble
    print(f"Disassembling code section (max {args.limit} insns)...")
    instructions = analyzer.disassemble_section(max_instructions=args.limit)
    print(f"Extracted {len(instructions)} instructions.")

    # Build CFG
    blocks = analyzer.build_cfg(instructions)
    print(f"Constructed {len(blocks)} Basic Blocks.")

    # Print Terminal Preview of Basic Blocks
    print("\n--- [TERMINAL CFG BASIC BLOCKS PREVIEW] ---")
    for block_id, block in list(blocks.items())[:5]:
        succs_str = ", ".join(block.successors) if block.successors else "END"
        print(f"▸ [{block_id}] ({len(block.instructions)} insns) ➔ Successors: [{succs_str}]")
        for ins in block.instructions[:3]:
            print(f"    {hex(ins.address)}: {ins.mnemonic} {ins.op_str}")
        if len(block.instructions) > 3:
            print("    ...")

    if len(blocks) > 5:
        print(f"... and {len(blocks) - 5} more blocks.")

    # Render HTML
    out_file = os.path.abspath(args.out)
    analyzer.render_mermaid_html(blocks, out_file)
    print("----------------------------------------------------------------------------")
    print(f"✅ Interactive HTML CFG report generated at:\n   file://{out_file}")
    print("============================================================================")


if __name__ == "__main__":
    main()
