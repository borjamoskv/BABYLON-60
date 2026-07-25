#!/usr/bin/env python3
import glob
import os
import shutil


def main() -> None:
    print("⚡ [C5-REAL] Memory Vault Session Synchronizer (INV_C5_15 / INV_C5_25)")
    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    vault_dir = os.path.expanduser("~/.gemini/config/.cortex/memory_vault")

    os.makedirs(vault_dir, exist_ok=True)

    if not os.path.exists(brain_dir):
        print("⚠️ Brain directory not found, skipping sync.")
        return

    transcripts = glob.glob(f"{brain_dir}/*/.system_generated/logs/transcript.jsonl")
    synced_count = 0

    for transcript in transcripts:
        conv_id = transcript.split("/")[-4]
        try:
            with open(transcript) as f:
                content = f.read()
                # Dynamic scan for workspace relevance keywords (INV_C5_25)
                if "belongs_to_babylon" in content or "BABYLON-60" in content:
                    dest_file = os.path.join(vault_dir, f"{conv_id}.jsonl")
                    shutil.copy2(transcript, dest_file)
                    synced_count += 1
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading {transcript}: {e}")

    print(f"🟢 Synchronized {synced_count} relevant session logs into Memory Vault.")


if __name__ == "__main__":
    main()
