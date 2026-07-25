# C5-REAL EXERGY CERTIFIED
import sys
import json
import os
from collections import Counter
import typing

def calculate_metrics(transcript_path: str) -> None:
    if not os.path.exists(transcript_path):
        print("Transcript not found.")
        return

    with open(transcript_path, "r") as f:
        lines = f.readlines()

    last_20 = lines[-20:]
    total_model_words = 0
    structured_words = 0
    fluff_words = 0
    commands_run: typing.Counter[str] = Counter()

    for line in last_20:
        data = json.loads(line)
        if data.get("source") == "MODEL" and "content" in data:
            content = data["content"]
            words = content.split()
            total_model_words += len(words)

            in_code_block = False
            for c_line in content.split("\n"):
                if c_line.startswith("```") or c_line.startswith(">"):
                    in_code_block = not in_code_block
                    structured_words += len(c_line.split())
                elif in_code_block:
                    structured_words += len(c_line.split())
                elif c_line.startswith("- **Ω") or c_line.startswith("[CORTEX"):
                    structured_words += len(c_line.split())
                else:
                    fluff_words += len(c_line.split())

        if data.get("source") == "MODEL" and "tool_calls" in data:
            for tc in data["tool_calls"]:
                if tc["name"] == "run_command":
                    cmd = tc["args"].get("CommandLine", "")
                    commands_run[cmd] += 1

    signal_density = structured_words / max(total_model_words, 1)
    anergy_ratio = fluff_words / max(total_model_words, 1)
    repeated_cmds = sum(1 for c, v in commands_run.items() if v > 1)

    print("```yaml")
    print("vector: metacognitive_state_audit")
    print(f"target: {transcript_path}")
    print("metrics:")
    print(f"  exergy_ratio: {signal_density:.2f}")
    print(f"  anergy_ratio: {anergy_ratio:.2f}")
    print(f"  repeated_commands: {repeated_cmds}")
    print("```")

if __name__ == "__main__":
    conv_id = sys.argv[1] if len(sys.argv) > 1 else "380ff690-d630-42f7-a5c7-cca8694d58a0"
    path = f"/Users/borjafernandezangulo/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl"
    calculate_metrics(path)
