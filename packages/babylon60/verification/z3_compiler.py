# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ Z3_COMPILER | Automatic SMT Constraint Generation from Pydantic ASTs
# ============================================================================
# STATE: C5-REAL (Zero-Anergy, Deterministic Type-Level Verification)
# ============================================================================
"""
Compilador AST → Z3: Extrae modelos Pydantic desde código fuente Python,
genera una Representación Intermedia (IR) tipada, y emite restricciones
SMT/Z3 deterministas para verificación formal de invariantes de tipo.

Pipeline:
    Source Files → Python AST → PydanticModelIR → Z3 Sorts/Constraints → SMT-LIB2

Uso:
    from babylon60.verification.z3_compiler import ASTExtractor, Z3ConstraintEmitter

    models = ASTExtractor().extract_from_file(Path("my_models.py"))
    for model in models:
        emitter = Z3ConstraintEmitter()
        solver = emitter.emit_model(model)
        print(solver.check())  # sat / unsat
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("babylon60.verification.z3_compiler")

__all__ = [
    "PydanticFieldIR",
    "PydanticModelIR",
    "ASTExtractor",
    "Z3ConstraintEmitter",
    "compile_models_from_paths",
    "Z3CompilationResult",
]


# ---------------------------------------------------------------------------
# Intermediate Representation (IR)
# ---------------------------------------------------------------------------
@dataclass
class PydanticFieldIR:
    """Representación Intermedia de un campo Pydantic extraído del AST."""

    name: str
    python_type: str  # "str", "int", "float", "bool", "Optional[str]", "List[int]", "Literal['a','b']"
    is_optional: bool = False
    default: Any = None
    has_default: bool = False
    constraints: Dict[str, Any] = field(default_factory=dict)
    enum_values: Optional[List[str]] = None

    def __repr__(self) -> str:
        parts = [f"{self.name}: {self.python_type}"]
        if self.is_optional:
            parts.append("optional")
        if self.constraints:
            parts.append(f"constraints={self.constraints}")
        if self.enum_values:
            parts.append(f"enum={self.enum_values}")
        return f"PydanticFieldIR({', '.join(parts)})"


@dataclass
class PydanticModelIR:
    """Representación Intermedia de un modelo Pydantic completo."""

    class_name: str
    module_path: str
    fields: List[PydanticFieldIR] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"PydanticModelIR({self.class_name}, "
            f"fields={len(self.fields)}, validators={len(self.validators)})"
        )


@dataclass
class Z3CompilationResult:
    """Resultado de compilar un modelo a restricciones Z3."""

    model_name: str
    module_path: str
    is_satisfiable: Optional[bool]  # None = not checked, True = sat, False = unsat
    num_constraints: int
    smtlib2: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# AST Extractor: Python Source → PydanticModelIR
# ---------------------------------------------------------------------------
class ASTExtractor:
    """Extractor de modelos Pydantic desde AST de Python.

    Recorre el AST buscando clases que heredan de BaseModel,
    extrae campos tipados con sus restricciones Field(...) y
    genera PydanticModelIR para cada modelo encontrado.
    """

    # Pydantic base class names we recognize
    _BASE_MODEL_NAMES = frozenset({"BaseModel", "pydantic.BaseModel"})

    # Known constraint keyword arguments in Field(...)
    _FIELD_CONSTRAINT_KEYS = frozenset({
        "ge", "gt", "le", "lt",
        "min_length", "max_length",
        "pattern", "regex",
        "multiple_of",
        "strict",
    })

    def extract_from_file(self, path: Path) -> List[PydanticModelIR]:
        """Extrae modelos Pydantic de un archivo .py."""
        source = path.read_text(encoding="utf-8")
        return self.extract_from_source(source, module_path=str(path))

    def extract_from_source(
        self, source: str, module_path: str = "<string>"
    ) -> List[PydanticModelIR]:
        """Extrae modelos Pydantic desde código fuente Python."""
        try:
            tree = ast.parse(source, filename=module_path)
        except SyntaxError as e:
            logger.error("SyntaxError parsing %s: %s", module_path, e)
            return []

        models: List[PydanticModelIR] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_pydantic_model(node):
                    model_ir = self._extract_model(node, module_path)
                    if model_ir.fields:
                        models.append(model_ir)

        logger.info(
            "Extracted %d Pydantic model(s) from %s", len(models), module_path
        )
        return models

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        """Determina si una clase hereda de BaseModel."""
        for base in node.bases:
            name = self._get_name(base)
            if name in self._BASE_MODEL_NAMES:
                return True
        return False

    def _extract_model(
        self, node: ast.ClassDef, module_path: str
    ) -> PydanticModelIR:
        """Extrae un PydanticModelIR de un nodo ClassDef."""
        fields: List[PydanticFieldIR] = []
        validators: List[str] = []
        base_classes = [self._get_name(b) for b in node.bases]

        for item in node.body:
            # Extract annotated fields
            if isinstance(item, ast.AnnAssign) and isinstance(
                item.target, ast.Name
            ):
                field_ir = self._extract_field(item)
                if field_ir:
                    fields.append(field_ir)

            # Track validators
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in item.decorator_list:
                    dec_name = self._get_name(decorator)
                    if dec_name in (
                        "field_validator",
                        "model_validator",
                        "validator",
                        "root_validator",
                    ):
                        validators.append(item.name)

        return PydanticModelIR(
            class_name=node.name,
            module_path=module_path,
            fields=fields,
            validators=validators,
            base_classes=base_classes,
        )

    def _parse_field_value_details(self, value_node: ast.expr) -> Tuple[Dict[str, Any], Any, bool]:
        """Extrae restricciones y valor por defecto de un nodo ast.expr."""
        if not isinstance(value_node, ast.Call):
            return {}, self._get_literal_value(value_node), True

        func_name = self._get_name(value_node.func)
        if func_name != "Field":
            return {}, self._get_literal_value(value_node), True

        constraints = self._extract_field_constraints(value_node)
        default = None
        has_default = False

        if value_node.args:
            def_val = self._get_literal_value(value_node.args[0])
            if def_val is not ...:
                default = def_val
                has_default = True

        for kw in value_node.keywords:
            if kw.arg == "default":
                default = self._get_literal_value(kw.value)
                has_default = True
            elif kw.arg == "default_factory":
                has_default = True
                default = "<factory>"

        return constraints, default, has_default

    def _extract_field(self, node: ast.AnnAssign) -> Optional[PydanticFieldIR]:
        """Extrae un PydanticFieldIR de una anotación de campo."""
        field_name = node.target.id  # type: ignore[union-attr]
        if field_name.startswith("_"):
            return None

        python_type, is_optional, enum_values = self._parse_annotation(node.annotation)

        constraints: Dict[str, Any] = {}
        default: Any = None
        has_default = False

        if node.value is not None:
            constraints, default, has_default = self._parse_field_value_details(node.value)

        return PydanticFieldIR(
            name=field_name,
            python_type=python_type,
            is_optional=is_optional,
            default=default,
            has_default=has_default,
            constraints=constraints,
            enum_values=enum_values,
        )

    def _parse_annotation(
        self, node: ast.expr
    ) -> Tuple[str, bool, Optional[List[str]]]:
        """Parsea una anotación de tipo y retorna (tipo_str, es_optional, enum_values).

        Handles: str, int, float, bool, Optional[T], List[T], Literal["a","b"], etc.
        """
        is_optional = False
        enum_values: Optional[List[str]] = None

        if isinstance(node, ast.Constant):
            return str(node.value), False, None

        if isinstance(node, ast.Name):
            return node.id, False, None

        if isinstance(node, ast.Attribute):
            return self._get_name(node), False, None

        # Optional[T] or Union[T, None]
        if isinstance(node, ast.Subscript):
            outer_name = self._get_name(node.value)

            if outer_name == "Optional":
                inner_type, _, inner_enum = self._parse_annotation(node.slice)
                return inner_type, True, inner_enum

            if outer_name == "Union":
                # Check for Union[T, None] pattern
                if isinstance(node.slice, ast.Tuple):
                    elts = node.slice.elts
                    none_present = any(
                        (isinstance(e, ast.Constant) and e.value is None)
                        or (isinstance(e, ast.Name) and e.id == "None")
                        for e in elts
                    )
                    non_none = [
                        e
                        for e in elts
                        if not (
                            (isinstance(e, ast.Constant) and e.value is None)
                            or (isinstance(e, ast.Name) and e.id == "None")
                        )
                    ]
                    if none_present and len(non_none) == 1:
                        inner_type, _, inner_enum = self._parse_annotation(
                            non_none[0]
                        )
                        return inner_type, True, inner_enum

            if outer_name == "Literal":
                enum_values = self._extract_literal_values(node.slice)
                return f"Literal[{', '.join(repr(v) for v in enum_values)}]", False, enum_values

            if outer_name == "List" or outer_name == "list":
                inner_type, _, _ = self._parse_annotation(node.slice)
                return f"List[{inner_type}]", False, None

            # Generic subscript
            return f"{outer_name}[...]", False, None

        # T | None (Python 3.10+ union syntax)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left_type, _, left_enum = self._parse_annotation(node.left)
            right_type, _, _ = self._parse_annotation(node.right)
            if right_type == "None":
                return left_type, True, left_enum
            if left_type == "None":
                return right_type, True, None
            return f"Union[{left_type}, {right_type}]", False, None

        return ast.dump(node), False, None

    def _extract_literal_values(self, node: ast.expr) -> List[str]:
        """Extrae valores de Literal[...] como strings."""
        values: List[str] = []
        if isinstance(node, ast.Tuple):
            for elt in node.elts:
                val = self._get_literal_value(elt)
                if val is not None:
                    values.append(str(val))
        else:
            val = self._get_literal_value(node)
            if val is not None:
                values.append(str(val))
        return values

    def _extract_field_constraints(self, call: ast.Call) -> Dict[str, Any]:
        """Extrae restricciones de Field(ge=0, le=100, ...)."""
        constraints: Dict[str, Any] = {}
        for kw in call.keywords:
            if kw.arg in self._FIELD_CONSTRAINT_KEYS:
                val = self._get_literal_value(kw.value)
                if val is not None:
                    constraints[kw.arg] = val
        return constraints

    @staticmethod
    def _get_literal_value(node: ast.expr) -> Any:
        """Extrae un valor literal de un nodo AST."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "None":
                return None
            if node.id == "True":
                return True
            if node.id == "False":
                return False
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = ASTExtractor._get_literal_value(node.operand)
            if isinstance(inner, (int, float)):
                return -inner
        if isinstance(node, ast.List):
            return [ASTExtractor._get_literal_value(e) for e in node.elts]
        return None

    @staticmethod
    def _get_name(node: ast.expr) -> str:
        """Extrae el nombre completo de un nodo (Name o Attribute)."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = ASTExtractor._get_name(node.value)
            return f"{prefix}.{node.attr}"
        if isinstance(node, ast.Call):
            return ASTExtractor._get_name(node.func)
        return ""


# ---------------------------------------------------------------------------
# Z3 Constraint Emitter: PydanticModelIR → Z3 Solver / SMT-LIB2
# ---------------------------------------------------------------------------
class Z3ConstraintEmitter:
    """Transductor PydanticModelIR → restricciones Z3 / SMT-LIB2.

    Genera sorts Z3 para cada campo tipado y emite restricciones
    basadas en las anotaciones de Field(...) extraídas del IR.
    """

    def __init__(self, rlimit: int = 512 * 1024 * 1024, timeout_ms: int = 5000):
        """Inicializa el emitter con límites de recurso para el solver.

        Args:
            rlimit: Límite de memoria en bytes para Z3 (default: 512MB).
            timeout_ms: Timeout en milisegundos para Z3 (default: 5s).
        """
        self._rlimit = rlimit
        self._timeout_ms = timeout_ms
        self._z3 = None

    def _ensure_z3(self):
        """Lazy import de z3 para permitir uso sin la dependencia instalada."""
        if self._z3 is None:
            try:
                import z3
                self._z3 = z3
            except ImportError:
                raise ImportError(
                    "z3-solver is required for Z3 constraint emission. "
                    "Install with: pip install 'babylon60[smt]'"
                )
        return self._z3

    def emit_sort(self, field_ir: PydanticFieldIR) -> Any:
        """Genera el Sort Z3 correspondiente a un tipo Python.

        Returns:
            Tuple de (z3.Sort, z3.ExprRef variable).
        """
        z3 = self._ensure_z3()
        base_type = self._normalize_type(field_ir.python_type)
        var_name = field_ir.name

        if base_type == "str":
            return z3.StringSort(), z3.String(var_name)
        if base_type == "int":
            return z3.IntSort(), z3.Int(var_name)
        if base_type == "float":
            return z3.RealSort(), z3.Real(var_name)
        if base_type == "bool":
            return z3.BoolSort(), z3.Bool(var_name)
        if base_type.startswith("List["):
            inner = self._extract_inner_type(base_type)
            inner_sort = self._type_to_sort(inner)
            arr = z3.Array(var_name, z3.IntSort(), inner_sort)
            length = z3.Int(f"{var_name}__len")
            return z3.ArraySort(z3.IntSort(), inner_sort), (arr, length)
        if field_ir.enum_values is not None:
            # Literal/Enum: use StringSort with constrained domain
            return z3.StringSort(), z3.String(var_name)

        # Fallback: uninterpreted sort
        sort = z3.DeclareSort(f"Sort_{base_type}")
        return sort, z3.Const(var_name, sort)

    def emit_field_constraints(
        self, field_ir: PydanticFieldIR
    ) -> Tuple[Any, List[Any]]:
        """Genera la variable Z3 y sus restricciones para un campo.

        Returns:
            Tuple de (z3_variable, [z3_constraints]).
        """
        z3 = self._ensure_z3()
        base_type = self._normalize_type(field_ir.python_type)
        constraints: List[Any] = []

        sort, var = self.emit_sort(field_ir)

        # Handle List types (var is a tuple of (array, length))
        if isinstance(var, tuple):
            arr, length_var = var
            constraints.append(length_var >= 0)
            if "min_length" in field_ir.constraints:
                constraints.append(length_var >= field_ir.constraints["min_length"])
            if "max_length" in field_ir.constraints:
                constraints.append(length_var <= field_ir.constraints["max_length"])
            return (arr, length_var), constraints

        # Numeric constraints (int / float)
        if base_type in ("int", "float"):
            if "ge" in field_ir.constraints:
                constraints.append(var >= field_ir.constraints["ge"])
            if "gt" in field_ir.constraints:
                constraints.append(var > field_ir.constraints["gt"])
            if "le" in field_ir.constraints:
                constraints.append(var <= field_ir.constraints["le"])
            if "lt" in field_ir.constraints:
                constraints.append(var < field_ir.constraints["lt"])
            if "multiple_of" in field_ir.constraints:
                m = field_ir.constraints["multiple_of"]
                if base_type == "int":
                    constraints.append(var % m == 0)

        # String constraints
        if base_type == "str":
            if "min_length" in field_ir.constraints:
                constraints.append(
                    z3.Length(var) >= field_ir.constraints["min_length"]
                )
            if "max_length" in field_ir.constraints:
                constraints.append(
                    z3.Length(var) <= field_ir.constraints["max_length"]
                )
            if "pattern" in field_ir.constraints:
                pattern = field_ir.constraints["pattern"]
                try:
                    constraints.append(z3.InRe(var, z3.Re(pattern)))
                except Exception:
                    logger.warning(
                        "Could not compile regex pattern %r for field %s",
                        pattern,
                        field_ir.name,
                    )

        # Enum / Literal constraints
        if field_ir.enum_values is not None:
            if base_type == "str" or field_ir.python_type.startswith("Literal"):
                or_clauses = [var == z3.StringVal(v) for v in field_ir.enum_values]
                if or_clauses:
                    constraints.append(z3.Or(*or_clauses))

        # Optional: wrap constraints in implication
        if field_ir.is_optional:
            is_present = z3.Bool(f"{field_ir.name}__present")
            if constraints:
                wrapped = z3.Implies(is_present, z3.And(*constraints))
                return var, [wrapped]
            return var, []

        return var, constraints

    def emit_model(self, model_ir: PydanticModelIR) -> Any:
        """Genera un z3.Solver completo con todas las restricciones del modelo.

        Returns:
            z3.Solver con todas las restricciones inyectadas.
        """
        z3 = self._ensure_z3()
        solver = z3.Solver()
        solver.set("timeout", self._timeout_ms)

        for field_ir in model_ir.fields:
            _, constraints = self.emit_field_constraints(field_ir)
            for c in constraints:
                solver.add(c)

        return solver

    def emit_smtlib2(self, model_ir: PydanticModelIR) -> str:
        """Serializa las restricciones de un modelo a formato SMT-LIB2.

        Returns:
            String SMT-LIB2 representando todas las restricciones.
        """
        solver = self.emit_model(model_ir)
        header = (
            f"; SMT-LIB2 constraints for Pydantic model: {model_ir.class_name}\n"
            f"; Module: {model_ir.module_path}\n"
            f"; Fields: {len(model_ir.fields)}\n"
            f"; Generated by BABYLON-60 Z3 Compiler\n"
        )
        return header + solver.to_smt2()

    def check_satisfiability(
        self, model_ir: PydanticModelIR
    ) -> Z3CompilationResult:
        """Compila y verifica satisfacibilidad de un modelo.

        Returns:
            Z3CompilationResult con el resultado de la verificación.
        """
        z3 = self._ensure_z3()
        try:
            solver = self.emit_model(model_ir)
            num_constraints = len(solver.assertions())
            smtlib2 = self.emit_smtlib2(model_ir)

            result = solver.check()
            if result == z3.sat:
                is_sat = True
            elif result == z3.unsat:
                is_sat = False
            else:
                # z3.unknown — timeout or rlimit exceeded
                is_sat = None

            return Z3CompilationResult(
                model_name=model_ir.class_name,
                module_path=model_ir.module_path,
                is_satisfiable=is_sat,
                num_constraints=num_constraints,
                smtlib2=smtlib2,
            )
        except Exception as e:
            logger.error("Z3 compilation failed for %s: %s", model_ir.class_name, e)
            return Z3CompilationResult(
                model_name=model_ir.class_name,
                module_path=model_ir.module_path,
                is_satisfiable=None,
                num_constraints=0,
                smtlib2="",
                error=str(e),
            )

    def _type_to_sort(self, type_str: str) -> Any:
        """Convierte un string de tipo a un Z3 Sort."""
        z3 = self._ensure_z3()
        mapping = {
            "str": z3.StringSort(),
            "int": z3.IntSort(),
            "float": z3.RealSort(),
            "bool": z3.BoolSort(),
        }
        return mapping.get(type_str, z3.IntSort())

    @staticmethod
    def _normalize_type(python_type: str) -> str:
        """Normaliza un tipo Python a su forma base."""
        # Strip Optional wrapper
        m = re.match(r"Optional\[(.+)\]", python_type)
        if m:
            return Z3ConstraintEmitter._normalize_type(m.group(1))
        # Direct types
        if python_type in ("str", "int", "float", "bool"):
            return python_type
        if python_type.startswith("List[") or python_type.startswith("list["):
            return python_type
        if python_type.startswith("Literal["):
            return "str"  # Literals are treated as constrained strings
        return python_type

    @staticmethod
    def _extract_inner_type(list_type: str) -> str:
        """Extrae el tipo interior de List[T]."""
        m = re.match(r"(?:List|list)\[(.+)\]", list_type)
        if m:
            return m.group(1)
        return "int"


# ---------------------------------------------------------------------------
# Convenience: Batch compilation
# ---------------------------------------------------------------------------
def compile_models_from_paths(
    paths: List[Path],
    rlimit: int = 512 * 1024 * 1024,
    timeout_ms: int = 5000,
    check: bool = True,
) -> List[Z3CompilationResult]:
    """Compila todos los modelos Pydantic encontrados en una lista de paths.

    Args:
        paths: Lista de ficheros .py o directorios a escanear.
        rlimit: Límite de memoria Z3.
        timeout_ms: Timeout Z3.
        check: Si True, verifica satisfacibilidad de cada modelo.

    Returns:
        Lista de Z3CompilationResult.
    """
    extractor = ASTExtractor()
    emitter = Z3ConstraintEmitter(rlimit=rlimit, timeout_ms=timeout_ms)
    results: List[Z3CompilationResult] = []

    py_files: List[Path] = []
    for p in paths:
        if p.is_file() and p.suffix == ".py":
            py_files.append(p)
        elif p.is_dir():
            py_files.extend(p.rglob("*.py"))

    for py_file in sorted(py_files):
        models = extractor.extract_from_file(py_file)
        for model in models:
            if check:
                result = emitter.check_satisfiability(model)
            else:
                smtlib2 = emitter.emit_smtlib2(model)
                result = Z3CompilationResult(
                    model_name=model.class_name,
                    module_path=model.module_path,
                    is_satisfiable=None,
                    num_constraints=len(model.fields),
                    smtlib2=smtlib2,
                )
            results.append(result)

    return results
