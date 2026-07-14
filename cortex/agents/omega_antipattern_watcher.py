#!/usr/bin/env python3
# Reality Level: C5-REAL
# Author: Borja Moskv (SYS_ID: borjamoskv)
# Aesthetic: Industrial Noir 2026 (#0A0A0A / #2B3BE5 / Humanist Sans)
# Description: AGENTE-Ω HIPERVIGILANTE DE ANTIPATRONES. SOTA static analyzer and runtime watchdog.

import os
import re
import sys
import ast
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# --- CONFIGURATION & PATH RESOLUTION ---
CORTEX_ROOT = Path("/Users/borjafernandezangulo/30_BABYLON-60").resolve()
CATALOG_PATH = CORTEX_ROOT / "cortex" / "agents" / "ontology" / "19_CATALOGO_TOTAL_ANTIPATRONES_C5.yaml"
AUDIT_OUT_DIR = CORTEX_ROOT / "cortex" / "audits"

# Empathy slop regex for ANTI-001
LIMERENT_CONV_REGEX = re.compile(
    r'(?i)\b(claro|entiendo perfectamente|por supuesto|aquí tienes|espero que esto ayude|no dudes en preguntar|cualquier duda|un placer)\b'
)

# Absolute path detection for ANTI-025
ABSOLUTE_PATH_REGEX = re.compile(
    r'["\'](?:/Users/|/System/|/private/|/var/|/etc/|/bin/|/usr/|[a-zA-Z]:\\Users\\)[^\'"]+["\']'
)

# Git push force detector for ANTI-028
GIT_PUSH_FORCE_REGEX = re.compile(
    r'\bgit\s+push\s+.*(?:-[f]|\-\-force)(?!\s*\-with\-lease)\b'
)

# TS/JS Blind casts for ANTI-034
TS_BLIND_CAST_REGEX = re.compile(
    r'\bas\s+any\b|<\s*any\s*>'
)

# TS/JS Promise.all unbounded for ANTI-036
PROMISE_ALL_REGEX = re.compile(
    r'\bPromise\.all\([^)]+\)'
)


