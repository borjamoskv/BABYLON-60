# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-docstring-logging
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import re
from pathlib import Path


def clean_docstrings():
    workspace = Path(__file__).parent.parent
    for folder in ["tools", "scripts"]:
        for file in (workspace / folder).rglob("*.py"):
            try:
                content = file.read_text(encoding="utf-8")
            except Exception:
                continue

            pattern = re.compile(r'^(?:#[^\n]*\n)*\s*"""(.*?)"""', re.DOTALL)
            match = pattern.match(content)
            if match and "import logging" in match.group(1):
                cleaned_doc = re.sub(
                    r"\s*import logging\s*\n?", "\n", match.group(1), count=1
                ).strip()

                def repl(
                    m: re.Match, content: str = content, cleaned_doc: str = cleaned_doc
                ) -> str:
                    prefix = content[: m.start(1)]
                    return f'{prefix}{cleaned_doc}\n"""'

                content_without_doc_import = pattern.sub(repl, content, count=1)
                # Check if import logging is already elsewhere in the file
                if "import logging" not in content_without_doc_import:
                    # Insert import logging after from __future__ if present, else after docstring
                    future_match = re.search(
                        r'^(?:#[^\n]*\n)*\s*"""[^\"]*"""\s*\n(from __future__ import [^\n]+\n)',
                        content_without_doc_import,
                        re.DOTALL,
                    )
                    if future_match:
                        insert_pos = future_match.end()
                        new_content = (
                            content_without_doc_import[:insert_pos]
                            + "\nimport logging\n"
                            + content_without_doc_import[insert_pos:]
                        )
                    else:
                        doc_end = pattern.match(content_without_doc_import).end()
                        new_content = (
                            content_without_doc_import[:doc_end]
                            + "\n\nimport logging\n"
                            + content_without_doc_import[doc_end:]
                        )
                else:
                    new_content = content_without_doc_import

                file.write_text(new_content, encoding="utf-8")
                print(f"Cleaned {file.relative_to(workspace)}")


if __name__ == "__main__":
    clean_docstrings()
