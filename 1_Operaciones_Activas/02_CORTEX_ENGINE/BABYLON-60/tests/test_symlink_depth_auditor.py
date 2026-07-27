# C5-REAL EXERGY CERTIFIED
import os
from scripts.symlink_depth_auditor import audit_symlinks, main

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
