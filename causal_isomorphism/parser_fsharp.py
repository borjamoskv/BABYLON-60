# C5-REAL: Targeted parser for F# ontological subset used in BABYLON-60
"""
Parses F# source files into the Intermediate Representation (IR).

This is NOT a general-purpose F# parser. It targets the specific
ontological subset used in BABYLON-60's Domain Kernel:
  - Discriminated unions (type X = | Case1 | Case2 of field: type)
  - Record types (type X = { Field1: type; Field2: type })
  - Functions with pattern matching (let f x = match x with | ...)
  - Module declarations (module Name =)

The parser operates as a line-by-line state machine with context tracking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from causal_isomorphism.ir import (
    IR_BOOL,
    IR_BYTES,
    IR_FLOAT,
    IR_INT,
    IR_STRING,
    IR_UNIT,
    EmitPermission,
    FunctionClassification,
    IRDiscriminatedUnion,
    IRExpr,
    IRExprKind,
    IRFunction,
    IRMatchArm,
    IRModule,
    IRParam,
    IRPattern,
    IRRecordField,
    IRRecordType,
    IRType,
    IRTypeKind,
    IRUnionCase,
    RegimeLayer,
    ir_custom,
    ir_map,
    ir_result,
)


FSHARP_TYPE_MAP: dict[str, IRType] = {
    "float": IR_FLOAT,
    "double": IR_FLOAT,
    "int": IR_INT,
    "int32": IR_INT,
    "int64": IR_INT,
    "string": IR_STRING,
    "bool": IR_BOOL,
    "unit": IR_UNIT,
    "byte[]": IR_BYTES,
}


def resolve_fsharp_type(type_str: str) -> IRType:
    """Resolve an F# type annotation to an IRType."""
    type_str = type_str.strip()

    result_match = re.match(r"Result<(.+),\s*(.+)>", type_str)
    if result_match:
        ok_t = resolve_fsharp_type(result_match.group(1))
        err_t = resolve_fsharp_type(result_match.group(2))
        return ir_result(ok_t, err_t)

    map_match = re.match(r"Map<(.+),\s*(.+)>", type_str)
    if map_match:
        k_t = resolve_fsharp_type(map_match.group(1))
        v_t = resolve_fsharp_type(map_match.group(2))
        return ir_map(k_t, v_t)

    if " * " in type_str:
        parts = [resolve_fsharp_type(p) for p in type_str.split(" * ")]
        return IRType(IRTypeKind.CUSTOM, custom_name="Tuple", type_params=tuple(parts))

    normalized = type_str.lower().strip()
    if normalized in FSHARP_TYPE_MAP:
        return FSHARP_TYPE_MAP[normalized]

    return ir_custom(type_str)


class ParserState(Enum):
    TOP_LEVEL = auto()
    IN_MODULE = auto()
    IN_UNION = auto()
    IN_RECORD = auto()
    IN_FUNCTION = auto()
    IN_MATCH = auto()


@dataclass
class ParserContext:
    """Tracks nested parsing context."""

    state: ParserState = ParserState.TOP_LEVEL
    current_module: IRModule | None = None
    current_union: IRDiscriminatedUnion | None = None
    current_record: IRRecordType | None = None
    current_function: IRFunction | None = None
    current_match_arms: list[IRMatchArm] = field(default_factory=list)
    current_match_var: str = ""
    indent_level: int = 0
    module_stack: list[IRModule] = field(default_factory=list)
    namespace: str = ""


def _get_indent(line: str) -> int:
    """Count leading spaces."""
    return len(line) - len(line.lstrip())


def _classify_function(name: str, params: list[IRParam], body_lines: list[str]) -> FunctionClassification:
    """Classify a function based on its name and content."""
    name_lower = name.lower()

    if "commit" in name_lower or "boundary" in name_lower:
        return FunctionClassification.COMMIT_BOUNDARY
    if "validate" in name_lower or "verify" in name_lower:
        return FunctionClassification.VALIDATION
    if "hash" in name_lower or "taint" in name_lower:
        return FunctionClassification.HASH_COMPUTATION
    if "apply" in name_lower or "transition" in name_lower or "stress" in name_lower:
        return FunctionClassification.STATE_TRANSITION
    if "get" in name_lower or "query" in name_lower or "path" in name_lower:
        return FunctionClassification.PURE_QUERY

    body_text = " ".join(body_lines)
    if "match" in body_text and any(
        "Stable" in b or "Smoothing" in b or "Rollback" in b or "Apoptosis" in b for b in body_lines
    ):
        return FunctionClassification.STATE_TRANSITION

    return FunctionClassification.PURE_QUERY


