# MOSKV-85 SPECIFICATION
## The Sovereign Base-85 Virtual Machine Kernel
**Author:** Borja Moskv (borjamoskv)  
**Reality Level:** C5-REAL  
**Aesthetic:** Industrial Noir 2026  

---

### 1. Introduction

MOSKV-85 is a stack-based, Turing-complete virtual machine and esoteric programming language designed to operate over the 85 printable ASCII characters from code 33 (character "!") to 117 (character "u"). Any character outside of this alphabet is treated as whitespace or ignored (acting as comments), except when enclosed inside string literal blocks or comments.

**Ouroboros AST Compiler & Optimizer:** To maximize thermodynamic execution efficiency (exergy), MOSKV-85 transpiles all code Ahead-Of-Time (AOT) into a dense Abstract Syntax Tree (AST), applying recursive constant folding on binary and unary operations prior to execution. This eliminates runtime computation overhead for static evaluations, resolving expressions like `5 5 +` to `10` directly in the AST, resulting in an ultra-fast O(1) execution dispatch.

---

### 2. Base-85 Alphabet Mapping

The alphabet contains exactly 85 characters, ordered by ASCII code:
`!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstu`

Each character maps to a digit value from 0 to 84:
- "!" = 0
- "\"" = 1
- "#" = 2
- ...
- "u" = 84

---

### 3. Literals & Constants

MOSKV-85 supports direct integer pushing, 32-bit/64-bit Base-85 literals, and fast built-in constants.

- **Direct digits:** "0" to "9" push the corresponding integer values 0 to 9 directly onto the stack.
- **32-bit Literals:** The prefix "#" reads the next 5 characters, decodes them from Base-85 as a 32-bit unsigned value, converts it to a signed 32-bit integer, and pushes it onto the stack.
- **64-bit Literals:** The prefix "$" reads the next 10 characters, decodes them from Base-85 as a 64-bit unsigned value, converts it to a signed 64-bit integer, and pushes it onto the stack.
- **Built-in constants:**
  - "(" pushes -1.
  - ")" pushes 255 (byte mask).
  - "F" pushes 0 (False).
  - "O" pushes 1 (True).
  - "T" pushes 2 (Two).
  - "H" pushes 100.
  - "K" pushes 1000.
  - "P" pushes 314159 (approximated Pi).
  - "k" pushes the Creator magic constant (858585).
  - "V" pushes the MOSKV-85 version identifier (85).

---

### 4. Instruction Set

| Opcode | Category | Description |
|---|---|---|
| `!` | Bitwise | Bitwise NOT |
| `"` | Stack | DUP2 (Duplicate top two elements) |
| `#` | Literal | Push 32-bit Base-85 literal (consumes 5 characters) |
| `$` | Literal | Push 64-bit Base-85 literal (consumes 10 characters) |
| `%` | Math | Modulo division (`a % b`) |
| `&` | Bitwise | Bitwise AND |
| `'` | Bitwise | Bitwise XOR |
| `(` | Constant | Push -1 |
| `)` | Constant | Push 255 |
| `*` | Math | Multiplication (`a * b`) |
| `+` | Math | Addition (`a + b`) |
| `,` | IO | Print top of stack as ASCII character (or whole string if it is a String) |
| `-` | Math | Subtraction (`a - b`) |
| `.` | IO | Print top of stack as decimal integer |
| `/` | Math | Integer division (`a // b`, protected) |
| `0` to `9` | Constant | Push value 0 to 9 |
| `:` | Stack | DUP3 (Duplicate top three elements) |
| `;` | Stack | POP2 (Remove top two elements) |
| `<` | Bitwise | Left shift (`a << b`) |
| `=` | Logic | Assert equality (`a == b` -> 1 or 0) |
| `>` | Bitwise | Right shift (`a >> b`) |
| `?` | Debug | Dumps the stack and memory state to stderr |
| `@` | Stack | ROT_LEFT (`[a, b, c]` -> `[b, c, a]`) |
| `A` | Math | Absolute value |
| `B` | Bitwise | Bit length of top element |
| `C` | Type | Convert top element to its string representation |
| `D` | Math | Double value (`a * 2`) |
| `E` | Math | Power of two (`2 ** a`) |
| `G` | Logic | Greater or equal (`a >= b` -> 1 or 0) |
| `I` | Math | Increment by 1 (`a + 1`) |
| `J` | Math | Decrement by 1 (`a - 1`) |
| `L` | Logic | Less or equal (`a <= b` -> 1 or 0) |
| `M` | Math | Maximum of two elements (`max(a, b)`) |
| `N` | Math | Minimum of two elements (`min(a, b)`) |
| `Q` | Math | Integer square root |
| `R` | Math | Pseudo-random integer between 0 and `a - 1` |
| `S` | Math | Sign of value (`-1`, `0`, or `1`) |
| `[` | Flow | Start code block capture |
| `\` | Literal | Start/End string literal capture |
| `]` | Flow | End code block capture |
| `^` | Math | Power exponentiation (`a ** b`) |
| `_` | Bitwise | Bitwise OR |
| `` ` `` | Comment | Line comment. Ignores everything until next newline |
| `a` | Logic | Less than (`a < b` -> 1 or 0) |
| `b` | Logic | Greater than (`a > b` -> 1 or 0) |
| `c` | Stack | Clear entire stack |
| `d` | Stack | DUP (Duplicate top element) |
| `e` | Flow | Execute block / Evaluate string / Exec ASCII instruction |
| `f` | Flow | While loop (`cond_block` `body_block` f) |
| `g` | Memory | Store (`value` `address` g -> `memory[address] = value`) |
| `h` | Memory | Load (`address` h -> push `memory[address]`) |
| `i` | IO | Read single character from stdin and push ASCII value |
| `j` | Flow | If-Else conditional (`true_block` `false_block` `cond` j) |
| `k` | Constant | Push Creator magic constant (858585) |
| `l` | Stack | Push current stack length |
| `m` | Meta | Print MOSKV-85 VM metadata, credits and version |
| `n` | IO | Read integer from stdin |
| `o` | Stack | OVER (Copy second element to top) |
| `p` | Stack | POP/DROP (Remove top element) |
| `q` | Logic | Not equal (`a != b` -> 1 or 0) |
| `r` | Stack | ROT (`[a, b, c]` -> `[b, c, a]`) |
| `s` | Stack | SWAP (Exchange top two elements) |
| `t` | Flow | If conditional (`true_block` `cond` t) |
| `u` | Flow | Halt execution |

---

### 5. Execution Model

- **Comments:** The backtick character (`` ` ``) comments out the rest of the line. Any non-alphabet character in regular code blocks is silently ignored.
- **Strings:** Double backslashes (like `\text\`) represent string constants. When parsed, the string is pushed to the stack as a unified String object.
- **Blocks:** Square brackets `[ ... ]` group code as data (blocks). A block is pushed onto the stack as a string containing its code.
- **While Loops:** The `f` instruction popped a conditional block and a body block. It runs the conditional block, pops the top of the stack, and if it is non-zero, runs the body block, repeating the cycle.
- **Conditionals:** The `t` instruction pops a condition and a block, executing it if the condition is non-zero. The `j` instruction pops a condition, a false block, and a true block, executing the corresponding block.

---

### 6. Usage and Execution

To run a MOSKV-85 file, execute:
```bash
python3 moskv85.py <file.m85>
```

To run with final debug information (dumps stack and memory at halt):
```bash
python3 moskv85.py -d <file.m85>
```

To encode numbers to Base-85 representation:
```bash
python3 helper.py <integer_value> [width=5/10]
```
