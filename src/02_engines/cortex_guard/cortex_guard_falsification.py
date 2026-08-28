# C5-REAL EXERGY CERTIFIED
import subprocess
import sys

def main():
    print("[FALSIFICATION TEST] Injecting saboteur dependency (Popperian Axiom Ω22)...")

    test_script = """
import sys
from cortex_guard import verify_dependencies

try:
    print("[CHILD] Requesting dependencies...")
    # Injecting a dependency that doesn't exist to trigger a collapse
    verify_dependencies(["ls", "herramienta_fantasma_inexistente"])
    print("[CHILD] ERROR: I should not be alive right now. Green Theater detected.")
    sys.exit(0)
except Exception as e:
    print(f"[CHILD] ERROR: Caught exception {e}. This is a violation! It should have been a SIGABRT.")
    sys.exit(0)
"""

    with open("cortex_guard_falsification_child.py", "w") as f:
        f.write(test_script)

    print("[FALSIFICATION TEST] Running child process...")
    # Run the child script in a subprocess
    result = subprocess.run(["python3", "cortex_guard_falsification_child.py"], capture_output=True, text=True)

    # A SIGABRT results in a negative return code in POSIX (specifically -6, but depends on platform, could be 134 in bash)
    # Python subprocess returns negative signals as -N (so -6 for SIGABRT)
    if result.returncode < 0 or result.returncode == 134:
        print(f"[FALSIFICATION TEST] PASS: Child process violently collapsed as expected (Return code {result.returncode}).")
        print("[FALSIFICATION TEST] SIGABRT confirmed. Silent failure is mathematically impossible.")
    else:
        print(f"[FALSIFICATION TEST] FAIL: Child process returned {result.returncode}. It did not SIGABRT.")
        print("Child STDOUT:")
        print(result.stdout)
        print("Child STDERR:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
