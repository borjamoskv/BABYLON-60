import pathlib
import sys

# Basic sanity checks for the Continuous Commit Polisher daemon

def test_constants():
    from scripts.commit_polisher import POLL_INTERVAL, DEBOUNCE_TIME, REPO_ROOT
    assert isinstance(POLL_INTERVAL, int) and POLL_INTERVAL > 0
    assert isinstance(DEBOUNCE_TIME, int) and DEBOUNCE_TIME >= POLL_INTERVAL
    # REPO_ROOT should be the repository root (parent of 'scripts')
    expected_root = pathlib.Path(__file__).parents[1]
    assert REPO_ROOT == expected_root

def test_main_entrypoint(monkeypatch):
    # Ensure that running the script as __main__ does not raise immediately
    from importlib import reload
    module_path = 'scripts.commit_polisher'
    # Reload the module to execute top-level code safely (it just defines functions)
    module = reload(sys.modules[module_path])
    assert hasattr(module, 'main')
    # Do not actually start the infinite loop in test
    # Verify that main can be called and will raise SystemExit if not a git repo (mocking)
    def mock_exists(path):
        return False
    monkeypatch.setattr(pathlib.Path, 'exists', mock_exists)
    try:
        module.main()
    except SystemExit as e:
        assert e.code == 1
    else:
        raise AssertionError('Expected SystemExit when repo not found')
