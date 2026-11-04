#!/usr/bin/env python3
"""
audit_skills_ecosystem.py
Linter Determinista de Silicio (C5-REAL Quality Gate)
Audita la conformidad de la Tríada Declarativa y colisiones de disparo
sobre el ecosistema de habilidades (Global + Workspace).
"""

import os
import sys
import glob
import re
import yaml
from collections import defaultdict

def audit():
    errors = []
    warnings = []

    search_dirs = [
        os.path.expanduser('~/BABYLON-60/.agents/skills'),
        os.path.expanduser('~/.gemini/config/skills')
    ]

    files = []
    for d in search_dirs:
        if os.path.exists(d):
            files.extend(glob.glob(os.path.join(d, '*/SKILL.md')))

    files = sorted(list(set(files)))
    print(f"=== C5-REAL SKILL ECOSYSTEM AUDITOR ===")
    print(f"Total habilidades detectadas en silicio: {len(files)}")

    role_counts = {'arquitecto': 0, 'ejecutor': 0, 'auditor': 0}
    all_triggers = defaultdict(list)
    skills_data = []

    for f in files:
        rel_path = f.replace(os.path.expanduser('~'), '~')
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()

        if not content.startswith('---'):
            errors.append(f"{rel_path}: No inicia con delimitador YAML '---'")
            continue

        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append(f"{rel_path}: Delimitadores YAML incompletos")
            continue

        fm_raw = parts[1]
        body = parts[2].strip()

        try:
            fm = yaml.safe_load(fm_raw)
            if not isinstance(fm, dict):
                errors.append(f"{rel_path}: Frontmatter YAML no se parseó como diccionario")
                continue
        except Exception as e:
            errors.append(f"{rel_path}: Error parseando YAML: {e}")
            continue

        # 1. Campos obligatorios
        for req in ['name', 'description', 'role', 'directives']:
            if req not in fm:
                errors.append(f"{rel_path}: Campo obligatorio '{req}' ausente")

        # 2. Rol canónico
        role = fm.get('role')
        if role not in ['arquitecto', 'ejecutor', 'auditor']:
            errors.append(f"{rel_path}: Rol inválido '{role}'. Debe ser arquitecto, ejecutor o auditor")
        else:
            role_counts[role] += 1

        # 3. Directivas de worktree
        dirs = fm.get('directives', {})
        if not isinstance(dirs, dict):
            errors.append(f"{rel_path}: 'directives' debe ser un diccionario estructurado")
        else:
            mode = dirs.get('worktree_mode')
            phase = dirs.get('phase')
            handoff = dirs.get('handoff', {})

            if mode not in ['spec-only', 'read-write', 'audit-only']:
                errors.append(f"{rel_path}: 'worktree_mode' inválido: '{mode}'")
            if phase not in ['design', 'implementation', 'verification']:
                errors.append(f"{rel_path}: 'phase' inválida: '{phase}'")
            if not isinstance(handoff, dict) or 'upstream' not in handoff or 'downstream' not in handoff:
                errors.append(f"{rel_path}: 'handoff' debe especificar 'upstream' y 'downstream'")

        # 4. Banner tipográfico en Markdown
        if "> **Directiva Declarativa" not in body:
            warnings.append(f"{rel_path}: Falta el banner de directiva declarativa en Markdown")

        # 5. Extracción de disparadores
        desc = fm.get('description', '')
        m = re.search(r'dispara con\s*[:\s]*(.+?)(?:\.|\n|$)', desc, re.IGNORECASE)
        triggers = []
        if m:
            raw = m.group(1)
            quoted = re.findall(r'[\"|\']([^\"|\']+)[\"|\']', raw)
            if quoted:
                triggers.extend([q.strip().lower() for q in quoted if q.strip()])
            else:
                triggers.extend([p.strip().lower() for p in raw.split(',') if p.strip()])
        else:
            warnings.append(f"{rel_path}: Sin frase estricta 'Dispara con \"...\"'")

        skill_name = fm.get('name', os.path.basename(os.path.dirname(f)))
        for t in set(triggers):
            all_triggers[t].append(skill_name)

        skills_data.append({
            'name': skill_name,
            'triggers': list(set(triggers))
        })

    # 6. Detección de colisiones críticas (O_i,j > 0.60)
    for i in range(len(skills_data)):
        for j in range(i + 1, len(skills_data)):
            s1 = skills_data[i]
            s2 = skills_data[j]
            set1 = set(s1['triggers'])
            set2 = set(s2['triggers'])
            if not set1 or not set2:
                continue
            inter = set1.intersection(set2)
            if inter:
                ratio = len(inter) / min(len(set1), len(set2))
                if ratio > 0.60:
                    errors.append(f"Colisión crítica de triggers entre '{s1['name']}' y '{s2['name']}' (O_i,j = {ratio:.2f}): {inter}")

    print("\n--- DISTRIBUCIÓN DE ROLES ---")
    for r, count in role_counts.items():
        print(f"  • {r.upper():12s}: {count} habilidades")

    if warnings:
        print(f"\nAVISOS ({len(warnings)}):")
        for w in warnings[:10]:
            print("  [WARN]", w)
        if len(warnings) > 10:
            print(f"  ... y {len(warnings) - 10} más.")

    if errors:
        print(f"\n[FAIL-CLOSED] {len(errors)} ERRORES DETECTADOS:")
        for err in errors:
            print("  [ERROR]", err)
        sys.exit(1)

    print(f"\n[PASS] 100% de las {len(files)} habilidades son plenamente conformes con la Tríada Declarativa CORTEX.")
    return 0

if __name__ == '__main__':
    sys.exit(audit())
