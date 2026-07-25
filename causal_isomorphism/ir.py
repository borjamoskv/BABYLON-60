from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

class RegimeLayer(Enum):
    ONTOLOGY = 'fsharp'
    THERMODYNAMICS = 'rust'
    CONSENSUS = 'solidity'

class EmitPermission(Enum):
    TYPE_DEFINITION = auto()
    STATE_STORAGE = auto()
    EVENT_EMISSION = auto()
    COMMIT_ANCHOR = auto()
    VALIDATION_GUARD = auto()
    PHYSICS_COMPUTATION = auto()
    POSET_OPERATION = auto()
    PURE_QUERY = auto()
REGIME_PERMISSIONS: dict[RegimeLayer, frozenset[EmitPermission]] = {RegimeLayer.ONTOLOGY: frozenset({EmitPermission.TYPE_DEFINITION, EmitPermission.PHYSICS_COMPUTATION, EmitPermission.VALIDATION_GUARD, EmitPermission.PURE_QUERY}), RegimeLayer.THERMODYNAMICS: frozenset({EmitPermission.TYPE_DEFINITION, EmitPermission.POSET_OPERATION, EmitPermission.VALIDATION_GUARD, EmitPermission.PURE_QUERY}), RegimeLayer.CONSENSUS: frozenset({EmitPermission.TYPE_DEFINITION, EmitPermission.STATE_STORAGE, EmitPermission.EVENT_EMISSION, EmitPermission.COMMIT_ANCHOR, EmitPermission.VALIDATION_GUARD, EmitPermission.PURE_QUERY})}

class IRTypeKind(Enum):
    FLOAT = 'float'
    INT = 'int'
    STRING = 'string'
    BOOL = 'bool'
    UNIT = 'unit'
    BYTES = 'bytes'
    CUSTOM = 'custom'
    RESULT = 'Result'
    MAP = 'Map'
    LIST = 'list'
    OPTION = 'Option'

@dataclass(frozen=True)
class IRType:
    kind: IRTypeKind
    custom_name: str = ''
    type_params: tuple[IRType, ...] = ()
    is_linear: bool = False
    is_affine: bool = False
    region: str = ''

    def __repr__(self) -> str:
        if self.kind == IRTypeKind.CUSTOM:
            return f'IRType({self.custom_name})'
        if self.type_params:
            params = ', '.join((repr(p) for p in self.type_params))
            return f'IRType({self.kind.value}<{params}>)'
        return f'IRType({self.kind.value})'
IR_FLOAT = IRType(IRTypeKind.INTEGER)
IR_INT = IRType(IRTypeKind.INT)
IR_STRING = IRType(IRTypeKind.STRING)
IR_BOOL = IRType(IRTypeKind.BOOL)
IR_UNIT = IRType(IRTypeKind.UNIT)
IR_BYTES = IRType(IRTypeKind.BYTES)

def ir_custom(name: str) -> IRType:
    return IRType(IRTypeKind.CUSTOM, custom_name=name)

def ir_result(ok_type: IRType, err_type: IRType) -> IRType:
    return IRType(IRTypeKind.RESULT, type_params=(ok_type, err_type))

def ir_map(key_type: IRType, val_type: IRType) -> IRType:
    return IRType(IRTypeKind.MAP, type_params=(key_type, val_type))

@dataclass
class IRUnionCase:
    name: str
    payload_fields: list[tuple[str, IRType]] = field(default_factory=list)

@dataclass
class IRDiscriminatedUnion:
    name: str
    cases: list[IRUnionCase] = field(default_factory=list)

    @property
    def is_simple_enum(self) -> bool:
        return all((len(c.payload_fields) == 0 for c in self.cases))

    @property
    def has_numeric_payload(self) -> bool:
        return any((any((t.kind == IRTypeKind.FLOAT or t.kind == IRTypeKind.INT for _, t in c.payload_fields)) for c in self.cases))

    @property
    def has_string_payload(self) -> bool:
        return any((any((t.kind == IRTypeKind.STRING for _, t in c.payload_fields)) for c in self.cases))

@dataclass
class IRRecordField:
    name: str
    ir_type: IRType

@dataclass
class IRRecordType:
    name: str
    fields: list[IRRecordField] = field(default_factory=list)

class IRExprKind(Enum):
    LITERAL = auto()
    VARIABLE = auto()
    FIELD_ACCESS = auto()
    CONSTRUCTOR = auto()
    FUNCTION_CALL = auto()
    BINARY_OP = auto()
    STRING_FORMAT = auto()
    MATCH = auto()
    WILDCARD_MATCH = auto()
    RETURN_OK = auto()
    RETURN_ERROR = auto()
    BLOCK = auto()

@dataclass
class IRPattern:
    case_name: str = ''
    bindings: list[str] = field(default_factory=list)
    is_wildcard: bool = False

@dataclass
class IRMatchArm:
    pattern: IRPattern
    body: IRExpr
    guard: IRExpr | None = None

@dataclass
class IRExpr:
    kind: IRExprKind
    literal_value: str = ''
    literal_type: IRType | None = None
    variable_name: str = ''
    object_expr: IRExpr | None = None
    field_name: str = ''
    type_name: str = ''
    case_name: str = ''
    constructor_args: list[IRExpr] = field(default_factory=list)
    function_name: str = ''
    call_args: list[IRExpr] = field(default_factory=list)
    op: str = ''
    left: IRExpr | None = None
    right: IRExpr | None = None
    format_string: str = ''
    format_args: list[IRExpr] = field(default_factory=list)
    match_expr: IRExpr | None = None
    match_arms: list[IRMatchArm] = field(default_factory=list)
    statements: list[IRExpr] = field(default_factory=list)
    requires_permission: EmitPermission = EmitPermission.PURE_QUERY

@dataclass
class IRParam:
    name: str
    ir_type: IRType
    is_consumed: bool = False

class FunctionClassification(Enum):
    STATE_TRANSITION = auto()
    COMMIT_BOUNDARY = auto()
    VALIDATION = auto()
    PURE_QUERY = auto()
    HASH_COMPUTATION = auto()
    EVENT_EMITTER = auto()

@dataclass
class IRFunction:
    name: str
    params: list[IRParam] = field(default_factory=list)
    return_type: IRType = IR_UNIT
    body: IRExpr | None = None
    is_pure: bool = True
    classification: FunctionClassification = FunctionClassification.PURE_QUERY
    doc_comment: str = ''

@dataclass
class IRModule:
    name: str
    source_layer: RegimeLayer = RegimeLayer.ONTOLOGY
    unions: list[IRDiscriminatedUnion] = field(default_factory=list)
    records: list[IRRecordType] = field(default_factory=list)
    functions: list[IRFunction] = field(default_factory=list)
    submodules: list[IRModule] = field(default_factory=list)

    def all_types(self) -> list[IRDiscriminatedUnion | IRRecordType]:
        result: list[IRDiscriminatedUnion | IRRecordType] = []
        result.extend(self.unions)
        result.extend(self.records)
        for sub in self.submodules:
            result.extend(sub.all_types())
        return result

    def all_functions(self) -> list[IRFunction]:
        result = list(self.functions)
        for sub in self.submodules:
            result.extend(sub.all_functions())
        return result