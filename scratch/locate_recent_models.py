import os
import time

base_path = "/Users/borjafernandezangulo/10_PROJECTS/"
recent_cutoff = time.time() - 7 * 24 * 3600 # 7 days ago

found_files = []

for root, dirs, files in os.walk(base_path):
    # limit depth to avoid wasting time
    depth = root[len(base_path):].count(os.sep)
    if depth > 4:
        dirs[:] = []
        continue
    
    # skip some huge dirs or hidden dirs
    if any(p in root for p in [".git", ".venv", "node_modules", "target", "build", "dist"]):
        continue

    for f in files:
        if f.endswith((".json", ".pt", ".onnx", ".bin", ".pkl", ".safetensors", ".pth", ".joblib")):
            fpath = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fpath)
                if mtime > recent_cutoff:
                    # check if the word "model" or "weight" is in the filename or if it's in a relevant path
                    if any(w in f.lower() or w in root.lower() for w in ["model", "weight", "train", "fit"]):
                        found_files.append((fpath, mtime))
            except Exception:
                pass

# Sort by modification time desc
found_files.sort(key=lambda x: x[1], reverse=True)

print("=== Found recent model-related files ===")
for path, mtime in found_files[:30]:
    print(f"{path} - Modified: {time.ctime(mtime)}")
