# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-provenance
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import re
from pathlib import Path

content = Path("tests/test_belief_object.py").read_text()

# Remove ProvenanceChain, ProvenanceEntry imports
content = re.sub(r"^\s*ProvenanceChain,\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^\s*ProvenanceEntry,\n", "", content, flags=re.MULTILINE)

# Add ProvenanceEnvelope if not there
if "ProvenanceEnvelope" not in content:
    content = re.sub(
        r"(from babylon60.extensions.hypervisor.belief_object import \()",
        r"\1\n    ProvenanceEnvelope,",
        content,
    )

# Replace the classes
content = re.sub(
    r"class TestProvenanceEntry:.*?class TestProvenanceChain:.*?(?=# ─── BeliefObject ───)",
    "",
    content,
    flags=re.DOTALL,
)

# Add a simple TestProvenanceEnvelope
replacement = """# ─── ProvenanceEnvelope ───────────────────────────────────────────────────────

class TestProvenanceEnvelope:
    def test_default_initialization(self):
        env = ProvenanceEnvelope()
        assert env.source_type == "agent"
        assert env.cortex_taint == "taint:system:0000:none:000"

    def test_custom_initialization(self):
        env = ProvenanceEnvelope(
            source_type="human",
            signer_id="operator",
            cortex_taint="taint:operator:0000:none:123"
        )
        assert env.source_type == "human"
        assert env.signer_id == "operator"

"""
content = re.sub(r"(?=# ─── BeliefObject ───)", replacement, content)

# Fix any instances of ProvenanceChain / ProvenanceEntry being used in the rest of the file
# "provenance = ProvenanceChain(entries=(entry,))"
content = re.sub(
    r"entry = ProvenanceEntry\([^)]*\)\s*provenance = ProvenanceChain\(entries=\(entry,\)\)",
    'provenance = ProvenanceEnvelope(source_type="agent", signer_id="system")',
    content,
    flags=re.DOTALL,
)

Path("tests/test_belief_object.py").write_text(content)
logging.getLogger(__name__).info("Done test_belief_object.py")
