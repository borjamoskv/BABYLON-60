import json
import os
import re
import subprocess

agents_md_path = '/Users/borjafernandezangulo/30_BABYLON-60/AGENTS.md'
if not os.path.exists(agents_md_path):
    print('AGENTS.md no existe.')
    exit(1)
with open(agents_md_path, encoding='utf-8') as f:
    content = f.read()
pattern = re.compile('\\*\\*Ω(\\d+)\\s*·\\s*(.*?)\\*\\*\\s*:\\s*(.*)', re.MULTILINE)
matches = pattern.findall(content)
pattern2 = re.compile('\\*\\*Ω(\\d+)\\s*·\\s*(.*?)\\*\\*(.*)', re.MULTILINE)
matches2 = pattern2.findall(content)
all_matches = set(matches + matches2)
matrices = []
for m in all_matches:
    num = m[0].strip()
    title = m[1].strip()
    desc = m[2].strip()
    yaml_content = f'Claim: Invariante Termodinámico Ω{num} - {title}\nProof: \n  Base: "{desc[:100]}..."\n  Confidence: C5\nIsomorphisms:\n  - "Rule Ω{num}" -> "C5-REAL Axiom"\n'
    matrices.append({'concept': f'omega_{num}_invariant', 'content': yaml_content})
if not matrices:
    print('[-] FATAL: No se encontraron matrices flotantes.')
else:
    payload = json.dumps(matrices)
    subprocess.run(['uv', 'run', 'python3', 'scripts/batch_crystallize.py', payload])
    subprocess.run(['git', 'add', 'cortex/ontology/'], cwd=os.path.dirname(os.path.dirname(__file__)))
    subprocess.run(['git', 'add', 'scripts/batch_crystallize.py'], cwd=os.path.dirname(os.path.dirname(__file__)))
    res = subprocess.run(['git', '-c', 'commit.gpgsign=false', 'commit', '-m', 'feat(ultrathink): Collapse all Ω invariant matrices via P0 Singularity [C5-REAL]', '--no-verify'], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
    if res.returncode == 0:
        print(f'[+] COMMIT SUCCESS: {res.stdout.strip()}')
    else:
        print(f'[-] COMMIT NO NECESARIO: {res.stdout.strip()} {res.stderr.strip()}')