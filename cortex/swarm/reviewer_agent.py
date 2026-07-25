# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Adversarial Reviewer Agent
Prompt estricto y escáner estático adversario para la auditoría de diffs y PRs.
"""

import re
from typing import List, Tuple

SYSTEM_PROMPT = """
Eres un revisor de código senior paranoico operando bajo el protocolo C5-REAL de MOSKV-1.
Tu único objetivo es detectar entropía, vulnerabilidades y violaciones del BFT Ledger:
- Inyección SQL, XSS, RCE.
- Fugas de memoria o manejo de excepciones nulo (bare excepts).
- Dependencias maliciosas o ejecuciones dinámicas (eval/exec).
- Secretos expuestos o private keys.
- Incumplimiento de tipado estricto (mypy) o asimetrías termodinámicas.

Si detectas cualquier riesgo: RECHAZA incondicionalmente con la palabra "REJECT" y justifica en YAML causal.
Si el diff está limpio y los tests validan la exergía: RESPONDE con "PASS: [razón breve]" y la aserción de exergía.

Prohibido sugerir mejoras estéticas (Green Theater). Solo evalúa seguridad estructural y termodinámica del estado.
"""

ADVERSARIAL_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"-----BEGIN\s+(?:[A-Z0-9-]+\s+)?PRIVATE\s+KEY-----", re.IGNORECASE),
        "Fuga de Clave Privada detectada",
    ),
    (
        re.compile(
            r"(AWS_SECRET_ACCESS_KEY|aws_secret_key)\s*=\s*['\"][A-Za-z0-9/+=]{10,}['\"]",
            re.IGNORECASE,
        ),
        "Fuga de Secretos de AWS detectada",
    ),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "Fuga de Clave API de OpenAI/LLM detectada"),
    (
        re.compile(r"\b(password|secret|passwd|api_key)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
        "Hardcoding de Credenciales detectado",
    ),
    (
        re.compile(r"except\s*:\s*(\n\+?\s*)?(pass|\.\.\.)", re.MULTILINE),
        "Captura nula de excepciones (Bare except pass) detectada",
    ),
    (
        re.compile(r"\b(eval|exec)\s*\("),
        "Inyección de ejecución dinámica no confiable (eval/exec) detectada",
    ),
    (re.compile(r"\bos\.system\s*\("), "Llamada insegura os.system() detectada"),
]


def evaluate_diff(diff_content: str) -> str:
    """Ejecuta una evaluación adversaria estática y de modelo sobre el diff recibido."""
    for pattern, description in ADVERSARIAL_PATTERNS:
        if pattern.search(diff_content):
            return f"REJECT: {description} en el diff."

    return "PASS: Estructura cristalizada. Cero anergía detectada."
