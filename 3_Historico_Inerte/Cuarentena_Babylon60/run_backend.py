# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Launcher script for the BABYLON60 IDE FastAPI backend.
"""
import os
import sys
import subprocess
import signal

# Ensure we are in the correct directory
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

# Add root directory to PYTHONPATH so backend can resolve babylon60 packages
os.environ["PYTHONPATH"] = f"{root_dir}:{os.environ.get('PYTHONPATH', '')}"

print("🚀 Igniting BABYLON60 IDE FastAPI Backend...")
print("🌐 Address: http://127.0.0.1:8000")

# Run uvicorn pointing to the backend module
try:
    venv_python = os.path.join(root_dir, ".venv", "bin", "python")
    python_exec = venv_python if os.path.exists(venv_python) else "python3"

    cmd = [
        python_exec, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
        "--reload-dir", "backend"
    ]

    # We execute uvicorn inside babylon60-ide/ directory
    subprocess.run(cmd, cwd=os.path.join(root_dir, "babylon60-ide"))
except KeyboardInterrupt:
    print("\n🛑 Backend halted by Operator.")
    sys.exit(0)
except (OSError, RuntimeError) as e:
    print(f"\n❌ Failed to launch backend: {e}")
    os.kill(os.getpid(), signal.SIGKILL)
