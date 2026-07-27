# C5-REAL EXERGY CERTIFIED - BATCH MAPPER & SYMLINK TRANSDUCER
import os
import shutil

def create_symlink(target, link_name):
    """
    Ley del Enlace Único: Creates a symlink to preserve compiler/AST invariants
    while physically storing the data in the Exergy-Maximized taxonomy.
    """
    if os.path.islink(link_name):
        os.remove(link_name)
    elif os.path.exists(link_name):
        shutil.rmtree(link_name)

    os.symlink(target, link_name)
    print(f"[C5-REAL] Symlink created: {link_name} -> {target}")

def apply_macos_tag(filepath: str, color: str):
    tags = {
        "Red": b'bplist00\xa1\x01U\x04Red\n6\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x11',
        "Yellow": b'bplist00\xa1\x01X\x04Yellow\n5\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x14',
        "Green": b'bplist00\xa1\x01W\x04Green\n2\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x13'
    }
    if color not in tags: return
    try:
        tag_string = f"<array><string>{color}\\n{tags.get(color, 0)}</string></array>"
        cmd = f"xattr -w com.apple.metadata:_kMDItemUserTags '{tag_string}' '{filepath}'"
        os.system(cmd)
    except:
        pass

def process_mapping():
    mappings = {
        "1_Operaciones_Activas": [
            "scripts", "src", "src-tauri", "strike-rs", "portal", "cortex", "cmd", "agents", "laboratory", "SUBSTACK"
        ],
        "2_Nucleo_Estatico": [
            "docs", "axioms", "primitives", "ontology", "assets"
        ],
        "3_Historico_Inerte": [
            "audits", "ledgers", "house_remotion_project"
        ],
        "0_Buzon_Entrada": [
            "scratch", "tmp_chroma_pkg", "tmp_fastapi_pkg"
        ]
    }

    colors = {
        "0_Buzon_Entrada": "Red",
        "1_Operaciones_Activas": "Red",
        "2_Nucleo_Estatico": "Yellow",
        "3_Historico_Inerte": "Green"
    }

    for category, folders in mappings.items():
        os.makedirs(category, exist_ok=True)
        for f in folders:
            if os.path.exists(f) and not os.path.islink(f):
                # Check if it's already in the category
                target_path = os.path.join(category, f)
                if not os.path.exists(target_path):
                    print(f"[C5-REAL] Moving {f} to {target_path}")
                    shutil.move(f, target_path)

                    # Create symlink back to root to preserve compilers
                    create_symlink(target_path, f)

                    # Apply macOS Exergy Tag
                    apply_macos_tag(f, colors[category])
                    apply_macos_tag(target_path, colors[category])

if __name__ == "__main__":
    print("Iniciando Transducción de Enlace Único y Mapeo Exergético (C5-REAL)...")
    process_mapping()
    print("Mapeo Completado. Compiladores preservados. Entropía aniquilada.")
