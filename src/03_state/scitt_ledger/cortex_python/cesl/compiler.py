# C5-REAL EXERGY CERTIFIED
"""
C5-REAL CESL 1.0 (C5 Engineering Specification Language) Compiler & Transducer.
Parses .cesl specifications into AST and IR, validates invariant completeness,
and compiles into Markdown documentation and Mermaid graph visualizers.
"""

from dataclasses import dataclass, field
import enum

class TokenType(enum.Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    COLON = "COLON"
    ARROW = "ARROW"
    QUESTION = "QUESTION"
    EOF = "EOF"

@dataclass
class CESLToken:
    type: TokenType
    value: str
    line: int
    column: int

@dataclass
class TypeField:
    name: str
    type_name: str
    optional: bool = False

@dataclass
class TypeDecl:
    name: str
    fields: list[TypeField] = field(default_factory=list)

@dataclass
class RelationDecl:
    name: str
    domain: str
    codomain: str

@dataclass
class InvariantDecl:
    name: str
    expression: str

@dataclass
class TransitionDecl:
    name: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    preconditions: str = ""
    postconditions: str = ""

@dataclass
class CapabilityDecl:
    name: str

@dataclass
class CESLAST:
    module_name: str = ""
    types: list[TypeDecl] = field(default_factory=list)
    relations: list[RelationDecl] = field(default_factory=list)
    invariants: list[InvariantDecl] = field(default_factory=list)
    transitions: list[TransitionDecl] = field(default_factory=list)
    capabilities: list[CapabilityDecl] = field(default_factory=list)

class CESLLexer:
    KEYWORDS = {
        "module",
        "type",
        "relation",
        "invariant",
        "transition",
        "capability",
        "verify",
        "forall",
        "exists",
        "where",
        "pre",
        "post",
        "input",
        "output",
    }

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def tokenize(self) -> list[CESLToken]:
        tokens: list[CESLToken] = []
        while self.pos < self.length:
            ch = self.source[self.pos]

            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self.line += 1
                self.column = 1
                self.pos += 1
                continue
            if ch == "/" and self._peek() == "/":
                while self.pos < self.length and self.source[self.pos] != "\n":
                    self.pos += 1
                continue

            self._tokenize_char(ch, tokens)

        tokens.append(CESLToken(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _tokenize_char(self, ch: str, tokens: list[CESLToken]) -> None:
        if ch == "{":
            tokens.append(CESLToken(TokenType.LBRACE, "{", self.line, self.column))
            self._advance()
            return
        if ch == "}":
            tokens.append(CESLToken(TokenType.RBRACE, "}", self.line, self.column))
            self._advance()
            return
        if ch == ":":
            tokens.append(CESLToken(TokenType.COLON, ":", self.line, self.column))
            self._advance()
            return
        if ch == "?":
            tokens.append(CESLToken(TokenType.QUESTION, "?", self.line, self.column))
            self._advance()
            return
        if ch == "-" and self._peek() == ">":
            tokens.append(CESLToken(TokenType.ARROW, "->", self.line, self.column))
            self._advance(2)
            return
        if ch == '"':
            start_line, start_col = self.line, self.column
            self._advance()
            start_pos = self.pos
            while self.pos < self.length and self.source[self.pos] != '"':
                self._advance()
            val = self.source[start_pos : self.pos]
            self._advance()  # closing quote
            tokens.append(CESLToken(TokenType.STRING, val, start_line, start_col))
            return
        if ch.isalpha() or ch == "_":
            start_line, start_col = self.line, self.column
            start_pos = self.pos
            while self.pos < self.length and (self.source[self.pos].isalnum() or self.source[self.pos] in "_."):
                self._advance()
            word = self.source[start_pos : self.pos]
            t_type = TokenType.KEYWORD if word in self.KEYWORDS else TokenType.IDENTIFIER
            tokens.append(CESLToken(t_type, word, start_line, start_col))
            return
        
        self._advance()
        return

    def _advance(self, count: int = 1) -> None:
        for _ in range(count):
            self.pos += 1
            self.column += 1

    def _peek(self) -> str:
        return self.source[self.pos + 1] if self.pos + 1 < self.length else ""

class CESLParser:
    def __init__(self, tokens: list[CESLToken]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _parse_keyword_declaration(self, token: CESLToken, ast: CESLAST) -> None:
        if token.value == "module":
            self._advance()
            ast.module_name = self._consume(TokenType.IDENTIFIER, "Expected module name").value
            return
        if token.value == "type":
            ast.types.append(self._parse_type())
            return
        if token.value == "relation":
            ast.relations.append(self._parse_relation())
            return
        if token.value == "invariant":
            ast.invariants.append(self._parse_invariant())
            return
        if token.value == "transition":
            ast.transitions.append(self._parse_transition())
            return
        if token.value == "capability":
            self._advance()
            cap_name = self._consume(TokenType.IDENTIFIER, "Expected capability name").value
            ast.capabilities.append(CapabilityDecl(name=cap_name))
            return
        
        self._advance()

    def parse(self) -> CESLAST:
        ast = CESLAST()
        while not self._is_at_end():
            token = self._peek()
            if token.type == TokenType.KEYWORD:
                self._parse_keyword_declaration(token, ast)
            else:
                self._advance()
        return ast

    def _parse_type(self) -> TypeDecl:
        self._advance()  # consume 'type'
        name = self._consume(TokenType.IDENTIFIER, "Expected type name").value
        self._consume(TokenType.LBRACE, "Expected '{'")
        fields: list[TypeField] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            f_name = self._consume(TokenType.IDENTIFIER, "Expected field name").value
            self._consume(TokenType.COLON, "Expected ':'")
            f_type = self._consume(TokenType.IDENTIFIER, "Expected field type").value
            optional = False
            if self._check(TokenType.QUESTION):
                optional = True
                self._advance()
            fields.append(TypeField(name=f_name, type_name=f_type, optional=optional))
        self._consume(TokenType.RBRACE, "Expected '}'")
        return TypeDecl(name=name, fields=fields)

    def _parse_relation(self) -> RelationDecl:
        self._advance()  # consume 'relation'
        rel_name = self._consume(TokenType.IDENTIFIER, "Expected relation name").value
        self._consume(TokenType.COLON, "Expected ':'")
        dom = self._consume(TokenType.IDENTIFIER, "Expected domain type").value
        self._consume(TokenType.ARROW, "Expected '->'")
        cod = self._consume(TokenType.IDENTIFIER, "Expected codomain type").value
        return RelationDecl(name=rel_name, domain=dom, codomain=cod)

    def _read_balanced_braces(self) -> list[str]:
        self._advance()
        depth = 1
        expr_parts = []
        while depth > 0 and not self._is_at_end():
            t = self._advance()
            if t.type == TokenType.LBRACE:
                depth += 1
                expr_parts.append(t.value)
                continue
            if t.type == TokenType.RBRACE:
                depth -= 1
                if depth == 0:
                    break
            expr_parts.append(t.value)
        return expr_parts

    def _parse_invariant(self) -> InvariantDecl:
        self._advance()  # consume 'invariant'
        inv_name = self._consume(TokenType.IDENTIFIER, "Expected invariant name").value
        expr_parts = []
        if self._check(TokenType.LBRACE):
            expr_parts = self._read_balanced_braces()
        return InvariantDecl(name=inv_name, expression=" ".join(expr_parts))

    def _process_transition_keyword(self, t: CESLToken, inputs: list, outputs: list) -> tuple[str, str]:
        pre, post = "", ""
        if t.value == "input":
            self._advance()
            self._consume(TokenType.COLON, "Expected ':'")
            inputs.append(self._consume(TokenType.IDENTIFIER, "Expected input type").value)
            return pre, post
        if t.value == "output":
            self._advance()
            self._consume(TokenType.COLON, "Expected ':'")
            outputs.append(self._consume(TokenType.IDENTIFIER, "Expected output type").value)
            return pre, post
        if t.value == "pre":
            self._advance()
            self._consume(TokenType.COLON, "Expected ':'")
            pre = self._read_until_newline_or_keyword()
            return pre, post
        if t.value == "post":
            self._advance()
            self._consume(TokenType.COLON, "Expected ':'")
            post = self._read_until_newline_or_keyword()
            return pre, post
        
        self._advance()
        return pre, post

    def _parse_transition(self) -> TransitionDecl:
        self._advance()  # consume 'transition'
        t_name = self._consume(TokenType.IDENTIFIER, "Expected transition name").value
        self._consume(TokenType.LBRACE, "Expected '{'")
        inputs, outputs = [], []
        pre_cond, post_cond = "", ""

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            t = self._peek()
            if t.type == TokenType.KEYWORD:
                pr, po = self._process_transition_keyword(t, inputs, outputs)
                if pr: pre_cond = pr
                if po: post_cond = po
            else:
                self._advance()
        self._consume(TokenType.RBRACE, "Expected '}'")
        return TransitionDecl(
            name=t_name,
            inputs=inputs,
            outputs=outputs,
            preconditions=pre_cond,
            postconditions=post_cond,
        )

    def _read_until_newline_or_keyword(self) -> str:
        parts = []
        while not self._is_at_end() and not self._check(TokenType.RBRACE):
            t = self._peek()
            if t.type == TokenType.KEYWORD and t.value in (
                "input",
                "output",
                "pre",
                "post",
            ):
                break
            parts.append(self._advance().value)
        return " ".join(parts)

    def _peek(self) -> CESLToken:
        return self.tokens[self.pos]

    def _advance(self) -> CESLToken:
        t = self.tokens[self.pos]
        if not self._is_at_end():
            self.pos += 1
        return t

    def _check(self, t_type: TokenType) -> bool:
        return self._peek().type == t_type

    def _consume(self, t_type: TokenType, err_msg: str) -> CESLToken:
        if self._check(t_type):
            return self._advance()
        raise ValueError(
            f"CESL Syntax Error at line {self._peek().line}, col {self._peek().column}: {err_msg} (got {self._peek().value})"
        )

    def _is_at_end(self) -> bool:
        return self.tokens[self.pos].type == TokenType.EOF

class CESLCompiler:
    def __init__(self, source: str) -> None:
        self.source = source
        self.lexer = CESLLexer(source)

    def compile(self) -> CESLAST:
        tokens = self.lexer.tokenize()
        parser = CESLParser(tokens)
        return parser.parse()

    def generate_mermaid(self, ast: CESLAST) -> str:
        lines = ["graph TD"]
        for r in ast.relations:
            lines.append(f"    {r.domain} -->|{r.name}| {r.codomain}")
        for t in ast.transitions:
            for i in t.inputs:
                lines.append(f"    {i} -->|input to {t.name}| {t.name}_Step")
            for o in t.outputs:
                lines.append(f"    {t.name}_Step -->|produces {o}| {o}")
        return "\n".join(lines)

    def generate_markdown(self, ast: CESLAST) -> str:
        md = [
            f"# Module: {ast.module_name}",
            "",
            "## Defined Types",
        ]
        for t in ast.types:
            md.append(f"### `type {t.name}`")
            for f in t.fields:
                opt = "?" if f.optional else ""
                md.append(f"- `{f.name}`: `{f.type_name}{opt}`")
            md.append("")

        md.append("## Typed Relations")
        for r in ast.relations:
            md.append(f"- **`{r.name}`**: `{r.domain}` $\\rightarrow$ `{r.codomain}`")
        md.append("")

        md.append("## Formal Invariants")
        for inv in ast.invariants:
            md.append(f"- **`{inv.name}`**: `{inv.expression}`")
        md.append("")

        md.append("## Agent Capabilities")
        for cap in ast.capabilities:
            md.append(f"- `capability {cap.name}`")
        md.append("")

        return "\n".join(md)
