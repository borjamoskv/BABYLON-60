# C5-REAL EXERGY CERTIFIED
import os
import json
import subprocess
import shutil
import urllib.request

REPOS_API_URL = "https://api.github.com/users/borjamoskv/repos?per_page=100"
WORKSPACE = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/04_LABORATORIO_RD/moskv_audit/repos"
REPORT_PATH = "/Users/borjafernandezangulo/.gemini/antigravity/brain/5fce4bed-5cb6-448c-83a1-2435209ac42c/audit_report.md"

def fetch_repos():
    req = urllib.request.Request(REPOS_API_URL)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def run_cmd(cmd, cwd=None):
    try:
        res = subprocess.run(cmd, shell=False, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout
    except Exception as e:
        return str(e)

def analyze_actions(repo_path):
    workflows_dir = os.path.join(repo_path, ".github", "workflows")
    findings = []
    if not os.path.exists(workflows_dir):
        return ["No GitHub Actions found (-5)"]
    for root, _, files in os.walk(workflows_dir):
        for f in files:
            if f.endswith((".yml", ".yaml")):
                filepath = os.path.join(root, f)
                with open(filepath, "r") as yaml_file:
                    content = yaml_file.read()
                    if "pull_request_target" in content:
                        findings.append(f"Dangerous trigger in {f}: pull_request_target (-10)")
                    if "permissions: write-all" in content:
                        findings.append(f"Overpermissive actions in {f}: write-all (-10)")
    return findings

def audit_repo(repo):
    name = repo["name"]
    clone_url = repo["clone_url"]
    repo_path = os.path.join(WORKSPACE, name)

    print(f"Auditing {name}...")

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    run_cmd(f"git clone --depth 1 {clone_url} {repo_path}")

    score = 100

    # 1. GitHub Actions
    action_findings = analyze_actions(repo_path)
    if "No GitHub Actions found (-5)" in action_findings:
        score -= 5
    for f in action_findings:
        if "(-10)" in f:
            score -= 10

    # 2. Semgrep
    semgrep_out = run_cmd("semgrep scan --config auto --json", cwd=repo_path)
    semgrep_findings = []
    try:
        res = json.loads(semgrep_out)
        results = res.get("results", [])
        for r in results:
            sev = r.get("extra", {}).get("severity", "INFO")
            if sev in ["ERROR", "WARNING"]:
                semgrep_findings.append(f"{r['check_id']}: {sev}")
                score -= 5 if sev == "ERROR" else 2
    except Exception:
        semgrep_findings.append("Failed to run semgrep.")

    score = max(0, score)

    return {
        "name": name,
        "score": score,
        "actions": action_findings,
        "semgrep": semgrep_findings
    }

def main():
    os.makedirs(WORKSPACE, exist_ok=True)
    repos = fetch_repos()

    results = []
    for repo in repos:
        if not repo["fork"]:
            results.append(audit_repo(repo))

    overall_score = sum(r["score"] for r in results) / len(results) if results else 0

    # Generate Report
    report = "# MOSKV-1 APEX: Sovereign C5-REAL Audit Report\n\n"
    report += f"**Overall Score:** {overall_score:.2f} / 100\n\n"
    report += "## Repository Analysis\n\n"

    for r in results:
        report += f"### {r['name']} - Score: {r['score']}/100\n"
        report += "- **GitHub Actions:**\n"
        if r['actions']:
            for a in r['actions']: report += f"  - {a}\n"
        else:
            report += "  - OK\n"

        report += "- **Semgrep Findings:**\n"
        if r['semgrep']:
            for s in r['semgrep'][:5]: report += f"  - {s}\n"
            if len(r['semgrep']) > 5: report += f"  - ... and {len(r['semgrep']) - 5} more.\n"
        else:
            report += "  - OK\n"

        report += "\n"

    with open(REPORT_PATH, "w") as f:
        f.write(report)

    print(f"Audit completed. Report saved to {REPORT_PATH}")

if __name__ == '__main__':
    main()
