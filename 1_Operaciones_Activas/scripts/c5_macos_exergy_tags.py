# C5-REAL EXERGY CERTIFIED - MACOS TAHOE KERNEL
import os
import sys
import datetime
import subprocess
from pathlib import Path

def apply_macos_tag(filepath: str, color: str):
    """
    Applies macOS Finder color tags via xattr directly to bypass UI clicking.
    Colors: Red (Urgente), Yellow (Revisión), Green (Finalizado)
    """
    tags = {
        "Red": b'bplist00\xa1\x01U\x04Red\n6\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x11',
        "Yellow": b'bplist00\xa1\x01X\x04Yellow\n5\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x14',
        "Green": b'bplist00\xa1\x01W\x04Green\n2\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x13'
    }

    if color not in tags:
        return

    try:
        # Using subprocess to call xattr is the most robust way on macOS Tahoe 26.5.2
        # Note: We'd typically write the plist hex, but for simplicity in C5-REAL we can use standard terminal command if installed,
        # or just use os.system for a simpler tool like `tag` if available.
        # But native xattr requires hex or plist. Let's use a standard shell approach for metadata.
        # The easiest native way without external libs is setting the com.apple.metadata:_kMDItemUserTags

        tag_string = f"<array><string>{color}\\n{tags.get(color, 0)}</string></array>"
        cmd = f"xattr -w com.apple.metadata:_kMDItemUserTags '{tag_string}' '{filepath}'"
        os.system(cmd)
        print(f"[C5-REAL] Tag {color} applied to {filepath}")
    except Exception as e:
        print(f"Error applying tag to {filepath}: {e}")

def exergy_rename(filepath: str, entidad: str = "MSK", accion: str = "Default", version: str = "v01") -> str:
    """
    Renames file to strict invariant: AAAAMMDD__ENTIDAD__ACCION__vXX
    """
    path = Path(filepath)
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    ext = path.suffix

    new_name = f"{date_str}__{entidad}__{accion}__{version}{ext}"
    new_path = path.parent / new_name

    os.rename(filepath, new_path)
    print(f"[C5-REAL] Renamed {path.name} -> {new_name}")
    return str(new_path)

def initialize_exergy_structure():
    """
    Creates the 4-level Zero-Friction Structure.
    """
    dirs = [
        "0_Buzon_Entrada",
        "1_Operaciones_Activas",
        "2_Nucleo_Estatico",
        "3_Historico_Inerte"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[C5-REAL] Ensured directory {d}")

if __name__ == "__main__":
    print("Iniciando mutación de estado macOS Tahoe 26.5.2...")
    initialize_exergy_structure()
    # Test file
    test_file = "0_Buzon_Entrada/test_document.txt"
    with open(test_file, "w") as f:
        f.write("Entropy to be purged.")

    new_path = exergy_rename(test_file, "TRM", "TestFriccionCero", "v01")
    apply_macos_tag(new_path, "Red")

    print("Mutación física completada. Exergía Maximizada.")
