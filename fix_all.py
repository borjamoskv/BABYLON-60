import re
from pathlib import Path


def replace_in_file(path, old, new):
    p = Path(path)
    if p.exists():
        p.write_text(p.read_text().replace(old, new))

def regex_replace_in_file(path, pattern, repl):
    p = Path(path)
    if p.exists():
        p.write_text(re.sub(pattern, repl, p.read_text()))

# Fix INTEGER
replace_in_file("babylon60/genomics/adt.py", "INTEGER", "int")
replace_in_file("babylon60/genomics/models.py", "INTEGER", "int")

# Fix Union
regex_replace_in_file("babylon60/genomics/adt.py", r"Union\[(.*?), (.*?)\]", r"\1 | \2")
regex_replace_in_file("babylon60/types/algebraic.py", r"Union\[(.*?), (.*?)\]", r"\1 | \2")
regex_replace_in_file("babylon60/genomics/adt.py", r"Union\[(.*?), (.*?), (.*?)\]", r"\1 | \2 | \3")
regex_replace_in_file("babylon60/genomics/adt.py", r"Union\[(.*?), (.*?), (.*?), (.*?)\]", r"\1 | \2 | \3 | \4")

# Fix B904
regex_replace_in_file("babylon60/core/moskv_kernel.py", r"except \(sqlite3\.DatabaseError, OSError, ValueError\):", r"except (sqlite3.DatabaseError, OSError, ValueError) as e:")
regex_replace_in_file("babylon60/core/moskv_kernel.py", r'raise RuntimeError\("FAIL-FAST: Fallo catastrófico en boot BFT."\)', r'raise RuntimeError("FAIL-FAST: Fallo catastrófico en boot BFT.") from e')

regex_replace_in_file("babylon60/core/moskv_kernel.py", r"except sqlite3\.DatabaseError:", r"except sqlite3.DatabaseError as e:")
regex_replace_in_file("babylon60/core/moskv_kernel.py", r'raise RuntimeError\("FAIL-FAST: BFT Ledger corrompido."\)', r'raise RuntimeError("FAIL-FAST: BFT Ledger corrompido.") from e')

regex_replace_in_file("babylon60/core/thermo_ast_pruner.py", r"except \(OSError, SyntaxError, ValueError, AttributeError, TypeError\):", r"except (OSError, SyntaxError, ValueError, AttributeError, TypeError) as e:")
regex_replace_in_file("babylon60/core/thermo_ast_pruner.py", r'raise RuntimeError\("FAIL-FAST: General Exception intercepted."\)', r'raise RuntimeError("FAIL-FAST: General Exception intercepted.") from e')

regex_replace_in_file("babylon60/crypto/keys.py", r'raise ValueError\("Key must be an Ed25519PrivateKey"\)', r'raise ValueError("Key must be an Ed25519PrivateKey") from None')
regex_replace_in_file("babylon60/crypto/keys.py", r'raise ValueError\("Key must be an Ed25519PublicKey"\)', r'raise ValueError("Key must be an Ed25519PublicKey") from None')

regex_replace_in_file("babylon60/guards/ast_sandbox.py", r'raise SecurityError\(f"Syntax error \(safe\): \{e\}"\)', r'raise SecurityError(f"Syntax error (safe): {e}") from e')

# Fix B008
regex_replace_in_file("babylon60/utils/pulmones.py", r"db_path: Path = Path\.home\(\) / \".cortex\" / \"pulmones\.db\"", r"db_path: Path | None = None")
regex_replace_in_file("babylon60/utils/pulmones.py", r"self\.db_path = db_path", r"self.db_path = db_path or Path.home() / '.cortex' / 'pulmones.db'")

regex_replace_in_file("babylon60/utils/pulmones_worker.py", r"db_path: Path = Path\.home\(\) / \".cortex\" / \"pulmones\.db\"", r"db_path: Path | None = None")
regex_replace_in_file("babylon60/utils/pulmones_worker.py", r"self\.db_path = db_path", r"self.db_path = db_path or Path.home() / '.cortex' / 'pulmones.db'")

# Fix E402 patch.py
regex_replace_in_file("patch.py", r"import re\n", "")
p = Path("patch.py")
if p.exists():
    p.write_text("import re\n" + p.read_text())

# Fix crypto init E402
replace_in_file("babylon60/crypto/__init__.py", "]\nfrom .rfc3161 import RFC3161Client", "]\n# noqa: E402\nfrom .rfc3161 import RFC3161Client")

# Fix assert False
replace_in_file("scripts/c5_logos_ethos_ship_engine.py", "assert False, 'Should have rejected C4_Simulated_Buffer'", "raise AssertionError('Should have rejected C4_Simulated_Buffer')")

