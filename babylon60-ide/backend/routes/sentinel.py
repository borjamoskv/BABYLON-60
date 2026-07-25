from __future__ import annotations
import re
import subprocess
from pathlib import Path
from typing import Any
from fastapi import APIRouter
router = APIRouter(prefix='/api/sentinel', tags=['sentinel'])
CANONICAL_REPO_NAME = 'Teorema-Robinson-Moskv'
CANONICAL_BRANCH = 'main'
DEAD_FORK_MARKER = 'BABYLON-60'

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent

def _git(root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(['git', *args], cwd=str(root), capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()
_CRED_RE = re.compile('(://)([^/@\\s]+)@')

def _redact_url(url: str) -> str:
    return _CRED_RE.sub('\\1***@', url)

@router.get('/status')
def sentinel_status() -> dict[str, Any]:
    root = _get_project_root()
    repo_name = root.name
    is_git = (root / '.git').exists()
    branch = _git(root, 'rev-parse', '--abbrev-ref', 'HEAD') if is_git else None
    head = head_subject = head_time = None
    if is_git:
        head_meta = _git(root, 'log', '-1', '--pretty=%h%x1f%s%x1f%cI')
        if head_meta:
            parts = head_meta.split('\x1f')
            if len(parts) == 3:
                head, head_subject, head_time = parts
    commit_count_raw = _git(root, 'rev-list', '--count', 'HEAD') if is_git else None
    porcelain = _git(root, 'status', '--porcelain') if is_git else None
    dirty_files = len([ln for ln in porcelain.splitlines() if ln.strip()]) if porcelain else 0
    remotes: list[dict[str, str]] = []
    remotes_raw = _git(root, 'remote', '-v') if is_git else None
    if remotes_raw:
        seen: set[str] = set()
        for line in remotes_raw.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in seen:
                seen.add(parts[0])
                remotes.append({'name': parts[0], 'url': _redact_url(parts[1])})
    warnings: list[dict[str, str]] = []
    if not is_git:
        warnings.append({'level': 'red', 'msg': f"'{repo_name}' no es un repo git — sin Git Sentinel no hay ledger de mutaciones."})
    if repo_name != CANONICAL_REPO_NAME:
        warnings.append({'level': 'red', 'msg': f"REPO INCORRECTO: estás en '{repo_name}', el linaje canónico es '{CANONICAL_REPO_NAME}'."})
    if branch and branch != CANONICAL_BRANCH:
        warnings.append({'level': 'amber', 'msg': f"Rama '{branch}' ≠ '{CANONICAL_BRANCH}' (canónica). Verifica antes de mutar."})
    marker = DEAD_FORK_MARKER.lower()
    for r in remotes:
        if marker in r['url'].lower():
            warnings.append({'level': 'red', 'msg': f"Remoto '{r['name']}' apunta al fork muerto {DEAD_FORK_MARKER} (historia no relacionada, claves expuestas). Linaje NO canónico."})
    if remotes and (not any((marker in r['url'].lower() for r in remotes))):
        warnings.append({'level': 'amber', 'msg': 'Hay remoto configurado. P0 (STATUS.md) exige linaje local sin remoto hasta rotar claves.'})
    warnings.sort(key=lambda w: 0 if w['level'] == 'red' else 1)
    return {'repo_root': str(root), 'repo_name': repo_name, 'is_git': is_git, 'branch': branch, 'head': head, 'head_subject': head_subject, 'head_time': head_time, 'commit_count': int(commit_count_raw) if commit_count_raw and commit_count_raw.isdigit() else None, 'dirty_files': dirty_files, 'remotes': remotes, 'canonical': {'repo_name': CANONICAL_REPO_NAME, 'branch': CANONICAL_BRANCH, 'remote_policy': 'none-until-P0-resolved'}, 'warnings': warnings}