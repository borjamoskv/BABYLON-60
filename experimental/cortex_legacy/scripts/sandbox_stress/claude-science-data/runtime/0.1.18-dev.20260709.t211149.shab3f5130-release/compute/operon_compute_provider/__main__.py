"""Generic entrypoint — replaces per-provider helper.py/bootstrap.py.

    python -I .../operon_compute_provider/__main__.py oneshot <provider.py> <op> <stage> <expectConfined>
    python -I .../operon_compute_provider/__main__.py repl    <provider.py>

Invoked as a script (not -m) because -I strips PYTHONPATH/cwd from sys.path,
so this file inserts the package's parent only — provider.py is loaded via
spec_from_file_location, so the skill dir is never on sys.path and unverified
sibling .py files there cannot shadow stdlib or third-party imports."""
import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_here))

from operon_compute_provider import ByocResident

mode, provider_py, *rest = sys.argv[1:]

spec = importlib.util.spec_from_file_location("_byoc_provider", provider_py)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

r = ByocResident(mod.PROVIDER(repl=(mode == "repl")))
if mode == "repl":
    r.run_repl()
else:


    r.run_oneshot([provider_py, *rest])
