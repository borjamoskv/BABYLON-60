import ast
from pathlib import Path
from typing import Any, Dict, List
REPO_ROOT = Path('/Users/borjafernandezangulo/30_BABYLON-60').resolve()
EXCLUDE_DIRS = {'node_modules', '.venv', '.git', '.mypy_cache', '.pytest_cache', 'forge-std', 'fable-library-js.5.8.0', 'fable-compiler', 'dist', 'target', 'build'}

def find_python_files(root: Path) -> List[Path]:
    py_files = []
    for path in root.rglob('*.py'):
        if any((part in EXCLUDE_DIRS for part in path.parts)):
            continue
        py_files.append(path)
    return sorted(py_files)

def audit_py_file(file_path: Path) -> Dict[str, Any]:
    rel_path = file_path.relative_to(REPO_ROOT)
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    lines = content.splitlines()
    issues = []
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        issues.append(f'SyntaxError at line {e.lineno}: {e.msg}')
        return {'path': str(rel_path), 'lines': len(lines), 'status': 'FAIL', 'issues': issues}
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(f"Line {node.lineno}: Bare 'except:' clause detected.")
            elif isinstance(node.type, ast.Name) and node.type.id in ('Exception', 'BaseException'):
                if 'bft' in str(rel_path) or 'ledger' in str(rel_path):
                    issues.append(f"Line {node.lineno}: Broad 'except {node.type.id}:' in BFT module (INV_C5_19 violation).")
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute) and child.func.attr in ('connect', 'execute') and isinstance(child.func.value, ast.Name) and (child.func.value.id == 'sqlite3'):
                        issues.append(f'Line {child.lineno}: Synchronous sqlite3 call inside async def {node.name} (INV_BFT_02 violation).')
    status = 'WARN' if issues else 'OK'
    return {'path': str(rel_path), 'lines': len(lines), 'status': status, 'issues': issues}

def main() -> None:
    py_files = find_python_files(REPO_ROOT)
    results = [audit_py_file(f) for f in py_files]
    total_files = len(results)
    total_lines = sum((r['lines'] for r in results))
    syntax_fails = [r for r in results if r['status'] == 'FAIL']
    warns = [r for r in results if r['issues']]
    print('=== CODEBASE DEEP REVIEW SUMMARY ===')
    print(f'Total Python Files: {total_files}')
    print(f'Total Lines of Code: {total_lines}')
    print(f'Files with Syntax Errors: {len(syntax_fails)}')
    print(f'Files with Invariant/Quality Warnings: {len(warns)}')
    print('-' * 50)
    for r in warns:
        flag = '🔴' if r['status'] == 'FAIL' else '🟡'
        print(f"{flag} {r['path']} ({r['lines']} lines)")
        for issue in r['issues']:
            print(f'   └── {issue}')
if __name__ == '__main__':
    main()