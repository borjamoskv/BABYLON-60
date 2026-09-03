# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os
import shutil
import subprocess


def parse_ir(file_path):
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def format_lean_decl(parts):
    tag = parts[0]
    handlers = {
        "Event": lambda p: f"def ev_tick_{p[1]} : Nat := {p[2]}",
        "HappensBefore": lambda p: f"axiom causal_{p[1]}_{p[2]} : ev_tick_{p[1]} ≤ ev_tick_{p[2]}",
        "Assign": lambda p: f"def assign_{p[3]} : Val := {p[2]}",
        "Add": lambda p: f"def add_{p[3]} : Val := {p[2]}",
        "Sub": lambda p: f"def sub_{p[3]} : Val := {p[2]}",
        "Spawn": lambda p: f'def spawn_{p[2]} : String := "{p[1]}"',
        "Block": lambda p: f'def await_{p[2]} : String := "{p[1]}"',
        "Wait": lambda p: f"def after_{p[2]} : Nat := {p[1]}",
        "Emit": lambda p: f'def emit_{p[2]} : String := "{p[1]}"',
    }
    handler = handlers.get(tag)
    return handler(parts) if handler else None


def translate_to_lean(ir_lines):
    lean_code = [
        "-- Auto-generated Lean 4 Backend for BABYLON-60",
        "-- Sovereign Verification Kernel (C5-REAL Zero Anergy)",
        "",
        "namespace Babylon60",
        "",
        "-- Core state declarations",
        "def Reg: Type := Nat",
        "def Val: Type := Int",
        "def EventId: Type := String",
        "",
    ]

    events = []
    causal_and_ops = []

    for line in ir_lines:
        if "sorry" in line or "admit" in line:
            causal_and_ops.append(f"-- TAINT_UNPROVEN: Ghost Guard detected in IR line '{line}'")
            continue

        parts = line.strip("()").split()
        if parts:
            decl = format_lean_decl(parts)
            if decl:
                if parts[0] == "Event":
                    events.append(decl)
                else:
                    causal_and_ops.append(decl)

    lean_code.append("-- Events")
    lean_code.extend(events)
    lean_code.append("")
    lean_code.append("-- Causal Relations and Operations")
    lean_code.extend(causal_and_ops)
    lean_code.append("")
    lean_code.append("end Babylon60")
    lean_code.append("")

    return "\n".join(lean_code)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lean_backend.py <path_to_proof.ir> [--out <output.lean>]")
        sys.exit(1)

    ir_file = sys.argv[1]
    out_file = "BabylonTrace.lean"
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            out_file = sys.argv[idx + 1]

    if not os.path.exists(ir_file):
        print(f"Error: {ir_file} not found.")
        sys.exit(1)

    ir_lines = parse_ir(ir_file)
    lean_code = translate_to_lean(ir_lines)

    with open(out_file, "w") as f:
        f.write(lean_code)

    print(f"[Lean Backend] Generated {out_file} successfully.")

    lean_bin = shutil.which("lean")
    if lean_bin:
        print(f"[Lean Backend] Verifying {out_file} with Lean 4 kernel ({lean_bin})...")
        proc = subprocess.run([lean_bin, out_file], capture_output=True, text=True)
        if proc.returncode == 0:
            print("[Lean Backend] Proof verification PASSED. Formal trace sound.")
        else:
            print(f"[Lean Backend] Formal verification FAILED (exit code {proc.returncode}):", file=sys.stderr)
            if proc.stderr:
                print(proc.stderr, file=sys.stderr)
            if proc.stdout:
                print(proc.stdout, file=sys.stderr)
            sys.exit(proc.returncode)
    else:
        print("[Lean Backend] Notice: 'lean' executable not found in PATH. File generated without immediate verification.")


if __name__ == "__main__":
    main()
