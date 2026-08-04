# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os


def parse_ir(file_path):
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def format_lean_axiom(parts):
    tag = parts[0]
    handlers = {
        "Event": lambda p: f"axiom ev_tick_{p[1]} : Nat := {p[2]}",
        "HappensBefore": lambda p: f"axiom causal_{p[1]}_{p[2]} : ev_tick_{p[1]} ≤ ev_tick_{p[2]}",
        "Assign": lambda p: f"axiom assign_{p[3]} : Val := {p[2]}",
        "Add": lambda p: f"axiom add_{p[3]} : Val := {p[2]}",
        "Sub": lambda p: f"axiom sub_{p[3]} : Val := {p[2]}",
        "Spawn": lambda p: f'axiom spawn_{p[2]} : String := "{p[1]}"',
        "Block": lambda p: f'axiom await_{p[2]} : String := "{p[1]}"',
        "Wait": lambda p: f"axiom after_{p[2]} : Nat := {p[1]}",
        "Emit": lambda p: f'axiom emit_{p[2]} : String := "{p[1]}"',
    }
    handler = handlers.get(tag)
    return handler(parts) if handler else None


def translate_to_lean(ir_lines):
    lean_code = [
        "-- Auto-generated Lean 4 Backend for BABYLON-60",
        "import Mathlib",
        "",
        "namespace Babylon60",
        "",
        "-- Core state declarations",
        "def Reg: Type := Nat",
        "def Val: Type := Int",
        "def EventId: Type := String",
        "",
        "-- Axiomatic Trace Declarations",
    ]

    for line in ir_lines:
        if "sorry" in line or "admit" in line:
            lean_code.append(f"-- TAINT_UNPROVEN: Ghost Guard detected in IR line '{line}'")
            continue

        parts = line.strip("()").split()
        if parts:
            axiom = format_lean_axiom(parts)
            if axiom:
                lean_code.append(axiom)

    lean_code.append("")
    lean_code.append("end Babylon60")
    lean_code.append("")

    return "\n".join(lean_code)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lean_backend.py <path_to_proof.ir>")
        sys.exit(1)

    ir_file = sys.argv[1]
    if not os.path.exists(ir_file):
        print(f"Error: {ir_file} not found.")
        sys.exit(1)

    ir_lines = parse_ir(ir_file)
    lean_code = translate_to_lean(ir_lines)

    out_file = "BabylonTrace.lean"
    with open(out_file, "w") as f:
        f.write(lean_code)

    print(f"[Lean Backend] Generated {out_file} successfully.")


if __name__ == "__main__":
    main()
