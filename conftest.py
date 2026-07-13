# [C5-REAL] CORTEX Unified Namespace Pytest Conftest
import sys
import os

root_dir = os.path.abspath(os.path.dirname(__file__))
incoming_dir = os.path.join(root_dir, "_incoming_borjamoskv_20260713")

if incoming_dir not in sys.path:
    sys.path.insert(0, incoming_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
