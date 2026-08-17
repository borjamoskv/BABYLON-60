# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TS_FRONTEND | TypeScript Declaration File → PydanticModelIR Extractor
# ============================================================================
# STATE: C5-REAL (Phase 1 Stub — Regex-Based .d.ts Parser)
# ============================================================================
"""
Frontend TypeScript para el compilador Z3: parsea ficheros .d.ts
(TypeScript declaration files) y genera PydanticModelIR equivalente,
reutilizando el Z3ConstraintEmitter sin cambios.

Phase 1: Parsing basado en regex para interfaces simples.
Phase 2 (futuro): Integración con tree-sitter-typescript para AST completo.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

from babylon60.verification.z3_compiler import PydanticFieldIR, PydanticModelIR

logger = logging.getLogger("babylon60.verification.ts_frontend")

__all__ = ["TypeScriptDeclExtractor"]

# TypeScript → Python type mapping
_TS_TYPE_MAP = {
    "string": "str",
    "number": "float",
    "boolean": "bool",
    "bigint": "int",
    "any": "str",
    "unknown": "str",
    "void": "None",
    "null": "None",
    "undefined": "None",
}

# Regex patterns for .d.ts parsing
_INTERFACE_PATTERN = re.compile(
    r"(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{",
    re.MULTILINE,
)

_FIELD_PATTERN = re.compile(
    r"^\s+(\w+)(\??):\s*(.+?)\s*;",
    re.MULTILINE,
)


class TypeScriptDeclExtractor:
    """Extrae interfaces de archivos .d.ts y genera PydanticModelIR equivalente.

    Mapeo de tipos:
        string → str, number → float, boolean → bool
        string[] → List[str], T | null → Optional[T]
        T | undefined → Optional[T]
    """

    def extract_from_dts(self, path: Path) -> List[PydanticModelIR]:
        """Extrae interfaces de un archivo .d.ts."""
        source = path.read_text(encoding="utf-8")
        return self.extract_from_source(source, module_path=str(path))

    def extract_from_source(
        self, source: str, module_path: str = "<string>"
    ) -> List[PydanticModelIR]:
        """Extrae interfaces de código TypeScript."""
        models: List[PydanticModelIR] = []

        # Find all interface blocks
        for match in _INTERFACE_PATTERN.finditer(source):
            interface_name = match.group(1)
            extends = match.group(2)
            base_classes = (
                [b.strip() for b in extends.split(",")]
                if extends
                else []
            )

            # Extract the body of the interface (between { and })
            start = match.end()
            brace_depth = 1
            pos = start
            while pos < len(source) and brace_depth > 0:
                if source[pos] == "{":
                    brace_depth += 1
                elif source[pos] == "}":
                    brace_depth -= 1
                pos += 1
            body = source[start : pos - 1]

            # Parse fields from body
            fields: List[PydanticFieldIR] = []
            for field_match in _FIELD_PATTERN.finditer(body):
                field_name = field_match.group(1)
                is_optional_mark = field_match.group(2) == "?"
                ts_type = field_match.group(3).strip()

                python_type, is_optional = self._map_ts_type(ts_type)
                is_optional = is_optional or is_optional_mark

                # Check for literal union types
                enum_values = self._extract_literal_union(ts_type)

                fields.append(
                    PydanticFieldIR(
                        name=field_name,
                        python_type=python_type,
                        is_optional=is_optional,
                        enum_values=enum_values,
                    )
                )

            if fields:
                models.append(
                    PydanticModelIR(
                        class_name=interface_name,
                        module_path=module_path,
                        fields=fields,
                        base_classes=base_classes,
                    )
                )

        logger.info(
            "Extracted %d TypeScript interface(s) from %s",
            len(models),
            module_path,
        )
        return models

    def _map_ts_type(self, ts_type: str) -> Tuple[str, bool]:
        """Mapea un tipo TypeScript a un tipo Python + flag de opcionalidad."""
        ts_type = ts_type.strip()
        is_optional = False

        # Handle T | null or T | undefined
        union_parts = [p.strip() for p in ts_type.split("|")]
        nullable_markers = {"null", "undefined"}
        non_null_parts = [p for p in union_parts if p not in nullable_markers]

        if len(non_null_parts) < len(union_parts):
            is_optional = True
            if len(non_null_parts) == 1:
                ts_type = non_null_parts[0]
            elif not non_null_parts:
                return "None", True
            else:
                ts_type = " | ".join(non_null_parts)

        # Check for array types: T[] or Array<T>
        arr_match = re.match(r"(\w+)\[\]$", ts_type)
        if arr_match:
            inner = self._map_scalar_type(arr_match.group(1))
            return f"List[{inner}]", is_optional

        arr_generic = re.match(r"Array<(\w+)>$", ts_type)
        if arr_generic:
            inner = self._map_scalar_type(arr_generic.group(1))
            return f"List[{inner}]", is_optional

        # Scalar type
        return self._map_scalar_type(ts_type), is_optional

    @staticmethod
    def _map_scalar_type(ts_type: str) -> str:
        """Mapea un tipo escalar TypeScript a Python."""
        return _TS_TYPE_MAP.get(ts_type, ts_type)

    @staticmethod
    def _extract_literal_union(ts_type: str) -> Optional[List[str]]:
        """Extrae valores de un union literal (ej. 'a' | 'b' | 'c')."""
        # Match patterns like: "active" | "inactive" | "pending"
        literal_pattern = re.compile(r"""['"](\w+)['"]""")
        parts = [p.strip() for p in ts_type.split("|")]

        # All parts must be string literals
        values: List[str] = []
        for part in parts:
            m = literal_pattern.fullmatch(part.strip())
            if m:
                values.append(m.group(1))
            elif part.strip() in ("null", "undefined"):
                continue
            else:
                return None

        return values if values else None
