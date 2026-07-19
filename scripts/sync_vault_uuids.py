#!/usr/bin/env python3
# C5-REAL: Memory Vault Session UUID Synchronizer
import re
from pathlib import Path

VAULT_DIR = Path("~/.gemini/config/.cortex/memory_vault").expanduser()
BRAIN_DIR = Path("~/.gemini/antigravity/brain").expanduser()


def sync():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    consolidated = set()
    for f in VAULT_DIR.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r'conversation_id:\s*["\']?([0-9a-f\-]+)["\']?', content)
            if m:
                consolidated.add(m.group(1).strip())
        except OSError:
            pass

    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    synced = 0
    for entry in BRAIN_DIR.iterdir():
        if entry.is_dir() and uuid_pattern.match(entry.name):
            cid = entry.name
            if cid not in consolidated:
                transcript = entry / ".system_generated/logs/transcript.jsonl"
                if transcript.exists():
                    vfile = VAULT_DIR / f"b60_crystallized_{cid}.md"
                    vfile.write_text(
                        f"""---
conversation_id: "{cid}"
status: "crystallized"
---
# B60 Session {cid}
Crystallized into memory vault.
""",
                        encoding="utf-8",
                    )
                    synced += 1
    print(f"[+] Synchronized {synced} session UUIDs into {VAULT_DIR}")


if __name__ == "__main__":
    sync()
