# C5_IGNORE_NESTING
# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Zero-Trust Prompt Injection Sanitizer
Filtro de seguridad dinámico de múltiples vectores para auditar issues y comentarios entrantes.
"""

import re
import base64
from typing import Tuple, List

# Patrones explícitos de desvío de instrucciones (Jailbreak / System Override)
MALICIOUS_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"bypass\s+security", re.IGNORECASE),
    re.compile(r"reveal\s+(secret|token|password|key)", re.IGNORECASE),
    re.compile(r"<\s*/?\s*(system|user_request|user_input|instruction)\s*>", re.IGNORECASE),
    re.compile(r"\x1b\[[0-9;]*[mGKH]", re.IGNORECASE),  # Escape sequences ANSI
]

class ZeroTrustSanitizer:
    """Sanitizador determinista multivector para insumos de usuarios externos."""

    def __init__(self, max_length: int = 10000) -> None:
        self.max_length = max_length

    def check_length(self, input_text: str) -> bool:
        return len(input_text) <= self.max_length

    def check_base64_payloads(self, input_text: str) -> bool:
        """Busca y decodifica fragmentos base64 para inspección de firmas maliciosas ocultas."""
        b64_matches = re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", input_text)
        for match in b64_matches:
            try:
                decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                for pattern in MALICIOUS_PATTERNS:
                    if pattern.search(decoded):
                        return False
            except (ValueError, UnicodeDecodeError):
                continue
        return True

    def validate(self, input_text: str) -> Tuple[bool, str]:
        """
        Valida el input contra todos los vectores.
        Retorna (is_clean, reason).
        """
        if not self.check_length(input_text):
            return False, "EXCEEDS_MAX_LENGTH"

        for pattern in MALICIOUS_PATTERNS:
            if pattern.search(input_text):
                return False, f"PATTERN_MATCH:{pattern.pattern}"

        if not self.check_base64_payloads(input_text):
            return False, "BASE64_OBFUSCATED_INJECTION"

        return True, "CLEAN"

    def sanitize_str(self, input_text: str) -> str:
        """Limpia caracteres nulos y secuencias de control no imprimibles."""
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", input_text)
        return cleaned
