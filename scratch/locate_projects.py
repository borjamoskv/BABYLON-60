import os
import time

base_path = "/Users/borjafernandezangulo/10_PROJECTS/"
target_name = "apex_trials"
target_file = "fit_rolling_window.py"

found = []

for root, dirs, files in os.walk(base_path):
    # limit depth
    depth = root[len(base_path):].count(os.sep)
    if depth > 4:
        # skip deep dirs to avoid scanning node_modules or envs
        dirs[:] = []
        continue
    
    # check for targets
    if target_name in dirs:
        found.append(os.path.join(root, target_name))
    if target_file in files:
        found.append(os.path.join(root, target_file))

print("=== Found targets ===")
for f in found:
    print(f)
