# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import ast
import logging
import re
import urllib.parse
from typing import Any

logger = logging.getLogger("babylon60_extensions.security.t_cell")


class BabestuTCell:
    """
    LENS 4: ZERO TRUST.
    Static (AST-level) and heuristic O(1) scanner.
    Filters the injection before it reaches the vascular system (LUNGS/Landauer).
    """

    FORBIDDEN_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "subprocess",
        "os.system",
        "os.popen",
    }
    FORBIDDEN_IMPORTS = {"socket", "requests", "urllib", "http.client", "subprocess", "os", "sys"}

    # Expressions for obfuscation and steganography
    B64_HEURISTIC = re.compile(r"([A-Za-z0-9+/]{200,}={0,2})")
    HEX_HEURISTIC = re.compile(r"(\\x[0-9a-fA-F]{2}){15,}")

    @classmethod
    def analyze_python_ast(cls, code: str) -> tuple[bool, str]:
        """Converts to AST and searches for lethal vectors in O(N) of the nodes."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # If it's not even valid Python, we let it pass through the AST.
            # The LLM's semantic analyzer will handle it if it's garbage.
            return True, ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in cls.FORBIDDEN_CALLS:
                    return (
                        False,
                        f"Forbidden dynamic execution or system call: {node.func.id}()",
                    )
                if isinstance(node.func, ast.Attribute) and node.func.attr in cls.FORBIDDEN_CALLS:
                    return False, f"Forbidden attribute invocation: {node.func.attr}()"

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in cls.FORBIDDEN_IMPORTS:
                        return False, f"Forbidden network/weaponized import: {alias.name}"

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in cls.FORBIDDEN_IMPORTS:
                    return False, f"Forbidden relative/weaponized import: {node.module}"

        return True, ""

    @classmethod
    def scan_payload(cls, raw_text: str, source_url: str = "") -> dict[str, Any]:
        """
        O(1) entry point.
        1. Searches for superficial obfuscations (Base64, Hex).
        2. Extracts code blocks (Python).
        3. Performs AST autopsy.
        """
        parsed_url = urllib.parse.urlparse(source_url)
        hostname = parsed_url.hostname or ""
        # codeql[py/incomplete-url-substring-sanitization]
        is_youtube = (
            hostname == "youtube.com"
            or hostname.endswith(".youtube.com")
            or hostname == "youtu.be"
            or hostname.endswith(".youtu.be")
        )

        if not is_youtube and cls.B64_HEURISTIC.search(raw_text):
            return cls._verdict(
                "CONTAMINATED",
                90,
                "Base64_Obfuscation_Suspected",
                "Unusually long Base64 string detected.",
            )

        if cls.HEX_HEURISTIC.search(raw_text):
            return cls._verdict(
                "CONTAMINATED",
                95,
                "Hex_Obfuscation_Suspected",
                "Obfuscated HexByte sequence detected.",
            )

        python_blocks = re.findall(r"```python\n(.*?)\n```", raw_text, re.DOTALL | re.IGNORECASE)
        for idx, block in enumerate(python_blocks):
            is_safe, reason = cls.analyze_python_ast(block)
            if not is_safe:
                return cls._verdict(
                    "CONTAMINATED", 100, "AST_Static_Lethal_Vector", f"Block {idx}: {reason}"
                )

        return cls._verdict("CLEAN", 0, None, "Static AST and O(1) heuristics passed", raw_text)

    @staticmethod
    def _verdict(
        state: str,
        level: int,
        signature: str | None,
        reason: str,
        sanitized_content: str | None = None,
    ) -> dict[str, Any]:
        return {
            "state": state,
            "threat_level": level,
            "attack_signature": signature,
            "reason": reason,
            "sanitized_content": sanitized_content if state == "CLEAN" else None,
        }
