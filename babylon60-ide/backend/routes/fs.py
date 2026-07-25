from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/fs", tags=["fs"])

class WriteRequest(BaseModel):
    path: str = Field(..., description="Relative path from project root")
    content: str = Field(..., description="File content to write")

def _get_project_root() -> Path:
    # babylon60-ide/backend/routes/fs.py -> root is 4 levels up
    return Path(__file__).resolve().parent.parent.parent.parent

@router.get("/tree")
def get_tree() -> dict[str, Any]:
    root = _get_project_root()
    
    def build_tree(dir_path: Path) -> list[dict[str, Any]]:
        tree = []
        try:
            for entry in sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith('.') or entry.name in ('__pycache__', 'node_modules', 'target', '.venv'):
                    continue
                node = {
                    "name": entry.name,
                    "path": str(Path(entry.path).relative_to(root)),
                    "is_dir": entry.is_dir()
                }
                if entry.is_dir():
                    node["children"] = build_tree(Path(entry.path))
                tree.append(node)
        except PermissionError:
            pass
        return tree

    return {"name": root.name, "path": ".", "is_dir": True, "children": build_tree(root)}

@router.get("/read")
def read_file(path: str) -> dict[str, str]:
    root = _get_project_root()
    target = (root / path).resolve()
    
    # Security: prevent path traversal out of root
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=403, detail="Path traversal detected")
        
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        content = target.read_text(encoding="utf-8")
        return {"content": content}
    except UnicodeDecodeError as err:
        raise HTTPException(status_code=400, detail="Cannot read binary file as text") from err

@router.post("/write")
def write_file(req: WriteRequest) -> dict[str, str]:
    root = _get_project_root()
    target = (root / req.path).resolve()
    
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=403, detail="Path traversal detected")
        
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    
    return {"status": "ok", "path": req.path}