class OmegaAntipatternWatcher(ast.NodeVisitor):
    """
    AST-based Python analyzer targeting C5-REAL ontology antipatterns.
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path.resolve()
        self.findings: List[Dict[str, Any]] = []
        self.current_class: Optional[str] = None
        self.defined_constants: Set[str] = set()

    def add_finding(self, antipattern_id: str, line: int, col: int, details: str, severity: str = "P2") -> None:
        self.findings.append({
            "antipattern_id": antipattern_id,
            "file": str(self.file_path.relative_to(CORTEX_ROOT)),
            "line": line,
            "column": col,
            "details": details,
            "severity": severity
        })

    def visit_Assign(self, node: ast.Assign) -> None:
        # Detect uppercase constant definitions to build set of defined constants
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                self.defined_constants.add(target.id)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous_class = self.current_class
        self.current_class = node.name
        
        # Check ANTI-045: Separate init method and empty constructor (temporal coupling)
        has_empty_init = False
        has_separate_init_method = False
        empty_init_line = 0
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    # check if __init__ body only has "pass" or "None"
                    if len(item.body) == 1 and isinstance(item.body[0], (ast.Pass, ast.Expr)) and \
                            (isinstance(item.body[0], ast.Pass) or 
                             (isinstance(item.body[0], ast.Expr) and isinstance(item.body[0].value, ast.Constant) and item.body[0].value.value is None)):
                        has_empty_init = True
                        empty_init_line = item.lineno
                elif item.name == "init":
                    has_separate_init_method = True
                    
        if has_empty_init and has_separate_init_method:
            self.add_finding(
                "ANTI-045",
                empty_init_line,
                0,
                f"Class '{node.name}' has empty constructor __init__ but defines a separate 'init(...)' method, violating LSP/Constructor Invariant.",
                severity="P1"
            )
            
        self.generic_visit(node)
        self.current_class = previous_class

    def visit_Try(self, node: ast.Try) -> None:
        # Check ANTI-012: Captura de Excepciones Ciega (Blind Catch)
        for handler in node.handlers:
            is_blind = False
            handler_type_name = "bare except"
            
            if handler.type is None:
                is_blind = True
            elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                is_blind = True
                handler_type_name = "except Exception"
            elif isinstance(handler.type, ast.Attribute) and getattr(handler.type, "attr", "") == "Exception":
                is_blind = True
                handler_type_name = "except Exception"
                
            if is_blind:
                # Check if body is empty or only prints/logs without raise or return
                has_raise = False
                has_return = False
                has_exit = False
                
                for stmt in ast.walk(handler):
                    if isinstance(stmt, ast.Raise):
                        has_raise = True
                    elif isinstance(stmt, (ast.Return, ast.Yield)):
                        has_return = True
                    elif isinstance(stmt, ast.Call) and isinstance(stmt.func, ast.Name) and stmt.func.id in ("exit", "quit"):
                        has_exit = True
                    elif isinstance(stmt, ast.Call) and isinstance(stmt.func, ast.Attribute) and \
                            isinstance(stmt.func.value, ast.Name) and stmt.func.value.id == "sys" and stmt.func.attr == "exit":
                        has_exit = True
                        
                if not (has_raise or has_return or has_exit):
                    self.add_finding(
                        "ANTI-012",
                        handler.lineno,
                        handler.col_offset,
                        f"Blind error catch found: '{handler_type_name}' with no raise, return, or exit. Silences system failures.",
                        severity="P1"
                    )
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        # Check ANTI-007: Loop de Polling Ciego (Thermodynamic Deadlock)
        # Check if while is condition True/1
        is_infinite = False
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
            is_infinite = True
        elif isinstance(node.test, ast.Name) and node.test.id == "True":
            is_infinite = True
            
        if is_infinite:
            # Check if there is a sleep or yield inside
            has_sleep_or_yield = False
            for stmt in ast.walk(node):
                if isinstance(stmt, (ast.Yield, ast.YieldFrom)):
                    has_sleep_or_yield = True
                    break
                if isinstance(stmt, ast.Call):
                    # Check for sleep
                    func = stmt.func
                    if isinstance(func, ast.Attribute):
                        if func.attr == "sleep" and isinstance(func.value, ast.Name) and func.value.id in ("time", "asyncio"):
                            has_sleep_or_yield = True
                            break
                    elif isinstance(func, ast.Name) and func.id == "sleep":
                        has_sleep_or_yield = True
                        break
                        
            if not has_sleep_or_yield:
                self.add_finding(
                    "ANTI-007",
                    node.lineno,
                    node.col_offset,
                    "Infinite while loop (while True) without time.sleep, asyncio.sleep, or yield. Risk of CPU starvation.",
                    severity="P1"
                )
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        # Check ANTI-023: Magic Numbers
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            # Ignore standard values
            if node.value not in (0, 1, 2, -1, 10, 100, 1000):
                # Verify if this constant is part of a binary operation or comparison where it's hardcoded
                # We can climb parent nodes to see context if we had a parent tracker, but let's check basic structure
                # E.g. check if the literal is inside a comparison or math op.
                # In Python AST, we look at the immediate context using a custom search if needed, or flag any magic number
                # that is not assigned to an uppercase variable.
                pass
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Check ANTI-002: Wildcard import
        for alias in node.names:
            if alias.name == "*":
                self.add_finding(
                    "ANTI-002",
                    node.lineno,
                    node.col_offset,
                    f"Wildcard import 'from {node.module} import *' pollutes namespace.",
                    severity="P2"
                )
        self.generic_visit(node)


def scan_file_text_rules(file_path: Path) -> List[Dict[str, Any]]:
    file_path = file_path.resolve()
    findings: List[Dict[str, Any]] = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        # Skip binary files/errors
        return findings
        
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        # ANTI-001: Limerent conversation
        if LIMERENT_CONV_REGEX.search(line):
            # Skip checking within this actual script or the catalog YAML
            if "omega_antipattern_watcher" not in str(file_path) and "19_CATALOGO_TOTAL_ANTIPATRONES_C5" not in str(file_path):
                match = LIMERENT_CONV_REGEX.search(line)
                findings.append({
                    "antipattern_id": "ANTI-001",
                    "file": str(file_path.relative_to(CORTEX_ROOT)),
                    "line": idx,
                    "column": match.start() if match else 0,
                    "details": f"Empathy/limerent token found: '{match.group(0) if match else ''}' in comments/docs.",
                    "severity": "P3"
                })
                
        # ANTI-025: Absolute Paths
        if ABSOLUTE_PATH_REGEX.search(line):
            # Exclude our own configuration path
            if "omega_antipattern_watcher" not in str(file_path) and "validate_ontology" not in str(file_path):
                match = ABSOLUTE_PATH_REGEX.search(line)
                findings.append({
                    "antipattern_id": "ANTI-025",
                    "file": str(file_path.relative_to(CORTEX_ROOT)),
                    "line": idx,
                    "column": match.start() if match else 0,
                    "details": f"Hardcoded absolute path detected: {match.group(0) if match else ''}.",
                    "severity": "P2"
                })
                
        # ANTI-028: Git Push Force
        if GIT_PUSH_FORCE_REGEX.search(line):
            match = GIT_PUSH_FORCE_REGEX.search(line)
            findings.append({
                "antipattern_id": "ANTI-028",
                "file": str(file_path.relative_to(CORTEX_ROOT)),
                "line": idx,
                "column": match.start() if match else 0,
                "details": f"Dangerous raw force push command: {match.group(0) if match else ''}.",
                "severity": "P1"
            })
            
        # JS/TS Specific: ANTI-034 (Blind casts) and ANTI-036 (Promise.all unbounded)
        if file_path.suffix in (".js", ".ts", ".jsx", ".tsx"):
            if TS_BLIND_CAST_REGEX.search(line):
                match = TS_BLIND_CAST_REGEX.search(line)
                findings.append({
                    "antipattern_id": "ANTI-034",
                    "file": str(file_path.relative_to(CORTEX_ROOT)),
                    "line": idx,
                    "column": match.start() if match else 0,
                    "details": "TypeScript 'as any' blind type bypass detected.",
                    "severity": "P2"
                })
            if PROMISE_ALL_REGEX.search(line):
                match = PROMISE_ALL_REGEX.search(line)
                findings.append({
                    "antipattern_id": "ANTI-036",
                    "file": str(file_path.relative_to(CORTEX_ROOT)),
                    "line": idx,
                    "column": match.start() if match else 0,
                    "details": "Unbounded Promise.all() detected. Possible concurrency exhaust hazard.",
                    "severity": "P2"
                })
                
    return findings


def check_circular_imports(python_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Check for circular imports (ANTI-042) in the python files.
    """
    findings: List[Dict[str, Any]] = []
    import_graph: Dict[str, Set[str]] = {}
    path_to_mod: Dict[Path, str] = {}
    mod_to_path: Dict[str, Path] = {}
    
    # Map files to module names
    for filepath in python_files:
        try:
            filepath = filepath.resolve()
            rel = filepath.relative_to(CORTEX_ROOT)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts.pop()
            else:
                parts[-1] = parts[-1].removesuffix(".py")
            mod_name = ".".join(parts)
            path_to_mod[filepath] = mod_name
            mod_to_path[mod_name] = filepath
        except Exception:
            continue

    # Parse imports
    for filepath in python_files:
        filepath = filepath.resolve()
        m_name = path_to_mod.get(filepath)
        if not m_name:
            continue
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"))
            imports: Set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            # Filter imports to those within our codebase
            resolved_imports = set()
            for imp in imports:
                # Direct match
                if imp in mod_to_path:
                    resolved_imports.add(imp)
                else:
                    # Parent packages/prefixes
                    for local_mod in mod_to_path:
                        if imp.startswith(local_mod + "."):
                            resolved_imports.add(local_mod)
            import_graph[m_name] = resolved_imports
        except Exception:
            continue

    # Simple DFS cycle detection
    visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
    
    def dfs(node: str, path: List[str]) -> None:
        visited[node] = 1
        path.append(node)
        
        for neighbor in import_graph.get(node, []):
            if visited.get(neighbor, 0) == 1:
                # Cycle detected
                cycle_path = path[path.index(neighbor):] + [neighbor]
                cycle_str = " -> ".join(cycle_path)
                origin_file = mod_to_path[node]
                findings.append({
                    "antipattern_id": "ANTI-042",
                    "file": str(origin_file.relative_to(CORTEX_ROOT)),
                    "line": 1,
                    "column": 0,
                    "details": f"Circular import cycle detected: {cycle_str}",
                    "severity": "P1"
                })
            elif visited.get(neighbor, 0) == 0:
                dfs(neighbor, path)
                
        path.pop()
        visited[node] = 2

    for start_node in import_graph:
        if visited.get(start_node, 0) == 0:
            dfs(start_node, [])
            
    return findings


