#!/usr/bin/env python3
# Mode: C5-REAL
"""
Sovereign Python AST Extector.
Extracts classes, methods, docstrings, decorators, and critical trust-infrastructure pathways.
"""

import os
import sys
import json
import ast
import logging

class SovereignPythonExtractorSkill:
    def __init__(self):
        self.name = "sovereign-python-extractor"
        self.description = "AST extraction."
        self.instructions = (
            "[C5-REAL]\n"
            "Usage: python scripts/sovereign_python_extractor.py <file> [--json] [--audit]\n"
        )

    def get_system_prompt(self):
        return self.instructions

    def execute(self, payload: dict) -> dict:
        logging.info(f"[{self.name}] Executing logic...")
        filepath = payload.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return {"status": "error", "message": "File not found"}
        
        result = analyze_file(filepath)
        return {
            "status": "success",
            "skill": self.name,
            "yield_impact": "O(1) AST Extraction",
            "extracted_payload": result
        }


def get_decorator_name(decorator_node) -> str:
    """Recursively reconstructs decorator names (e.g. @pytest.mark.asyncio)."""
    if isinstance(decorator_node, ast.Name):
        return decorator_node.id
    elif isinstance(decorator_node, ast.Attribute):
        return f"{get_decorator_name(decorator_node.value)}.{decorator_node.attr}"
    elif isinstance(decorator_node, ast.Call):
        return get_decorator_name(decorator_node.func)
    return "unknown"


