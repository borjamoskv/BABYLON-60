import importlib.util
import os
import sys
import tempfile
import threading
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).absolute().parents[5]
real_open = os.open
lock = threading.Lock()
logs = []


def op(path, flags, *a, **kw):
    try:
        return real_open(path, flags, *a, **kw)
    except OSError as e:
        with lock:
            r = {"path": str(path), "flags": flags, "dir_fd": kw.get("dir_fd"), "error": repr(e)}
            if "dir_fd" in kw:
                try:
                    r["dir_stat"] = list(os.fstat(kw["dir_fd"]))
                    r["entries"] = os.listdir(kw["dir_fd"])
                except OSError as s:
                    r["diagnostic_error"] = repr(s)
            logs.append(r)
        raise


os.open = op
with tempfile.TemporaryDirectory(prefix="b60-review-queue-") as tmp:
    root = Path(tmp).resolve()
    os.environ["HOME"] = str(root)
    hosts = []
    for i in range(3):
        spec = importlib.util.spec_from_file_location(
            "probe_native_" + str(i), ROOT / "scripts/c5_cli/moskv_native_host.py"
        )
        m = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = m
        spec.loader.exec_module(m)
        m.QUEUE_FILE = root / "prompts.json"
        hosts.append(m)
    with ThreadPoolExecutor(max_workers=6) as pool:
        for count in (6, 6, 50):
            futures = [pool.submit(hosts[i % 3].enqueue_prompt, str(i)) for i in range(count)]
            errors = []
            for f in futures:
                try:
                    f.result()
                except OSError as e:
                    errors.append(repr(e))
            if errors:
                print("ERRORS", errors)
            print("queue_len", len(hosts[0].queued_prompts()))
            for i in range(count):
                hosts[i % 3].get_next_prompt()
    print(json.dumps(logs, indent=2))
