# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-belief-tests
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import re
from pathlib import Path

files = [
    "tests/cortex/extensions/hypervisor/test_graph_orphan.py",
    "tests/memory/test_scheduler.py",
    "tests/test_belief_object.py",
    "tests/test_cognitive_handoff.py",
    "tests/test_encb_v2/test_belief_object.py",
    "tests/test_encb_v2/test_merge.py",
]

for f_path in files:
    path = Path(f_path)
    if not path.exists():
        continue
    content = path.read_text()

    # We only want to replace content= with proposition= and status= with state=
    # if they are part of BeliefObject.
    # Since these test files mainly use BeliefObject and replace() on BeliefObject,
    # we can just blindly replace "content=" with "proposition=" and "status=" with "state="
    # but let's check if there are other uses.

    content = re.sub(r"\bcontent=", "proposition=", content)
    content = re.sub(r"\bstatus=", "state=", content)

    path.write_text(content)
logging.getLogger(__name__).info("Done")
