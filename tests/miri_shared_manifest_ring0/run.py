"""Run the dependency-free source regression without changing repository lockfiles."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 7])
    args = parser.parse_args()
    fixture = Path(__file__).absolute().with_name("main.rs")
    with tempfile.TemporaryDirectory(prefix="b60-miri-ring0-") as directory:
        project = Path(directory)
        (project / "Cargo.toml").write_text(
            '[package]\nname="b60-miri-ring0"\nversion="0.0.0"\nedition="2021"\n'
            '\n[[bin]]\nname="ring0"\npath=' + json.dumps(str(fixture)) + "\n"
        )
        subprocess.run(["cargo", "generate-lockfile", "--offline"], cwd=project, check=True)
        for seed in args.seeds:
            env = dict(
                os.environ,
                MIRIFLAGS=f"-Zmiri-preemption-rate=1 -Zmiri-seed={seed}",
                # Miri embeds its package cwd; do not reuse artifacts from a removed temp project.
                CARGO_TARGET_DIR=str(project / "target"),
            )
            print(f"Miri source regression: seed={seed}", flush=True)
            subprocess.run(
                ["cargo", "+nightly", "miri", "run", "--locked", "--offline", "--quiet"],
                cwd=project, env=env, check=True,
            )


if __name__ == "__main__":
    main()
