# C5-REAL EXERGY CERTIFIED
from cortex.swarm.reviewer_agent import evaluate_diff

def test_reviewer_clean_diff() -> None:
    diff = "+++ src/main.py\n+ def clean_func(x: int) -> int:\n+     return x + 1"
    res = evaluate_diff(diff)
    assert res.startswith("PASS")

def test_reviewer_private_key_leak() -> None:
    diff = "+++ src/auth.py\n+ KEY = '-----BEGIN RSA PRIVATE KEY-----\\nMIIE...'"
    res = evaluate_diff(diff)
    assert res.startswith("REJECT")
    assert "Fuga de Clave Privada" in res

def test_reviewer_aws_key_leak() -> None:
    diff = "+++ src/cloud.py\n+ AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
    res = evaluate_diff(diff)
    assert res.startswith("REJECT")
    assert "Fuga de Secretos de AWS" in res

def test_reviewer_openai_key_leak() -> None:
    diff = "+++ src/llm.py\n+ OPENAI_KEY = 'sk-proj-123456789012345678901234567890'"
    res = evaluate_diff(diff)
    assert res.startswith("REJECT")
    assert "Fuga de Clave API de OpenAI" in res

def test_reviewer_bare_except() -> None:
    diff = "+++ src/utils.py\n+ try:\n+     do_something()\n+ except:\n+     pass"
    res = evaluate_diff(diff)
    assert res.startswith("REJECT")
    assert "Bare except pass" in res

def test_reviewer_eval_exec() -> None:
    diff = "+++ src/calc.py\n+ result = eval(user_input)"
    res = evaluate_diff(diff)
    assert res.startswith("REJECT")
    assert "eval/exec" in res