def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
            lines = code.splitlines()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error in target file: {e}"}

    classes = []
    functions = []
    critical_paths = []
    sovereign_markers = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls_doc = ast.get_docstring(node)
            methods = []
            decorators = [get_decorator_name(d) for d in node.decorator_list]
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(f"{getattr(b.value, 'id', 'unknown')}.{b.attr}")

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = ast.get_docstring(item)
                    args = [a.arg for a in item.args.args]
                    method_decorators = [get_decorator_name(d) for d in item.decorator_list]
                    methods.append({
                        "name": item.name,
                        "docstring": method_doc,
                        "args": args,
                        "decorators": method_decorators,
                        "line": item.lineno,
                        "is_async": isinstance(item, ast.AsyncFunctionDef)
                    })
            classes.append({
                "name": node.name,
                "docstring": cls_doc,
                "bases": bases,
                "decorators": decorators,
                "methods": methods,
                "line": node.lineno
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node)
            args = [a.arg for a in node.args.args]
            decorators = [get_decorator_name(d) for d in node.decorator_list]
            functions.append({
                "name": node.name,
                "docstring": func_doc,
                "args": args,
                "decorators": decorators,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            })

    critical_keywords = {"ledger", "guard", "commit", "verify", "sign", "encrypt", "decrypt", "hash"}
    sovereign_keywords = {"c5-real", "c4-sim", "singularity", "sovereign", "exergy", "centinela", "moskv", "cortex"}

    for subnode in ast.walk(tree):
        if isinstance(subnode, ast.Name):
            name_lower = subnode.id.lower()
            if any(k in name_lower for k in critical_keywords):
                line_no = getattr(subnode, "lineno", None)
                line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                critical_paths.append({
                    "type": "identifier",
                    "name": subnode.id,
                    "line": line_no,
                    "context": line_content
                })
            if any(s in name_lower for s in sovereign_keywords):
                line_no = getattr(subnode, "lineno", None)
                line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                sovereign_markers.append({
                    "type": "identifier",
                    "name": subnode.id,
                    "line": line_no,
                    "context": line_content
                })

        elif isinstance(subnode, ast.Attribute):
            attr_lower = subnode.attr.lower()
            if any(k in attr_lower for k in critical_keywords):
                line_no = getattr(subnode, "lineno", None)
                line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                critical_paths.append({
                    "type": "attribute",
                    "name": subnode.attr,
                    "line": line_no,
                    "context": line_content
                })
            if any(s in attr_lower for s in sovereign_keywords):
                line_no = getattr(subnode, "lineno", None)
                line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                sovereign_markers.append({
                    "type": "attribute",
                    "name": subnode.attr,
                    "line": line_no,
                    "context": line_content
                })

        elif isinstance(subnode, ast.Await):
            line_no = getattr(subnode, "lineno", None)
            line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
            critical_paths.append({
                "type": "await",
                "name": "await",
                "line": line_no,
                "context": line_content
            })

        elif isinstance(subnode, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in subnode.names]
            module = getattr(subnode, "module", "") or ""
            full_names = [f"{module}.{n}" if module else n for n in names]
            for fn in full_names:
                fn_lower = fn.lower()
                if any(s in fn_lower for s in {"cortex", "omega", "solidity", "web3", "eth", "cryptography", "crypto", "blockchain"}):
                    line_no = getattr(subnode, "lineno", None)
                    line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                    sovereign_markers.append({
                        "type": "import",
                        "name": fn,
                        "line": line_no,
                        "context": line_content
                    })

        elif isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
            val_lower = subnode.value.lower()
            if any(s in val_lower for s in sovereign_keywords):
                line_no = getattr(subnode, "lineno", None)
                line_content = lines[line_no - 1].strip() if line_no and 1 <= line_no <= len(lines) else ""
                sovereign_markers.append({
                    "type": "string_constant",
                    "value": subnode.value[:50] + "..." if len(subnode.value) > 50 else subnode.value,
                    "line": line_no,
                    "context": line_content
                })

    dedup_crit = []
    seen_crit = set()
    for cp in critical_paths:
        key = (cp["line"], cp["name"], cp["type"])
        if key not in seen_crit:
            seen_crit.add(key)
            dedup_crit.append(cp)

    dedup_sov = []
    seen_sov = set()
    for sm in sovereign_markers:
        key = (sm["line"], sm.get("name") or sm.get("value"), sm["type"])
        if key not in seen_sov:
            seen_sov.add(key)
            dedup_sov.append(sm)

    dedup_crit.sort(key=lambda x: x["line"] if x["line"] is not None else 0)
    dedup_sov.sort(key=lambda x: x["line"] if x["line"] is not None else 0)

    return {
        "classes": classes,
        "functions": functions,
        "critical_paths": dedup_crit,
        "sovereign_markers": dedup_sov
    }


def print_report(filepath, result, audit_only=False):
    print("\033[1;30m======================================================================\033[0m")
    print("\033[1;34m⚡ SOVEREIGN CORTEX STRUCTURAL REPORT \u2014 AST DETECTOR v8.3.0\033[0m")
    print(f"\033[1;30mTarget File: {filepath}\033[0m")
    print("\033[1;30m======================================================================\033[0m")
    
    if "error" in result:
        print(f"\033[1;31m[-] ANALYSIS FAILED: {result['error']}\033[0m")
        return

    print("[*] Summary Stats:")
    print(f"    - Classes: {len(result['classes'])}")
    print(f"    - Global Functions: {len(result['functions'])}")
    print(f"    - Critical Paths: {len(result['critical_paths'])}")
    print(f"    - Sovereign Markers: {len(result['sovereign_markers'])}")
    print("")

    if not audit_only:
        print("\033[1;36m[Classes]\033[0m")
        if not result["classes"]:
            print("    None detected.")
        for cls in result["classes"]:
            doc_snippet = f" | \"{cls['docstring'].strip().splitlines()[0][:60]}\"" if cls["docstring"] else ""
            bases_str = f"({', '.join(cls['bases'])})" if cls["bases"] else ""
            dec_str = " ".join([f"@{d}" for d in cls["decorators"]]) + " " if cls["decorators"] else ""
            print(f"  • {dec_str}\033[1;37mclass {cls['name']}\033[0m{bases_str} (Line {cls['line']}){doc_snippet}")
            for method in cls["methods"]:
                async_tag = "\033[1;35masync \033[0m" if method["is_async"] else ""
                args_str = ", ".join(method["args"])
                method_dec = " ".join([f"@{d}" for d in method["decorators"]]) + " " if method["decorators"] else ""
                print(f"    └─ {method_dec}{async_tag}def {method['name']}({args_str}) (Line {method['line']})")
        print("")

        print("\033[1;36m[Global Functions]\033[0m")
        if not result["functions"]:
            print("    None detected.")
        for func in result["functions"]:
            async_tag = "\033[1;35masync \033[0m" if func["is_async"] else ""
            args_str = ", ".join(func["args"])
            func_dec = " ".join([f"@{d}" for d in func["decorators"]]) + " " if func["decorators"] else ""
            print(f"  • {func_dec}{async_tag}def {func['name']}({args_str}) (Line {func['line']})")
        print("")

    print("\033[1;33m[Critical Paths (ledger, guards, crypto, async)]\033[0m")
    if not result["critical_paths"]:
        print("    None detected.")
    for cp in result["critical_paths"]:
        print(f"  [{cp['line'] or '?'}] \033[1;37m{cp['type']}\033[0m: '{cp['name']}' -> \033[0;32m{cp['context']}\033[0m")
    print("")

    print("\033[1;32m[Sovereign Markers (trust infrastructure, invariants)]\033[0m")
    if not result["sovereign_markers"]:
        print("    None detected.")
    for sm in result["sovereign_markers"]:
        print(f"  [{sm['line'] or '?'}] \033[1;37m{sm['type']}\033[0m: '{sm.get('name') or sm.get('value')}' -> \033[0;32m{sm['context']}\033[0m")
    print("\033[1;30m======================================================================\033[0m")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sovereign_python_extractor.py <file_path> [--json] [--audit]")
        sys.exit(1)

    filepath = sys.argv[1]
    
    use_json = "--json" in sys.argv
    use_audit = "--audit" in sys.argv

    if not os.path.exists(filepath):
        if use_json:
            print(json.dumps({"error": f"File not found: {filepath}"}))
        else:
            print(f"[-] Error: File not found: {filepath}")
        sys.exit(1)

    result = analyze_file(filepath)

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print_report(filepath, result, audit_only=use_audit)


if __name__ == "__main__":
    main()
