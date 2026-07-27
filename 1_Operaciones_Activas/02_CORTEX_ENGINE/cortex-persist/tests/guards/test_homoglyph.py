import pytest
import ast
from babylon60.guards.homoglyph import cassandra_validate_identifiers, SecurityViolation


def test_vector1_homoglyph_attack_rejected():
    code = """
def lеa_omega_purge():
    pass
"""
    tree = ast.parse(code)
    with pytest.raises(SecurityViolation, match="HOMOGLYPH_ATTACK"):
        cassandra_validate_identifiers(tree)


def test_vector1_clean_ascii_accepted():
    code = """
def lea_omega_purge():
    x = 100
    return x
"""
    tree = ast.parse(code)
    cassandra_validate_identifiers(tree)
