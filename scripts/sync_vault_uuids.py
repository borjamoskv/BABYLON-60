#!/usr/bin/env python3
import re
from pathlib import Path

VAULT_DIR = Path("~/.gemini/config/.cortex/memory_vault").expanduser()
BRAIN_DIR = Path("~/.gemini/antigravity/brain").expanduser()
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _get_consolidated_uuids() -> set[str]:
    consolidated = set()
    for f in VAULT_DIR.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r'conversation_id:\s*["\']?([0-9a-f\-]+)["\']?', content)
            if m:
                consolidated.add(m.group(1).strip())
        except OSError:
            pass
    return consolidated


def _crystallize_session(entry: Path, consolidated: set[str]) -> bool:
    if not entry.is_dir() or not UUID_PATTERN.match(entry.name):
        return False
    cid = entry.name
    if cid in consolidated:
        return False
    transcript = entry / ".system_generated/logs/transcript.jsonl"
    if not transcript.exists():
        return False

    vfile = VAULT_DIR / f"b60_crystallized_{cid}.md"
    vfile.write_text(f'---\nconversation_id: "{cid}"\nstatus: "crystallized"\n---\nCrystallized into memory vault.\n', encoding="utf-8")
    return True


def sync() -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    consolidated = _get_consolidated_uuids()
    synced = sum(1 for entry in BRAIN_DIR.iterdir() if _crystallize_session(entry, consolidated))
    print(f"[+] Synchronized {synced} session UUIDs into {VAULT_DIR}")


if __name__ == "__main__":
    sync()

