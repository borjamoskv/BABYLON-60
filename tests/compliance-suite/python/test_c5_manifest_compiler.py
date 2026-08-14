#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

COMPILER_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "c5_manifest_compiler.py"

def setup_adversarial_environment(base_dir: Path):
    """Injects maximum anergy into the test environment."""
    
    # 1. Nesting & Time (Python)
    py_anergy = base_dir / "bad_operations.py"
    py_anergy.write_text("""
import time
def deep_abyss():
    if True:
        if True:
            for i in range(10):
                while True:
                    if time.time() > 0:
                        print("Anergy!")
""")

    # 2. FFI (Rust)
    rs_anergy = base_dir / "bad_ffi.rs"
    rs_anergy.write_text("""
#[no_mangle]
pub extern "C" fn do_nothing() {}
""")

    # 3. Supply Chain (JSON)
    json_anergy = base_dir / "package.json"
    json_anergy.write_text("""
{
  "dependencies": {
    "leftpad": "^1.0.0"
  }
}
""")

    # 4. LaTeX (Markdown)
    md_anergy = base_dir / "docs.md"
    md_anergy.write_text(r"""
This is a formula: $$ H(X) = - \sum p(x) \log p(x) $$
And inline $x = y$.
""")

    # 5. Cargo (TOML)
    toml_anergy = base_dir / "Cargo.toml"
    toml_anergy.write_text("""
[dependencies]
crossbeam-epoch = "0.9"
""")

def run_stress_test():
    print("=== C5-REAL COMPILER STRESS TEST ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        setup_adversarial_environment(temp_path)
        
        print("[1] Running compiler against adversarial (anergic) environment...")
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, str(COMPILER_SCRIPT.resolve())], 
            cwd=temp_path, 
            capture_output=True, 
            text=True
        )
        
        output = result.stdout + result.stderr
        
        # Verify it fails
        assert result.returncode == 1, f"Expected compiler to fail (Exit 1), got {result.returncode}"
        
        # Verify it caught EVERYTHING
        assert "OPERACIONES_NESTING_01" in output, "Missed Nesting violation"
        assert "OPERACIONES_TIME_01" in output, "Missed Time violation"
        assert "SILICIO_FFI_01" in output, "Missed FFI #[no_mangle] violation"
        assert "REPOSITORIO_SUPPLY_01" in output, "Missed ^ version violation"
        assert "ESTETICA_LATEX_01" in output, "Missed LaTeX violation"
        assert "SILICIO_EBR_01" in output, "Missed crossbeam-epoch violation"
        
        print("✅ Compiler successfully intercepted ALL injected anergy vectors.")
        
        print("\n[2] Running compiler against pure environment...")
        # Clear dir
        for p in temp_path.iterdir():
            if p.is_file():
                p.unlink()
        
        result2 = subprocess.run(
            [sys.executable, str(COMPILER_SCRIPT.resolve())], 
            cwd=temp_path, 
            capture_output=True, 
            text=True
        )
        
        assert result2.returncode == 0, f"Expected pure env to pass, but it failed:\n{result2.stdout}"
        print("✅ Compiler successfully passed on zero-anergy environment.")
        
        print("\n🏆 STRESS TEST COMPLETED SUCCESSFULLY. The C5-REAL Compiler is impenetrable.")

if __name__ == "__main__":
    run_stress_test()
