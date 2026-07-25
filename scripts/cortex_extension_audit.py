# C5-REAL EXERGY CERTIFIED
import json
from pathlib import Path


def audit_files() -> None:
    root = Path(".")
    extensions = {".py", ".go", ".rs", ".js", ".ts", ".yml"}
    exclude_dirs = {".venv", "node_modules", ".git", "target", "dist", "build"}

    total_files = 0
    c5_certified = 0
    c4_anergy_detected = 0

    for path in root.rglob("*"):
        if path.is_dir() or path.suffix not in extensions:
            continue

        if any(part in exclude_dirs for part in path.parts):
            continue

        total_files += 1

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        has_c5 = "C5-REAL" in content
        has_sleep = "sleep(" in content

        if has_c5:
            c5_certified += 1
        if has_sleep:
            c4_anergy_detected += 1

    print(
        json.dumps(
            {
                "total_files": total_files,
                "c5_certified": c5_certified,
                "c4_anergy": c4_anergy_detected,
                "exergy_ratio": round(c5_certified / max(total_files, 1), 3),
            }
        )
    )


if __name__ == "__main__":
    audit_files()
