import os
import hashlib

def get_hash_and_size(filepath):
    if not os.path.exists(filepath):
        return None, 0
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        content = f.read()
        h.update(content)
        return h.hexdigest(), len(content)

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    pairs = [
        ("cortex/audits/ing-inv/pycharm_audit.md", "cortex/audits/pycharm_2026.1.4/pycharm_audit.md"),
        ("cortex/audits/ing-inv/webstorm_audit.md", "cortex/audits/webstorm_2026.2/webstorm_audit.md"),
        ("cortex/audits/ing-inv/codex_claude_deep_audit.md", "cortex/audits/codex/codex_claude_deep_audit.md"),
        ("cortex/audits/ing-inv/copilot_sdk_audit_report.md", "cortex/audits/copilot/copilot_sdk_audit_report.md"),
        ("cortex/audits/ing-inv/vscode_audit.md", "cortex/audits/vscode/vscode_audit.md"),
        ("cortex/audits/ing-inv/claude_science_audit_report.md", "cortex/audits/claude_science/claude_science_audit_report.md"),
        ("cortex/audits/ing-inv/flow_ax_audit_report.md", "cortex/audits/flow/flow_ax_audit_report.md"),
    ]
    
    for p1, p2 in pairs:
        path1 = os.path.join(root, p1)
        path2 = os.path.join(root, p2)
        h1, s1 = get_hash_and_size(path1)
        h2, s2 = get_hash_and_size(path2)
        print(f"Comparing {os.path.basename(p1)}:")
        print(f"  {p1}: hash={h1[:16]}..., size={s1}")
        print(f"  {p2}: hash={h2[:16]}..., size={s2}")
        print(f"  Same: {h1 == h2}")
        print()

if __name__ == "__main__":
    main()
