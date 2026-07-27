import logging
import re


def fix(filepath):
    with open(filepath) as f:
        content = f.read()

    # The regex:
    # <<<<<<< HEAD\n
    # followed by anything (non-greedy)
    # \n=======\n
    # followed by anything (non-greedy)
    # \n>>>>>>> [anything until newline]\n
    pattern = re.compile(r"<<<<<<< HEAD\n.*?\n=======\n(.*?)\n>>>>>>>[^\n]*\n", re.DOTALL)

    new_content, count = pattern.subn(r"\1\n", content)

    with open(filepath, "w") as f:
        f.write(new_content)
    logging.getLogger(__name__).info(f"Fixed {count} conflicts in {filepath}")


fix("~/30_BABYLON60/babylon60/engine/__init__.py")
fix("~/30_BABYLON60/babylon60/engine/mutation_engine.py")
