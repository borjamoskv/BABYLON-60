# [C5-REAL] Exergy-Maximized
#!/usr/bin/env python3
"""
cat_id: ouroboros-mutation
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import datetime
import hashlib
import os
import re
import subprocess
import sys


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def main():
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    if not os.path.exists(readme_path):
        logging.getLogger(__name__).info("[OUROBOROS] README.md not found. Aborting mutation.")
        sys.exit(0)

    # 1. Get Exergy Metrics (Staged diff)
    diff_stat = run_cmd("git diff --cached --numstat")
    lines_added = 0
    lines_deleted = 0
    staged_files = 0

    for line in diff_stat.split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            added, deleted, filename = parts
            if filename == "README.md":
                continue  # Ignore README's own previous mutation
            if added != "-":
                lines_added += int(added)
            if deleted != "-":
                lines_deleted += int(deleted)
            staged_files += 1

    # Skip mutation if nothing else is staged (to avoid infinite loops)
    if staged_files == 0:
        sys.exit(0)

    # 2. Generate Deterministic CORTEX Hash
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw_entropy = f"{timestamp}:{lines_added}:{lines_deleted}:{staged_files}"
    exergy_hash = hashlib.sha3_256(raw_entropy.encode()).hexdigest()[:16]

    # 3. Format the Pulse
    pulse_text = (
        f"> **[OUROBOROS PULSE]** `LAST_MUTATION: {timestamp}` | "
        f"`EXERGY_YIELD: +{lines_added}/-{lines_deleted} ({staged_files} files)` | "
        f"`HASH: {exergy_hash}`"
    )

    # 4. Mutate README.md
    with open(readme_path, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(<!-- OUROBOROS_PULSE_START -->).*?(<!-- OUROBOROS_PULSE_END -->)", re.DOTALL
    )
    if not pattern.search(content):
        logging.getLogger(__name__).info("[OUROBOROS] Anchor tags not found in README.md. Aborting mutation.")
        sys.exit(0)

    mutated_content = pattern.sub(rf"\1\n{pulse_text}\n\2", content)

    if mutated_content != content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(mutated_content)

        # 5. Stage the mutation
        run_cmd(f"git add {readme_path}")
        logging.getLogger(__name__).info(f"[C5-REAL] Ouroboros Mutation successful. Exergy: {exergy_hash}")


if __name__ == "__main__":
    main()
