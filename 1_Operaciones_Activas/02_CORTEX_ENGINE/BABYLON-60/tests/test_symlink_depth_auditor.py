# C5-REAL EXERGY CERTIFIED
import os
import sys
import importlib.util
import types
from pathlib import Path

_script_path = Path(__file__).resolve().parent.parent / "scripts" / "symlink_depth_auditor.py"
_spec = importlib.util.spec_from_file_location("scripts.symlink_depth_auditor", _script_path)
_mod = importlib.util.module_from_spec(_spec)

if "scripts" not in sys.modules:
    pkg = types.ModuleType("scripts")
    pkg.__path__ = [str(_script_path.parent)]
    sys.modules["scripts"] = pkg
else:
    if not hasattr(sys.modules["scripts"], "__path__"):
        sys.modules["scripts"].__path__ = [str(_script_path.parent)]

sys.modules["scripts.symlink_depth_auditor"] = _mod
sys.modules["symlink_depth_auditor"] = _mod
_spec.loader.exec_module(_mod)

audit_symlinks = _mod.audit_symlinks
main = _mod.main

def test_audit_symlinks_valid(tmp_path):
    # Create valid symlink with ../..
    target = "../../sibling/path"
    link = tmp_path / "link1"
    os.symlink(target, link)
    violations = audit_symlinks(tmp_path)
    assert len(violations) == 0

def test_audit_symlinks_invalid(tmp_path):
    # Create invalid symlink with ../
    target = "../sibling/path"
    link = tmp_path / "link2"
    os.symlink(target, link)
    violations = audit_symlinks(tmp_path)
    assert len(violations) == 1
    assert violations[0][0] == link

def test_main_pass(tmp_path):
    valid_link = tmp_path / "link_valid"
    os.symlink("../../sibling/file", valid_link)
    # Mock REPO_ROOT in script
    import scripts.symlink_depth_auditor as module
    original_root = module.REPO_ROOT
    try:
        module.REPO_ROOT = tmp_path
        assert main() == 0
    finally:
        module.REPO_ROOT = original_root
