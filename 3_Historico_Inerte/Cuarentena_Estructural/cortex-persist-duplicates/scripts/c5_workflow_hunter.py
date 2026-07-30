# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-workflow-hunter
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import re

dead_workflows = []
for root, _, files in os.walk(".github/workflows"):
    for file in files:
        if file.endswith((".yml", ".yaml")):
            filepath = os.path.join(root, file)
            with open(filepath) as f:
                content = f.read()
                # Find all scripts referenced in the workflow
                scripts = re.findall(r"scripts/[a-zA-Z0-9_\-\./]+\.py", content)
                for script in scripts:
                    if not os.path.exists(script):
                        logging.getLogger(__name__).info(f"Workflow {filepath} references MISSING script {script}")
                        if filepath not in dead_workflows:
                            dead_workflows.append(filepath)

logging.getLogger(__name__).info("DEAD_WORKFLOWS:", dead_workflows)
