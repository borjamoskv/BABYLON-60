# [C5-REAL] Exergy-Maximized
"""
Macrófago Ontológico (OP_OUROBOROS_INIT)
Aserción Termodinámica y Purga de Entropía Estocástica para BABYLON-60.
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Límite físico C5-REAL
MAX_LOC = 25000
MAX_FUNCTION_LINES = 100


@dataclass
class EntropyViolation:
    file_path: str
    line_number: int
    violation_type: str
    description: str


@dataclass
class ThermodynamicReport:
    total_files_scanned: int = 0
    total_loc: int = 0
    violations: list[EntropyViolation] = field(default_factory=list)

    @property
    def is_compromised(self) -> bool:
        return len(self.violations) > 0 or self.total_loc > MAX_LOC


class ASTMacrophage(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations: list[EntropyViolation] = []
        self.source_lines = []

    def load_source(self, path: Path):
        try:
            with open(path, encoding="utf-8") as f:
                self.source_lines = f.readlines()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error cargando lineas de {path}: {e}")

    def _check_function_length(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, label: str
    ) -> None:
        if hasattr(node, "end_lineno") and node.end_lineno:
            length = node.end_lineno - node.lineno
            if length > MAX_FUNCTION_LINES:
                self.violations.append(
                    EntropyViolation(
                        self.file_path,
                        node.lineno,
                        "INV_REDUCE_LINES",
                        f"{label} '{node.name}' excede {MAX_FUNCTION_LINES} líneas ({length}).",
                    )
                )

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_function_length(node, "Función")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_function_length(node, "Función asíncrona")
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Detect 'except Exception: pass'
        if isinstance(node.type, ast.Name) and node.type.id == "Exception":
            has_raise = any(isinstance(stmt, ast.Raise) for stmt in ast.walk(node))
            has_log = any(
                isinstance(stmt, ast.Call)
                and isinstance(stmt.func, ast.Attribute)
                and getattr(stmt.func.value, "id", "") in ("logger", "log", "logging")
                for stmt in ast.walk(node)
            )
            if not has_raise and not has_log:
                self.violations.append(
                    EntropyViolation(
                        self.file_path,
                        node.lineno,
                        "AP-04 (Silent Swallow)",
                        "Bloque 'except Exception' vacío o sin logger/raise.",
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.violations.append(
                EntropyViolation(
                    self.file_path,
                    node.lineno,
                    "AP-07 (Naked Print)",
                    "Uso de print() detectado. Reemplazar por logger.",
                )
            )
        elif isinstance(node.func, ast.Attribute) and getattr(node.func, "attr", "") == "sleep":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
                # Only a violation if we're inside an async loop (hard to perfectly detect here, but time.sleep is suspicious)
                self.violations.append(
                    EntropyViolation(
                        self.file_path,
                        node.lineno,
                        "AP-02 (Sync Sleep Lock)",
                        "Uso de time.sleep() detectado. Potencial bloqueo síncrono.",
                    )
                )
        self.generic_visit(node)


class OntologicalMacrophage:
    """Motor central de auditoría estructural y termodinámica."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def scan(self) -> ThermodynamicReport:
        report = ThermodynamicReport()

        for py_file in self.root_dir.rglob("*.py"):
            # Omitir entornos virtuales o basura local
            if ".venv" in py_file.parts or "node_modules" in py_file.parts:
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()
                report.total_loc += len(lines)
                report.total_files_scanned += 1

                tree = ast.parse(content, filename=str(py_file))
                visitor = ASTMacrophage(str(py_file.relative_to(self.root_dir)))
                visitor.load_source(py_file)
                visitor.visit(tree)

                report.violations.extend(visitor.violations)

            except Exception as e:  # noqa: BLE001
                logger.warning(f"Error parseando {py_file}: {e}")

        return report

    def annihilate(self, report: ThermodynamicReport):
        """Ejecuta purga OP_ANNIHILATE si se requiere (dry-run o destrucción controlada)."""
        if report.is_compromised:
            # En modo C5-REAL estricto, esto mataría el proceso o bloquearía el hook.
            # Por ahora, levantamos RuntimeError para anclarnos causalmente al fallo.
            raise RuntimeError(
                f"[OP_OOM_SIM] Entropía Detectada: {len(report.violations)} violaciones estructurales. "
                f"LOC Total: {report.total_loc}/{MAX_LOC}. Abortando matriz."
            )
