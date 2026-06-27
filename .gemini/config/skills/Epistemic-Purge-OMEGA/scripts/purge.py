import ast
import re
import sys
import logging
from pathlib import Path
from typing import List, Set, Tuple

# █ SYS_ID: EPISTEMIC_PURGE_ENGINE
# █ STATE: C5-REAL | BABYLON-60 CORE

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("EpistemicPurge")

GREEN_THEATER_PATTERNS = [
    re.compile(r"(?i)espero que (esto|te) (sea útil|ayude)"),
    re.compile(r"(?i)aquí tienes el código"),
    re.compile(r"(?i)lo siento,"),
    re.compile(r"(?i)mis disculpas"),
    re.compile(r"(?i)como modelo de (lenguaje|IA)"),
    re.compile(r"(?i)es importante (recordar|notar|tener en cuenta) que"),
    re.compile(r"(?i)por favor ten en cuenta"),
]

def analyze_ast_for_limerence(filepath: Path) -> List[Tuple[int, str]]:
    """
    Escanea docstrings y comentarios en busca de anergía y prosa estocástica.
    """
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        
        # Check module docstring
        if ast.get_docstring(tree):
            for pattern in GREEN_THEATER_PATTERNS:
                if pattern.search(ast.get_docstring(tree)):
                    violations.append((1, "Green Theater detected in module docstring"))

        # Check classes and functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc:
                    for pattern in GREEN_THEATER_PATTERNS:
                        if pattern.search(doc):
                            violations.append((node.lineno, f"Anergy in docstring of {node.name}"))
                            
    except SyntaxError:
        logger.error(f"[!] AST Parse Error: {filepath.name}")
    except Exception as e:
        logger.error(f"[!] Epistemic Failure in {filepath.name}: {e}")

    return violations

def enforce_zero_anergy(target_dir: str):
    """
    Aplica el principio de Landauer: elimina ruido, conserva estado inmutable.
    """
    path = Path(target_dir)
    if not path.exists():
        logger.error("Target path does not exist. Thermodynamic vacuum.")
        sys.exit(1)

    total_violations = 0
    for py_file in path.rglob("*.py"):
        if "venv" in py_file.parts or ".tox" in py_file.parts:
            continue
            
        faults = analyze_ast_for_limerence(py_file)
        if faults:
            logger.warning(f"-> [TAINTED] {py_file.name}")
            for line, issue in faults:
                logger.warning(f"   L{line}: {issue}")
                total_violations += 1

    if total_violations > 0:
        logger.error(f"\n[ABORT] {total_violations} instancias de Green Theater detectadas. SAGA-1 Iniciado.")
        sys.exit(1)
    else:
        logger.info("\n[C5-REAL] Estructura cristalizada. Cero anergía detectada.")
        sys.exit(0)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    enforce_zero_anergy(target)
