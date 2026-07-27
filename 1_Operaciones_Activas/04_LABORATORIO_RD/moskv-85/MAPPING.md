# MOSKV-85 ONTOLOGICAL MATRIX
SYS_ID: borjamoskv
Reality Level: C5-REAL
Hash: f482651d8b9d311b1cbeb89e558faac9e8ac251d (Base)

```yaml
meta:
  engine: "Ouroboros AST Execution Matrix v2.0"
  alphabet: "ASCII 33-117"
  cardinality: 85

primitives:
  numerics:
    "0-9": "PUSH_INT(0-9)"
    "#": "AOT_32BIT_LITERAL (Consumes 5 bytes)"
    "$": "AOT_64BIT_LITERAL (Consumes 10 bytes)"
    "\\": "AOT_STRING_LITERAL (Consumes until next \\)"

  arithmetic:
    "+": "ADD"
    "-": "SUB"
    "*": "MUL"
    "/": "DIV (Zero-guarded)"
    "%": "MOD (Zero-guarded)"
    "^": "POW"
    "A": "ABS"
    "D": "MUL_BY_2"
    "E": "POW_OF_2"
    "I": "INC"
    "J": "DEC"
    "Q": "SQRT"
    "R": "RANDOM (0 to max(0, limit-1))"

  bitwise:
    "!": "NOT"
    "&": "AND"
    "_": "OR"
    "'": "XOR"
    "<": "LSHIFT"
    ">": "RSHIFT"
    "B": "BIT_LENGTH"

  constants:
    "(": "PUSH(-1)"
    ")": "PUSH(255)"
    "H": "PUSH(100)"
    "K": "PUSH(1000)"
    "P": "PUSH(314159)"
    "V": "PUSH(85)"
    "k": "PUSH(858585)"

  stack:
    "d": "DUP"
    "\"": "DUP2"
    ":": "DUP3"
    "o": "OVER"
    "s": "SWAP"
    "p": "POP"
    ";": "POP2"
    "r": "ROT_RIGHT (a b c -> b c a)"
    "@": "ROT_LEFT (a b c -> c a b)"
    "c": "CLEAR"
    "l": "STACK_LEN"
    "U": "STACK_LEN"

  flow:
    "e": "EVAL_AST"
    "t": "IF_AST"
    "j": "IF_ELSE_AST"
    "f": "WHILE_AST"

  concurrency:
    "F": "CHAN_CREATE"
    "O": "CHAN_SEND"
    "T": "CHAN_RECV"
    "Y": "SPAWN"

  memory:
    "g": "STORE"
    "h": "LOAD"

  disk:
    "W": "WRITE_FILE"
    "Z": "READ_FILE"
    "X": "IMPORT_AOT"

  io_system:
    ".": "PRINT_VAL"
    ",": "PRINT_CHAR"
    "i": "READ_CHAR"
    "n": "READ_INT"
    "m": "PRINT_METADATA"
    "?": "DEBUG_DUMP"
    "u": "HALT"

hardware_mapping:
  mmio:
    "0x0000-0x00FF": "Kernel reserved"
    "0x0100-0x7FFF": "General RAM"
    "0x8000-0x800F": "RNG register"
    "0x8010-0x801F": "High-Res System Timer"
    "0x8020-0x802F": "UART buffer"
    "0x8030-0x803F": "VRAM framebuffer"

antipatterns:
  - id: "STACK_OVERFLOW_DUP3"
    cause: "Original implementation duplicated the whole triad twice instead of single push."
    status: "RESOLVED"
  - id: "EVAL_HOT_PARSING"
    cause: "Scanning strings iteratively inside while loops."
    status: "RESOLVED_BY_AOT_AST"

redundancies:
  - target: "lex_purge"
    status: "ELIMINATED (Fused into compile_aot)"
```
