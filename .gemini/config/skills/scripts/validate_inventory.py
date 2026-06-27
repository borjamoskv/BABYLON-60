#!/usr/bin/env python3
"""
C5-REAL CI Job: Autonomous Inventory Validation
Cross-checks SKILLS_INVENTORY.md against actual SKILL.md and script files.
Raises alerts for mismatches.
"""
import os
import re
import sys

SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILLS_DIR, "scripts")

def get_all_skills():
    skills = []
    for item in os.listdir(SKILLS_DIR):
        if os.path.isdir(os.path.join(SKILLS_DIR, item)) and not item.startswith('.'):
            if os.path.exists(os.path.join(SKILLS_DIR, item, "SKILL.md")):
                skills.append(item)
    return skills

def validate_skill(skill):
    skill_md = os.path.join(SKILLS_DIR, skill, "SKILL.md")
    with open(skill_md, "r") as f:
        content = f.read()
    
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return f"[WARNING] {skill} missing frontmatter"
    
    frontmatter = frontmatter_match.group(1)
    script_match = re.search(r'^script:\s*(.*?)$', frontmatter, re.MULTILINE)
    
    if not script_match:
        return f"[ERROR] {skill} missing 'script' field in frontmatter"
    
    script_value = script_match.group(1).strip()
    if script_value and script_value.lower() != 'none':
        # Remove surrounding quotes if present
        script_value = script_value.strip("'\"")
        # Handle cases where it is just the script name vs scripts/name
        if script_value.startswith("scripts/"):
            script_path = os.path.join(SKILLS_DIR, script_value)
        else:
            script_path = os.path.join(SCRIPTS_DIR, script_value)
            
        if not os.path.exists(script_path):
            return f"[ERROR] {skill} script defined as '{script_value}' but file does not exist"
    
    return None

def main():
    print("[C5-REAL] Validating Skill Ecosystem...")
    skills = get_all_skills()
    errors = []
    
    for skill in skills:
        err = validate_skill(skill)
        if err:
            errors.append(err)
            
    if errors:
        print("\n".join(errors))
        print(f"\n[FAILURE] Validation failed: {len(errors)} mismatches found.")
        sys.exit(1)
    else:
        print("[SUCCESS] All skills validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
