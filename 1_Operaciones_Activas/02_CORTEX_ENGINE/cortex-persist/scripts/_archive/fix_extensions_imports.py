import logging
import os
import re

EXTENSIONS = [
    "adk",
    "aether",
    "agent",
    "agents",
    "alma",
    "axioms",
    "bci",
    "browser",
    "causality",
    "context",
    "cuatrida",
    "daemon",
    "episodic",
    "evolution",
    "federation",
    "fingerprint",
    "gate",
    "genesis",
    "git",
    "ha",
    "health",
    "hive",
    "hypervisor",
    "immune",
    "interfaces",
    "langbase",
    "launchpad",
    "llm",
    "manifold",
    "market_maker",
    "mejoralo",
    "metering",
    "moltbook",
    "music_engine",
    "nexus",
    "notifications",
    "perception",
    "platform",
    "policy",
    "protocols",
    "red_team",
    "revenue",
    "sap",
    "scraper",
    "security",
    "shannon",
    "signals",
    "skills",
    "songlines",
    "sovereign",
    "substrate",
    "swarm",
    "sync",
    "thinking",
    "timing",
    "training",
    "trust",
    "ttt",
    "ui",
    "ui_control",
    "vex",
    "wealth",
    "web3",
    "zkortex",
]


def process_file(filepath):
    with open(filepath) as f:
        content = f.read()

    original = content
    for ext in EXTENSIONS:
        # Match `from babylon60.EXTENSION` or `import babylon60.EXTENSION`
        # Need to be careful about word boundaries so we don't match partials.
        content = re.sub(rf"from babylon60\.{ext}\b", rf"from babylon60.extensions.{ext}", content)
        content = re.sub(
            rf"import babylon60\.{ext}\b", rf"import babylon60.extensions.{ext}", content
        )
        # Also handle multiline imports or deeper imports
        # Actually \b takes care of `from babylon60.extensions.skills.xxx import ...`

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return True
    return False


root_dirs = ["babylon60", "tests", "scripts"]
modified = 0
for d in root_dirs:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                if process_file(path):
                    modified += 1
                    logging.getLogger(__name__).info(f"Modified {path}")
logging.getLogger(__name__).info(f"Total modified: {modified}")
