import py_compile
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parent.parent
TRACKED_DIRS = ('cli', 'core', 'bft', 'analysis', 'adapters', 'compiler', 'contracts', 'cortex', 'scripts', 'tests')
EXCLUDED_PARTS = {'__pycache__', 'node_modules', 'fable_modules', 'bin', 'obj'}

def _tracked_python_files() -> list[Path]:
    files: list[Path] = []
    for dirname in TRACKED_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob('*.py')):
            if EXCLUDED_PARTS.isdisjoint(path.parts):
                files.append(path)
    files.extend(sorted(ROOT.glob('*.py')))
    return files

@pytest.mark.parametrize('path', _tracked_python_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_module_compiles(path: Path) -> None:
    py_compile.compile(str(path), doraise=True)