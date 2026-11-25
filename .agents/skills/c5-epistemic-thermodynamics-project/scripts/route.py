#!/usr/bin/env python3
# Generated from tools/skill_library/router.py; edit the canonical source.
import runpy
from pathlib import Path
import sys
hub = Path(__file__).absolute().parent.parent
sys.argv.extend(['--hub-root', str(hub)])
runpy.run_path(str(hub.parent / '_skill_router.py'), run_name='__main__')
