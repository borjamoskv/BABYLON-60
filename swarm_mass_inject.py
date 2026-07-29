# C5-REAL EXERGY CERTIFIED
import os
import json
import uuid
import sys

try:
    import redis
except ImportError:
    print("Redis python package not installed. Installing it...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
    import redis

def find_binaries(max_count=10000):
    targets = []
    # Directories to scan for Mach-O or ASAR bundles
    scan_dirs = ["/Applications", "/usr/bin"]
    for d in scan_dirs:
        for root, dirs, files in os.walk(d):
            for f in files:
                # We'll just grab everything that lacks an extension or is .app, .asar
                if not f.startswith(".") and (not "." in f or f.endswith(".asar") or f.endswith(".dylib")):
                    full_path = os.path.join(root, f)
                    targets.append(full_path)
                    if len(targets) >= max_count:
                        return targets
    return targets

def main():
    r = redis.Redis(host='localhost', port=6379, db=0)

    try:
        r.ping()
    except redis.ConnectionError:
        print("ERROR: Redis server is not running on localhost:6379.")
        return

    print("Locating binaries for analysis...")
    binaries = find_binaries(10000)
    print(f"Found {len(binaries)} targets.")

    print("Flushing existing tasks...")
    r.delete('swarm:tasks')

    print("Injecting tasks into Swarm BFT broker...")
    pipe = r.pipeline()
    for bin_path in binaries:
        task = {
            "task_id": str(uuid.uuid4()),
            "type": "reverse_engineering",
            "target": bin_path,
            "instructions": "Run nm, otool, strings. Extract Endpoints and Protocols. Distill CoT.",
            "status": "pending"
        }
        pipe.lpush('swarm:tasks', json.dumps(task))

    pipe.execute()
    count = r.llen('swarm:tasks')
    print(f"Successfully injected {count} tasks to swarm:tasks queue.")

if __name__ == "__main__":
    main()
