# C5-REAL EXERGY CERTIFIED
import urllib.request, json
import time

modules = [
    "devsecops_attest", "cortex_env", "posthog", "setuptools", "numpy",
    "babylon60", "rich", "playwright", "strike_rs", "yaml", "pyaudio",
    "chromadb", "cryptography", "pytest", "numba", "bft_sqlite",
    "cortex_guard_core", "click", "python", "nacl", "agents"
]

for m in modules:
    try:
        req = urllib.request.urlopen(f"https://pypi.org/pypi/{m}/json")
        data = json.loads(req.read())
        desc = data["info"].get("summary", "")
        print(f"{m}: REGISTRADO | {desc}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"{m}: 404 LIBRE PARA SQUATTING")
    except Exception as e:
        print(f"{m}: ERROR {e}")
    time.sleep(0.1) # Be nice to PyPI
