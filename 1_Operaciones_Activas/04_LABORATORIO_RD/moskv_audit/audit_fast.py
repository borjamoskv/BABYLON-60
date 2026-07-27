import urllib.request
import json
import base64
import os

REPOS_API_URL = "https://api.github.com/users/borjamoskv/repos?per_page=100"
REPORT_PATH = "/Users/borjafernandezangulo/.gemini/antigravity/brain/5fce4bed-5cb6-448c-83a1-2435209ac42c/audit_report.md"

def fetch_json(url):
    req = urllib.request.Request(url)
    # req.add_header('Authorization', 'token YOUR_TOKEN') # if needed, but public repos don't strictly need it unless rate limited
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return None

def fetch_text(url):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return None

def fetch_workflows(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/workflows"
    contents = fetch_json(url)
    workflows = []
    if not contents or not isinstance(contents, list):
        return []
    for item in contents:
        if item['name'].endswith(('.yml', '.yaml')):
            content_url = item['download_url']
            text = fetch_text(content_url)
            if text:
                workflows.append((item['name'], text))
    return workflows

def audit_repo(repo):
    name = repo["name"]
    full_name = repo["full_name"]
    score = 100
    
    workflows = fetch_workflows(full_name)
    action_findings = []
    
    if not workflows:
        action_findings.append("No GitHub Actions found (-5)")
        score -= 5
    else:
        for fname, text in workflows:
            if "pull_request_target" in text:
                action_findings.append(f"Dangerous trigger in {fname}: pull_request_target (-10)")
                score -= 10
            if "permissions: write-all" in text:
                action_findings.append(f"Overpermissive actions in {fname}: write-all (-10)")
                score -= 10
            if "run: npm install" in text and "clean-install" not in text and "npm ci" not in text:
                action_findings.append(f"Unsafe npm install in {fname}: use npm ci (-2)")
                score -= 2
                
    # Check dependencies files for general architecture
    deps = []
    pkg = fetch_text(f"https://raw.githubusercontent.com/{full_name}/master/package.json") or fetch_text(f"https://raw.githubusercontent.com/{full_name}/main/package.json")
    if pkg: deps.append("package.json")
    
    cargo = fetch_text(f"https://raw.githubusercontent.com/{full_name}/master/Cargo.toml") or fetch_text(f"https://raw.githubusercontent.com/{full_name}/main/Cargo.toml")
    if cargo: deps.append("Cargo.toml")
    
    py = fetch_text(f"https://raw.githubusercontent.com/{full_name}/master/requirements.txt") or fetch_text(f"https://raw.githubusercontent.com/{full_name}/main/requirements.txt")
    if py: deps.append("requirements.txt")

    return {
        "name": name,
        "score": max(0, score),
        "actions": action_findings,
        "deps": deps
    }

def main():
    repos = fetch_json(REPOS_API_URL)
    if not repos:
        print("Failed to fetch repos (Rate limit?).")
        return
        
    results = []
    for repo in repos:
        if not repo["fork"]:
            print(f"Auditing {repo['name']}...")
            results.append(audit_repo(repo))
            
    overall_score = sum(r["score"] for r in results) / len(results) if results else 0
    
    report = f"# MOSKV-1 APEX: Sovereign C5-REAL Audit Report\n\n"
    report += f"**Overall Score:** {overall_score:.2f} / 100\n\n"
    report += "## Repository Analysis\n\n"
    
    for r in results:
        report += f"### {r['name']} - Score: {r['score']}/100\n"
        report += f"- **Supply Chain Files Detected:** {', '.join(r['deps']) if r['deps'] else 'None'}\n"
        report += "- **GitHub Actions:**\n"
        if r['actions']:
            for a in r['actions']: report += f"  - {a}\n"
        else:
            report += "  - OK\n"
        report += "\n"
        
    # Write to File
    with open(REPORT_PATH, "w") as f:
        f.write(report)
        
    print("Audit fast completed.")

if __name__ == '__main__':
    main()
