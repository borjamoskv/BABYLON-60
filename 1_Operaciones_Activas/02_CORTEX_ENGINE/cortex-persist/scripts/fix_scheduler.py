# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-scheduler
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import re
from pathlib import Path

content = Path("tests/memory/test_scheduler.py").read_text()

# Fix MockBelief definition
content = re.sub(r'content: str = ""', 'proposition: str = ""', content)

# Also test_real_belief_object_integration failed because:
# TypeError: BeliefObject.__init__() got an unexpected keyword argument 'confidence'
# Need to replace confidence= with confidence_score= for BeliefObject
content = re.sub(
    r"confidence=BeliefConfidence\.", "confidence_score=0.9, # BeliefConfidence.", content
)

Path("tests/memory/test_scheduler.py").write_text(content)
