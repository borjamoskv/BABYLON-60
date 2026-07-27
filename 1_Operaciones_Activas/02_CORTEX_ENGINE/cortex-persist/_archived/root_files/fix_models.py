with open("babylon60/engine/cognitive/models.py") as f:
    m = f.readlines()
with open("babylon60/engine/flow/causality_models.py") as f:
    c = f.readlines()

# Quitar cabeceras y __all__ de models
new_lines = ["# [C5-REAL] Exergy-Maximized\n", "from __future__ import annotations\n"]
for line in m:
    if line.startswith("import ") or line.startswith("from "):
        if line not in new_lines:
            new_lines.append(line)
for line in c:
    if line.startswith("import ") or line.startswith("from "):
        if line not in new_lines:
            new_lines.append(line)

new_lines.append("\n__all__ = []\n\n")

for line in m:
    if not (line.startswith("import ") or line.startswith("from ") or line.startswith("__all__") or line.startswith("# ")):
        new_lines.append(line)

for line in c:
    if not (line.startswith("import ") or line.startswith("from ") or line.startswith("__all__") or line.startswith("# ")):
        new_lines.append(line)

with open("babylon60/types/core_models.py", "w") as f:
    f.writelines(new_lines)

reexport_models = """# [C5-REAL] Exergy-Maximized
from babylon60.types.core_models import Fact, row_to_fact, _parse_json_blob, _to_float, _extract_full_layout, _extract_rich_layout
__all__ = ["Fact", "row_to_fact"]
"""
with open("babylon60/engine/cognitive/models.py", "w") as f:
    f.write(reexport_models)

reexport_causality = """# [C5-REAL] Exergy-Maximized
from babylon60.types.core_models import EpistemicStatus, TruthScore, UtilityScore, Evidence, Claim, DecisionTrace, TaintStatus, Confidence, TaintReport, LedgerEvent, EDGE_DERIVED_FROM, EDGE_TRIGGERED_BY, EDGE_UPDATED_FROM, EDGE_TAINTED_BY, CONFIDENCE_ORDER, CONFIDENCE_LEVELS, _downgrade_confidence
"""
with open("babylon60/engine/flow/causality_models.py", "w") as f:
    f.write(reexport_causality)
