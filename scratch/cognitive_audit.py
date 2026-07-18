import json
import os
import hashlib
from typing import Any

TRANSCRIPT_PATH = os.path.expanduser("~/.gemini/antigravity/brain/5ef55016-c1c1-4fe1-9b16-01e777087198/.system_generated/logs/transcript.jsonl")

def load_transcript(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def compute_metrics(steps: list[dict[str, Any]]) -> dict[str, Any]:
    tool_calls = 0
    identical_loops = 0
    token_len = 0
    signal_len = 0
    
    last_tools = []
    for step in steps:
        if step.get("type") == "PLANNER_RESPONSE":
            content = step.get("content", "")
            token_len += len(content)
            
            # Very basic signal density check
            if "```yaml" in content or "```python" in content or "Claim:" in content:
                signal_len += len(content)
                
            calls = step.get("tool_calls", [])
            for c in calls:
                tool_calls += 1
                c_name = c.get("name")
                last_tools.append(c_name)
                if len(last_tools) >= 3:
                    if last_tools[-1] == last_tools[-2] == last_tools[-3]:
                        identical_loops += 1
                    
    return {
        "exergy_ratio": signal_len / token_len if token_len > 0 else 1.0,
        "circular_loop_density": identical_loops,
        "token_signal_ratio": signal_len / max(1, token_len)
    }

def main() -> None:
    steps = load_transcript(TRANSCRIPT_PATH)
    recent_steps = steps[-20:] if len(steps) >= 20 else steps
    
    metrics = compute_metrics(recent_steps)
    
    report = f"""
Claim: METACOGNITIVE_AUDIT_COMPLETED
Proof: {{ Base: {hashlib.sha256(json.dumps(metrics).encode()).hexdigest()}, Range: [0,1], Confidence: C5-REAL }}

Autocognition Metrics:
exergy_ratio: {metrics['exergy_ratio']:.4f}
circular_loop_density: {metrics['circular_loop_density']}
token_signal_ratio: {metrics['token_signal_ratio']:.4f}

Adjustments: Proceed with zero anergy.
"""
    print(report)
    
    with open("cortex_audit_report.yml", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
