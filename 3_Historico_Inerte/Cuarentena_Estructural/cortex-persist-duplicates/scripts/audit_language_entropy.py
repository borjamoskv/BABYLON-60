# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
cat_id: audit-language-entropy
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import ast
import json
import logging
import os
import re
import sys
import tokenize

SPANISH_CHARS_PATTERN = re.compile(r"[áéíóúÁÉÍÓÚñÑüÜ]")
# C5-REAL Entropy Stopwords: common spanish words found in bad codebase translations
SPANISH_STOPWORDS_PATTERN = re.compile(
    r"\b(datos|resultado|obtener|procesar|archivo|lista|texto|cadena|numero|fecha|usuario|"
    r"clave|sesion|respuesta|peticion|mensaje|tipo|valor|estado|configuracion|ruta|directorio|"
    r"conexion|base_datos|tabla|fila|columna|registro|error|excepcion|funcion|clase|metodo|"
    r"propiedad|atributo|variable|constante|bucle|condicion|prueba|testear|validar|limpiar|"
    r"filtrar|ordenar|buscar|encontrar|guardar|leer|escribir|actualizar|borrar|eliminar)\b",
    re.IGNORECASE,
)


class EntropyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.entropy_hits = []

    def _check_identifier(self, name, node_type, lineno):
        if not name:
            return

        # Check specific spanish characters
        if SPANISH_CHARS_PATTERN.search(name):
            self.entropy_hits.append(
                {
                    "type": node_type,
                    "line": lineno,
                    "value": name,
                    "reason": "Spanish characters [áéíóúñ]",
                }
            )
            return

        # Check for spanglish or plain spanish words
        # Clean underscores to check words
        words = name.replace("_", " ")
        if SPANISH_STOPWORDS_PATTERN.search(words):
            self.entropy_hits.append(
                {
                    "type": node_type,
                    "line": lineno,
                    "value": name,
                    "reason": "Spanish semantic slop",
                }
            )

    def visit_ClassDef(self, node):
        self._check_identifier(node.name, "ClassDef", node.lineno)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._check_identifier(node.name, "FunctionDef", node.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_identifier(node.name, "AsyncFunctionDef", node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node):
        self._check_identifier(node.id, "Variable", node.lineno)
        self.generic_visit(node)

    def visit_arg(self, node):
        self._check_identifier(node.arg, "Argument", node.lineno)
        self.generic_visit(node)


def analyze_comments(filepath):
    hits = []
    try:
        with open(filepath, "rb") as f:
            tokens = tokenize.tokenize(f.readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    content = tok.string
                    if SPANISH_CHARS_PATTERN.search(content):
                        hits.append(
                            {
                                "type": "Comment",
                                "line": tok.start[0],
                                "value": content.strip(),
                                "reason": "Spanish characters [áéíóúñ]",
                            }
                        )
                elif tok.type == tokenize.STRING:
                    # Very basic check for docstrings, strings might be legit UI text
                    pass
    except Exception:  # noqa: BLE001
        # Ignore decoding or tokenization errors safely
        pass
    return hits


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "babylon60"
    report = {}

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, encoding="utf-8") as f:
                    source = f.read()
            except Exception:  # noqa: BLE001
                continue

            try:
                tree = ast.parse(source, filename=filepath)
            except SyntaxError:
                continue

            visitor = EntropyVisitor()
            visitor.visit(tree)

            # Extract comment entropy
            comment_hits = analyze_comments(filepath)

            all_hits = visitor.entropy_hits + comment_hits

            if all_hits:
                # Deduplicate by line and value to avoid explosion of Name nodes
                dedup = {}
                for hit in all_hits:
                    k = f"{hit['line']}_{hit['value']}"
                    if k not in dedup:
                        dedup[k] = hit

                report[filepath] = list(dedup.values())

    logging.getLogger(__name__).info(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