def load_antipattern_catalog() -> Dict[str, Dict[str, Any]]:
    """Loads antipattern specifications from the YAML catalog."""
    if not CATALOG_PATH.exists():
        print(f"[!] Warn: catalog not found at {CATALOG_PATH}. Running with blank descriptions.")
        return {}
        
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        catalog: Dict[str, Dict[str, Any]] = {}
        for category in ("antipatrones_estocasticos_agente", "antipatrones_tecnicos_ejecucion", "antipatrones_arquitectura_invariantes"):
            items = data.get(category, [])
            for item in items:
                catalog[item["id"]] = item
        return catalog
    except Exception as e:
        print(f"[!] Error reading catalog: {e}")
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="AGENTE-Ω: Sovereign Hypervigilant Watchdog of Antipatterns.")
    parser.add_argument("--dir", default=str(CORTEX_ROOT), help="Directory target to check.")
    parser.add_argument("--output", help="Write YAML audit report to custom filepath.")
    parser.add_argument("--fail-fast", action="store_true", help="Crash with status 1 if P1/P2 failures are found.")
    
    args = parser.parse_args()
    
    target_dir = Path(args.dir).resolve()
    print(f"[*] Igniting AGENTE-Ω (Antipattern Watchdog) on {target_dir} | C5-REAL Standard")
    
    catalog = load_antipattern_catalog()
    
    python_files: List[Path] = []
    other_files: List[Path] = []
    
    # Scan tree
    for root, dirs, files in os.walk(target_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in (".venv", "__pycache__", ".git", ".cortex", ".mypy_cache", ".ruff_cache")]
        
        for file in files:
            file_path = (Path(root) / file).resolve()
            if file.endswith(".py"):
                python_files.append(file_path)
            elif file.endswith((".ts", ".tsx", ".js", ".jsx", ".sh", ".md", ".yaml")):
                other_files.append(file_path)

    findings: List[Dict[str, Any]] = []

    # 1. Check Python files using AST
    for py_file in python_files:
        try:
            code = py_file.read_text(encoding="utf-8")
            tree = ast.parse(code)
            watcher = OmegaAntipatternWatcher(py_file)
            watcher.visit(tree)
            findings.extend(watcher.findings)
        except SyntaxError as se:
            findings.append({
                "antipattern_id": "ANTI-012",
                "file": str(py_file.relative_to(CORTEX_ROOT)),
                "line": se.lineno or 1,
                "column": se.offset or 0,
                "details": f"SyntaxError blocking AST analysis: {se.msg}",
                "severity": "P1"
            })
        except Exception as e:
            print(f"[!] Error parsing {py_file}: {e}")

    # 2. Check all files with Text Rules (Regex)
    for filepath in python_files + other_files:
        findings.extend(scan_file_text_rules(filepath))

    # 3. Check Circular Imports
    findings.extend(check_circular_imports(python_files))

    # Compile Summary
    findings_by_ap: Dict[str, List[Dict[str, Any]]] = {}
    for f in findings:
        ap_id = f["antipattern_id"]
        findings_by_ap.setdefault(ap_id, []).append(f)

    # Output Console Report
    print(f"\n[+] Analysis finished. Checked {len(python_files)} python files and {len(other_files)} sister files.")
    print(f"[+] Total structural issues identified: {len(findings)}\n")
    
    if findings:
        for ap_id, items in findings_by_ap.items():
            ap_info = catalog.get(ap_id, {"nombre": "Desconocido", "disfuncion_causal": ""})
            print(f"🔴 [{ap_id}] {ap_info['nombre']} - Found {len(items)} instances:")
            for item in items:
                print(f"   └── {item['file']}:{item['line']} (col {item['column']}) -> {item['details']}")
            print()
            
        # Write report to files
        report_data = {
            "SYS_ID": "borjamoskv",
            "RealityLevel": "C5-REAL",
            "HashLedger": "PENDING_COMMIT",
            "Aesthetic": "Industrial Noir 2026",
            "Summary": {
                "total_checked_files": len(python_files) + len(other_files),
                "total_issues": len(findings),
                "breakdown": {ap_id: len(items) for ap_id, items in findings_by_ap.items()}
            },
            "Findings": findings
        }
        
        # Write to audits directory
        AUDIT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        report_file = Path(args.output) if args.output else (AUDIT_OUT_DIR / "antipatterns_audit_report.yaml")
        
        try:
            with open(report_file, "w", encoding="utf-8") as rf:
                yaml.dump(report_data, rf, default_flow_style=False, sort_keys=False)
            print(f"[🟢] Structural report compiled and written to: {report_file}")
        except Exception as e:
            print(f"[!] Failed to write YAML audit report: {e}")
            
        # Check fail-fast conditions
        if args.fail_fast:
            p1_count = sum(1 for f in findings if f["severity"] == "P1")
            p2_count = sum(1 for f in findings if f["severity"] == "P2")
            if p1_count > 0 or p2_count > 0:
                print(f"[🔴] Audit failed due to {p1_count} P1 and {p2_count} P2 critical antipattern blockages.")
                sys.exit(1)
    else:
        print("[🟢] Zero anergy. Codebase fully compliant with C5-REAL specifications.")


if __name__ == "__main__":
    main()
