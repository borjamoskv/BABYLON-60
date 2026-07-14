"""
Objectives & Milestones Agent (ULTRAThink ITERA)
Author: Borja Moskv (borjamoskv)
C5-REAL Execution Kernel
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

def run_git_sentinel(file_path: Path, message: str) -> str:
    """Executes atomic Git Sentinel commit."""
    try:
        subprocess.run(["git", "add", str(file_path)], check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True, text=True)
        hash_result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], check=True, capture_output=True, text=True)
        return hash_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git Sentinel failed: {e.stderr}")
        sys.exit(1)

def parse_project_md(content: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Parses PROJECT.md to extract milestones and objectives."""
    lines = content.split('\n')
    data = []
    
    header_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("| ID | Type | Title"):
            header_idx = i
            break
            
    if header_idx == -1:
        print("Error: Milestones table not found.")
        sys.exit(1)
        
    for i in range(header_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line or not line.startswith("|"):
            break
            
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 5:
            data.append({
                "id": parts[0],
                "type": parts[1],
                "title": parts[2],
                "desc_due": parts[3],
                "status": parts[4],
                "info": parts[5] if len(parts) > 5 else "",
                "line_idx": i
            })
            
    return lines, data

def calculate_exergy(data: List[Dict[str, Any]]) -> None:
    """Calculates exergy for objectives based on milestones."""
    obj_milestones: Dict[str, List[Dict[str, Any]]] = {}
    current_obj = None
    
    for row in data:
        if row["type"] == "Objective":
            current_obj = row["id"]
            obj_milestones[current_obj] = []
        elif row["type"] == "Milestone" and current_obj:
            obj_milestones[current_obj].append(row)
            
    for obj_id, milestones in obj_milestones.items():
        if not milestones:
            continue
            
        total = len(milestones)
        completed = sum(1 for m in milestones if m["status"] == "DONE")
        
        exergy = completed / total if total > 0 else 0.0
        
        for row in data:
            if row["id"] == obj_id:
                if completed == total:
                    row["status"] = "DONE"
                elif completed > 0:
                    row["status"] = "IN_PROGRESS"
                row["info"] = f"Exergy: {exergy:.2f}"

def format_row(row: Dict[str, Any]) -> str:
    return f"| {row['id']} | {row['type']} | {row['title']} | {row['desc_due']} | {row['status']} | {row['info']} |"

def main() -> None:
    project_path = Path(__file__).resolve().parent.parent / "PROJECT.md"
    if not project_path.exists():
        print("Error: PROJECT.md not found.")
        sys.exit(1)
        
    content = project_path.read_text(encoding="utf-8")
    lines, data = parse_project_md(content)
    
    # Mark OBJ-006 and MS-007 as DONE
    for row in data:
        if row["id"] in ("OBJ-006", "MS-007"):
            row["status"] = "DONE"
            if row["id"] == "MS-007":
                row["info"] = "Hash: TBD"
                
    calculate_exergy(data)
    
    for row in data:
        lines[row["line_idx"]] = format_row(row)
        
    new_content = '\n'.join(lines)
    
    if new_content != content:
        project_path.write_text(new_content, encoding="utf-8")
        commit_hash = run_git_sentinel(project_path, "docs(project): resolve OBJ-006 and MS-007 [C5-REAL]")
        
        content = project_path.read_text(encoding="utf-8")
        lines, data = parse_project_md(content)
        for row in data:
            if row["id"] == "MS-007":
                row["info"] = f"Hash: {commit_hash}"
                lines[row["line_idx"]] = format_row(row)
                
        project_path.write_text('\n'.join(lines), encoding="utf-8")
        run_git_sentinel(project_path, "docs(project): inject hash for MS-007 [C5-REAL]")
        print(f"[STATUS_OK / EXERGY] C5-REAL mutation completed. Hash: {commit_hash}")
    else:
        print("[STATUS_OK / EXERGY] Idempotency declared. No mutations.")

if __name__ == "__main__":
    main()
