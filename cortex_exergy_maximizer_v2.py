# C5-REAL EXERGY CERTIFIED
import os
import subprocess


def maximize_exergy():
    print("Initiating C5-REAL AST Collapse Phase 2...")

    # Rust Exergy
    if os.path.exists("strike-rs"):
        subprocess.run(
            ["cargo", "clippy", "--fix", "--allow-dirty", "--allow-no-vcs", "--workspace"], cwd="strike-rs", check=False
        )
        subprocess.run(["cargo", "fmt", "--all"], cwd="strike-rs", check=False)

    # JS/TS Exergy
    subprocess.run(["npx", "--yes", "prettier", "--write", "."], check=False)

    # Git Sentinel (R4)
    subprocess.run(["git", "add", "."])
    result = subprocess.run(
        ["git", "commit", "-m", "refactor(core): C5-REAL AST Pareto dominance pass"], capture_output=True, text=True
    )

    if "nothing to commit" in result.stdout:
        print("State stable. No anergy detected.")
    else:
        hash_result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        print(f"C5-REAL Hash: {hash_result.stdout.strip()}")


if __name__ == "__main__":
    maximize_exergy()
