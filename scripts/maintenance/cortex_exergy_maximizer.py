# C5-REAL EXERGY CERTIFIED
import os
import subprocess

def maximize_exergy():
    print("Initiating C5-REAL AST Collapse...")

    # Python Exergy (Ruff AST Collapse)
    subprocess.run(["uv", "run", "ruff", "check", ".", "--fix", "--unsafe-fixes"], check=False)
    subprocess.run(["uv", "run", "ruff", "format", "."], check=False)

    # Rust Exergy
    if os.path.exists("strike-rs"):
        subprocess.run(
            ["cargo", "clippy", "--fix", "--allow-dirty", "--allow-no-vcs", "--workspace"],
            cwd="strike-rs",
            check=False,
        )
        subprocess.run(["cargo", "fmt", "--all"], cwd="strike-rs", check=False)

    # Frontend Exergy (TypeScript/React)
    if os.path.exists("package.json"):
        subprocess.run(["npm", "run", "lint", "--if-present", "--", "--fix"], check=False)

    # Git Sentinel (R4)
    subprocess.run(["git", "add", "."])
    result = subprocess.run(
        ["git", "commit", "-m", "refactor(core): apply systemic exergy maximization (ITERA)"],
        capture_output=True,
        text=True,
    )

    if "nothing to commit" in result.stdout:
        print("State stable. No anergy detected.")
    else:
        hash_result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        print(f"C5-REAL Hash: {hash_result.stdout.strip()}")

if __name__ == "__main__":
    maximize_exergy()