class FSharpParser:
    """
    Parses F# source files into IRModule trees.

    Usage:
        parser = FSharpParser()
        ir_module = parser.parse_file(Path("domain_kernel/IRPAutomata.fs"))
    """

    RE_NAMESPACE = re.compile(r"^namespace\s+(.+)")
    RE_OPEN = re.compile(r"^\s*open\s+(.+)")
    RE_MODULE = re.compile(r"^(\s*)module\s+(\w+)\s*=")
    RE_UNION_START = re.compile(r"^\s*type\s+(\w+)\s*=\s*$")
    RE_UNION_INLINE = re.compile(r"^\s*type\s+(\w+)\s*=\s*\|")
    RE_UNION_CASE_BARE = re.compile(r"^\s*\|\s+(\w+)\s*$")
    RE_UNION_CASE_PAYLOAD = re.compile(r"^\s*\|\s+(\w+)\s+of\s+(.+)")
    RE_RECORD_START = re.compile(r"^\s*type\s+(\w+)\s*=\s*\{")
    RE_RECORD_FIELD = re.compile(r"^\s*(\w+)\s*:\s*(.+?)(?:;|\}|\s*$)")
    RE_RECORD_END = re.compile(r"^\s*\}")
    RE_LET_FN = re.compile(r"^\s*let\s+(\w+)\s*(.*):\s*(.+?)\s*=")
    RE_MATCH_START = re.compile(r"^\s*match\s+(.+?)\s+with")
    RE_MATCH_CASE = re.compile(r"^\s*\|\s+(\w+)\s*(.*?)\s*->")
    RE_SPRINTF = re.compile(r'sprintf\s+"([^"]+)"\s+(.*)')
    RE_COMMENT = re.compile(r"^\s*//")
    RE_DOC_COMMENT = re.compile(r"^\s*///\s*(.*)")

    def __init__(self) -> None:
        self._ctx = ParserContext()
        self._root_module: IRModule | None = None
        self._raw_lines: list[str] = []
        self._function_body_lines: list[str] = []

    def parse_file(self, path: Path) -> IRModule:
        """Parse an F# source file and return the IRModule tree."""
        source = path.read_text(encoding="utf-8")
        return self.parse_source(source, path.stem)

    def parse_source(self, source: str, module_name: str = "Anonymous") -> IRModule:
        """Parse F# source string into an IRModule."""
        self._ctx = ParserContext()
        self._raw_lines = source.splitlines()
        self._root_module = IRModule(
            name=module_name,
            source_layer=RegimeLayer.ONTOLOGY,
        )
        self._ctx.current_module = self._root_module

        i = 0
        while i < len(self._raw_lines):
            line = self._raw_lines[i]
            i = self._parse_line(i, line)
            i += 1

        self._finalize_pending()

        return self._root_module

    def _parse_line(self, idx: int, line: str) -> int:
        """Parse a single line. Returns the (possibly advanced) line index."""
        stripped = line.strip()

        if not stripped or self.RE_COMMENT.match(line) or self.RE_OPEN.match(line):
            doc_match = self.RE_DOC_COMMENT.match(line)
            if doc_match and self._ctx.current_function is None:
                pass
            return idx

        ns_match = self.RE_NAMESPACE.match(line)
        if ns_match:
            self._ctx.namespace = ns_match.group(1).strip()
            if self._root_module is not None:
                self._root_module.name = self._ctx.namespace.split(".")[-1]
            return idx

        mod_match = self.RE_MODULE.match(line)
        if mod_match:
            self._finalize_pending()
            mod_name = mod_match.group(2)
            new_module = IRModule(
                name=mod_name,
                source_layer=RegimeLayer.ONTOLOGY,
            )
            if self._ctx.current_module is not None:
                self._ctx.current_module.submodules.append(new_module)
            self._ctx.module_stack.append(self._ctx.current_module)  # type: ignore[arg-type]
            self._ctx.current_module = new_module
            self._ctx.indent_level = _get_indent(line)
            return idx

        rec_match = self.RE_RECORD_START.match(line)
        if rec_match:
            self._finalize_pending()
            rec_name = rec_match.group(1)
            self._ctx.current_record = IRRecordType(name=rec_name)
            field_matches = re.findall(r"(\w+)\s*:\s*([^;}\s]+(?:<[^>]+>)?)", line)
            for fname, ftype in field_matches:
                if fname != rec_name:  # Skip the type name itself
                    self._ctx.current_record.fields.append(
                        IRRecordField(name=fname, ir_type=resolve_fsharp_type(ftype))
                    )
            if "}" in line:
                self._commit_record()
            return idx

        union_inline_match = self.RE_UNION_INLINE.match(line)
        if union_inline_match:
            self._finalize_pending()
            union_name = union_inline_match.group(1)
            self._ctx.current_union = IRDiscriminatedUnion(name=union_name)
            rest = line[line.index("|") :]
            self._parse_union_case(rest)
            return idx

        union_start_match = self.RE_UNION_START.match(line)
        if union_start_match:
            self._finalize_pending()
            union_name = union_start_match.group(1)
            self._ctx.current_union = IRDiscriminatedUnion(name=union_name)
            return idx

        if self._ctx.current_union is not None:
            if stripped.startswith("|"):
                self._parse_union_case(stripped)
                return idx
            self._commit_union()
            return self._parse_line(idx, line)

        if self._ctx.current_record is not None:
            if "}" in stripped:
                field_match = self.RE_RECORD_FIELD.match(stripped)
                if field_match:
                    self._ctx.current_record.fields.append(
                        IRRecordField(
                            name=field_match.group(1),
                            ir_type=resolve_fsharp_type(field_match.group(2)),
                        )
                    )
                self._commit_record()
                return idx
            field_match = self.RE_RECORD_FIELD.match(stripped)
            if field_match:
                self._ctx.current_record.fields.append(
                    IRRecordField(
                        name=field_match.group(1),
                        ir_type=resolve_fsharp_type(field_match.group(2)),
                    )
                )
            return idx

        fn_match = self.RE_LET_FN.match(line)
        if fn_match:
            self._finalize_pending()
            fn_name = fn_match.group(1)
            params_str = fn_match.group(2).strip()
            return_type_str = fn_match.group(3).strip()

            params = self._parse_params(params_str)
            return_type = resolve_fsharp_type(return_type_str)

            body_lines: list[str] = []
            fn_indent = _get_indent(line)
            rest_of_line = line[line.index("=") + 1 :].strip()
            if rest_of_line:
                body_lines.append(rest_of_line)

            j = idx + 1
            while j < len(self._raw_lines):
                next_line = self._raw_lines[j]
                next_stripped = next_line.strip()
                next_indent = _get_indent(next_line) if next_stripped else fn_indent + 4

                if next_stripped and next_indent <= fn_indent:
                    break
                body_lines.append(next_line)
                j += 1

            classification = _classify_function(fn_name, params, body_lines)
            body_expr = self._parse_function_body(body_lines)

            func = IRFunction(
                name=fn_name,
                params=params,
                return_type=return_type,
                body=body_expr,
                is_pure=classification != FunctionClassification.EVENT_EMITTER,
                classification=classification,
            )

            if self._ctx.current_module is not None:
                self._ctx.current_module.functions.append(func)

            return j - 1  # Return last consumed line

        return idx

    def _parse_union_case(self, case_line: str) -> None:
        """Parse a single union case line: | CaseName of field: type."""
        if self._ctx.current_union is None:
            return

        stripped = case_line.strip()
        if not stripped.startswith("|"):
            return

        content = stripped[1:].strip()

        of_match = re.match(r"(\w+)\s+of\s+(.+)", content)
        if of_match:
            case_name = of_match.group(1)
            payload_str = of_match.group(2).strip()
            fields = self._parse_payload_fields(payload_str)
            self._ctx.current_union.cases.append(IRUnionCase(name=case_name, payload_fields=fields))
            return

        bare_match = re.match(r"(\w+)", content)
        if bare_match:
            case_name = bare_match.group(1)
            self._ctx.current_union.cases.append(IRUnionCase(name=case_name))

    def _parse_payload_fields(self, payload_str: str) -> list[tuple[str, IRType]]:
        """Parse union case payload: field1: type1 * field2: type2."""
        fields: list[tuple[str, IRType]] = []

        parts = [p.strip() for p in payload_str.split("*")]
        for part in parts:
            colon_match = re.match(r"(\w+)\s*:\s*(.+)", part)
            if colon_match:
                fname = colon_match.group(1)
                ftype = resolve_fsharp_type(colon_match.group(2).strip())
                fields.append((fname, ftype))
            else:
                ftype = resolve_fsharp_type(part)
                fields.append(("value", ftype))

        return fields

    def _parse_params(self, params_str: str) -> list[IRParam]:
        """Parse function parameters: (p1: type1) (p2: type2)."""
        params: list[IRParam] = []
        for match in re.finditer(r"\((\w+)\s*:\s*([^)]+)\)", params_str):
            pname = match.group(1)
            ptype = resolve_fsharp_type(match.group(2).strip())
            params.append(IRParam(name=pname, ir_type=ptype))
        return params

    def _parse_function_body(self, body_lines: list[str]) -> IRExpr:
        """Parse function body into an IRExpr tree."""
        match_var = ""
        arms: list[IRMatchArm] = []
        current_arm_body: list[str] = []
        current_pattern: IRPattern | None = None
        in_match = False

        for line in body_lines:
            stripped = line.strip()

            match_start = self.RE_MATCH_START.match(stripped)
            if match_start:
                if in_match and current_pattern is not None:
                    arm_body = self._lines_to_expr(current_arm_body)
                    arms.append(IRMatchArm(pattern=current_pattern, body=arm_body))
                    current_arm_body = []
                    current_pattern = None

                match_var = match_start.group(1).strip()
                in_match = True
                continue

            if in_match:
                case_match = self.RE_MATCH_CASE.match(stripped)
                if case_match:
                    if current_pattern is not None:
                        arm_body = self._lines_to_expr(current_arm_body)
                        arms.append(IRMatchArm(pattern=current_pattern, body=arm_body))
                        current_arm_body = []

                    case_name = case_match.group(1)
                    bindings_str = case_match.group(2).strip()
                    bindings = self._extract_bindings(bindings_str)

                    is_wildcard = case_name == "_"
                    current_pattern = IRPattern(
                        case_name=case_name,
                        bindings=bindings,
                        is_wildcard=is_wildcard,
                    )

                    arrow_idx = stripped.index("->")
                    after_arrow = stripped[arrow_idx + 2 :].strip()
                    if after_arrow:
                        current_arm_body = [after_arrow]
                    continue

                if current_pattern is not None:
                    current_arm_body.append(stripped)
                continue

        if current_pattern is not None:
            arm_body = self._lines_to_expr(current_arm_body)
            arms.append(IRMatchArm(pattern=current_pattern, body=arm_body))

        if arms:
            return IRExpr(
                kind=IRExprKind.MATCH,
                match_expr=IRExpr(kind=IRExprKind.VARIABLE, variable_name=match_var),
                match_arms=arms,
                requires_permission=EmitPermission.PHYSICS_COMPUTATION,
            )

        return self._lines_to_expr(body_lines)

    def _extract_bindings(self, bindings_str: str) -> list[str]:
        """Extract variable bindings from a pattern match case."""
        bindings: list[str] = []
        bindings_str = bindings_str.strip()
        if not bindings_str:
            return bindings

        for part in re.findall(r"(\w+)", bindings_str):
            if part not in ("of", "with", "when", "as"):
                bindings.append(part)
        return bindings

    def _lines_to_expr(self, lines: list[str]) -> IRExpr:
        """Convert raw body lines into an IRExpr."""
        if not lines:
            return IRExpr(kind=IRExprKind.LITERAL, literal_value="()", literal_type=IR_UNIT)

        combined = " ".join(line_str.strip() for line_str in lines if line_str.strip())

        sprintf_match = self.RE_SPRINTF.match(combined)
        if sprintf_match:
            fmt = sprintf_match.group(1)
            args_str = sprintf_match.group(2)
            args = [IRExpr(kind=IRExprKind.VARIABLE, variable_name=a.strip()) for a in args_str.split() if a.strip()]
            return IRExpr(
                kind=IRExprKind.STRING_FORMAT,
                format_string=fmt,
                format_args=args,
                requires_permission=EmitPermission.PURE_QUERY,
            )

        ctor_match = re.match(r"(\w+)\s+(.+)", combined)
        if ctor_match:
            case_name = ctor_match.group(1)
            args_raw = ctor_match.group(2).strip()
            args = [
                IRExpr(kind=IRExprKind.VARIABLE, variable_name=a.strip().strip('"'))
                for a in re.split(r"\s+", args_raw)
                if a.strip()
            ]
            return IRExpr(
                kind=IRExprKind.CONSTRUCTOR,
                case_name=case_name,
                constructor_args=args,
                requires_permission=EmitPermission.PHYSICS_COMPUTATION,
            )

        if combined.startswith('"') and combined.endswith('"'):
            return IRExpr(
                kind=IRExprKind.LITERAL,
                literal_value=combined.strip('"'),
                literal_type=IR_STRING,
            )

        try:
            float(combined)
            return IRExpr(
                kind=IRExprKind.LITERAL,
                literal_value=combined,
                literal_type=IR_FLOAT,
            )
        except ValueError:
            pass

        return IRExpr(
            kind=IRExprKind.VARIABLE,
            variable_name=combined,
        )

    def _commit_union(self) -> None:
        """Commit the current union to the current module."""
        if self._ctx.current_union is not None and self._ctx.current_module is not None:
            self._ctx.current_module.unions.append(self._ctx.current_union)
        self._ctx.current_union = None

    def _commit_record(self) -> None:
        """Commit the current record to the current module."""
        if self._ctx.current_record is not None and self._ctx.current_module is not None:
            self._ctx.current_module.records.append(self._ctx.current_record)
        self._ctx.current_record = None

    def _finalize_pending(self) -> None:
        """Finalize any pending parse constructs."""
        self._commit_union()
        self._commit_record()
