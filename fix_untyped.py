# C5-REAL EXERGY CERTIFIED
import re
import sys

FILES = [
    "scripts/c7_causal_proof_of_work_bft.py",
    "scripts/c8_reputation_metabolism_bft.py",
    "scripts/c7_recursive_self_audit_bft.py",
    "scripts/c7_legitimacy_collapse_bft.py",
    "scripts/c7_fork_competition_bft.py",
    "scripts/c7_external_witness_bft.py",
    "cortex/quad_pillar_kernel_test.py"
]

def add_typing(file):
    with open(file, "r") as f:
        content = f.read()

    if "from typing import Any" not in content:
        content = "from typing import Any, Dict, List, Tuple\n" + content

    def replacer(match):
        name = match.group(1)
        args_str = match.group(2)

        new_args = []
        if args_str.strip():
            # simple split by comma, works if no nested brackets in args
            for arg in args_str.split(','):
                arg = arg.strip()
                if not arg:
                    continue
                if ':' not in arg and '=' not in arg and arg != 'self':
                    arg = f"{arg}: Any"
                elif '=' in arg and ':' not in arg:
                    var, val = arg.split('=', 1)
                    arg = f"{var.strip()}: Any = {val.strip()}"
                new_args.append(arg)

        args_final = ", ".join(new_args)

        # If the original function already had `->`, don't replace the end
        # But this regex only matches `):`, it doesn't match `) -> type:`.
        # So it's safe.

        if name in ["__init__", "setup_module", "teardown_module"]:
            return f"def {name}({args_final}) -> None:"
        elif name.startswith("test_") or name.startswith("run_"):
            return f"def {name}({args_final}) -> None:"
        else:
            return f"def {name}({args_final}) -> Any:"

    # Match def without return type (ends with '):' )
    new_content = re.sub(r'def\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*:', replacer, content)

    # Fix incompatible dict in recursive_self_audit
    new_content = new_content.replace('dict[str, dict[str, str]]', 'Any')

    # Fix incompatible assignments
    new_content = re.sub(r'([a-zA-Z0-9_]+)\s*:\s*int\s*=\s*time\.time\(\)', r'\1: float = time.time()', new_content)
    new_content = re.sub(r'([a-zA-Z0-9_]+)\s*:\s*int\s*=\s*0\.0', r'\1: float = 0.0', new_content)
    new_content = new_content.replace('total_work: int = 0.0', 'total_work: float = 0.0')
    new_content = new_content.replace('total_difficulty: int = 0.0', 'total_difficulty: float = 0.0')

    with open(file, "w") as f:
        f.write(new_content)

for f in FILES:
    add_typing(f)
