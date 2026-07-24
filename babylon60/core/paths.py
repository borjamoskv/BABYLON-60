# [C5-REAL] Exergy-Maximized Paths Configuration
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CORTEX_DIR = Path(os.getenv("CORTEX_DIR", "~/.babylon60")).expanduser()
CORTEX_DB = Path(os.getenv("CORTEX_DB_PATH", CORTEX_DIR / "cortex.db")).expanduser()
SKILLS_DIR = Path(os.getenv("SKILLS_DIR", "~/.gemini/antigravity/skills")).expanduser()
AGENT_DIR = Path(os.getenv("AGENT_DIR", "~/.agents")).expanduser()
DAEMON_CONFIG_FILE = CORTEX_DIR / "daemon.json"
DAEMON_STATUS_FILE = CORTEX_DIR / "daemon_status.json"

__all__ = [
    "ROOT_DIR",
    "CORTEX_DIR",
    "CORTEX_DB",
    "SKILLS_DIR",
    "AGENT_DIR",
    "DAEMON_CONFIG_FILE",
    "DAEMON_STATUS_FILE",
]
