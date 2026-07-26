# C5-REAL EXERGY CERTIFIED
# C5-REAL EMPIRICAL TEST HARNESS FOR CORTEX PURGE
import sys
import os
import tempfile

PROJECT_ROOT = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.cortex_purge import is_purgeable_zero_operator, _obliterate_node_file

def run_empirical_assertions():
    print("==================================================")
    print("=== EMPIRICAL CHALLENGE: IS_PURGEABLE ASSERTIONS ===")
    print("==================================================")

    # 1. Active source files MUST return False (NEVER PURGEABLE)
    protected_test_cases = [
        "strike-rs/src/lib.rs",
        "src-tauri/src/lib.rs",
        "cortex/cortex_purge.py",
        "scripts/cortex_purge.py",
        "scripts/30_test_pytest.py",
        "scripts/40_stress_db.py",
        "src/main.rs",
        "axioms/foundation.rs",
        "some_dir/foo.py",
        "another_dir/bar.rs",
        "frontend/app.ts",
        "config.json",
    ]

    for path in protected_test_cases:
        res = is_purgeable_zero_operator(path)
        assert res is False, f"CRITICAL FAILURE: {path} was marked as purgeable!"
        print(f"✅ PROTECTED: {path} -> is_purgeable={res}")

    # 2. Disposable temporary/cache files SHOULD return True
    purgeable_test_cases = [
        "/tmp/c5_test_file.tmp",
        "scratch/temp_scratchpad.log",
        "module/__pycache__/module.cpython-312.pyc",
        "project/.pytest_cache/README.txt",
    ]

    for path in purgeable_test_cases:
        res = is_purgeable_zero_operator(path)
        assert res is True, f"FAILURE: Disposable path {path} was not marked as purgeable!"
        print(f"✅ PURGEABLE: {path} -> is_purgeable={res}")

    # 3. Test _obliterate_node_file on actual temporary test file vs mock active source file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fake active file in protected dir
        fake_protected_dir = os.path.join(tmpdir, "strike-rs", "src")
        os.makedirs(fake_protected_dir, exist_ok=True)
        fake_source_file = os.path.join(fake_protected_dir, "lib.rs")
        with open(fake_source_file, "w") as f:
            f.write("// active source")

        rel_protected_path = os.path.relpath(fake_source_file, tmpdir)
        obliterate_res = _obliterate_node_file(fake_source_file, rel_protected_path)
        assert obliterate_res is False, "CRITICAL: _obliterate_node_file attempted to remove protected file!"
        assert os.path.exists(fake_source_file), "CRITICAL: protected file was deleted physically!"
        print(f"✅ OBLITERATE BLOCKED ON PROTECTED SOURCE: {rel_protected_path}")

        # Fake disposable cache file
        fake_cache_dir = os.path.join(tmpdir, "scratch")
        os.makedirs(fake_cache_dir, exist_ok=True)
        fake_temp_file = os.path.join(fake_cache_dir, "temp_junk.txt")
        with open(fake_temp_file, "w") as f:
            f.write("junk")

        rel_temp_path = os.path.relpath(fake_temp_file, tmpdir)
        obliterate_temp_res = _obliterate_node_file(fake_temp_file, rel_temp_path)
        assert obliterate_temp_res is True, "FAILURE: _obliterate_node_file failed to remove disposable temp file!"
        assert not os.path.exists(fake_temp_file), "FAILURE: disposable temp file still exists!"
        print(f"✅ OBLITERATE ALLOWED ON DISPOSABLE TEMP: {rel_temp_path}")

    print("\n🎉 ALL EMPIRICAL ASSERTIONS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    run_empirical_assertions()
