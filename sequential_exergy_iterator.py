# C5-REAL EXERGY CERTIFIED
import os
import glob

print("Iniciando Transducción Secuencial A-Z (C5-REAL)...")

# Get all files and sort A-Z
all_files = glob.glob('**/*', recursive=True)
all_files = [f for f in all_files if os.path.isfile(f) and not f.startswith('.git/') and '/node_modules/' not in f and '/target/' not in f and '/.venv/' not in f and '/.uv_python/' not in f]
all_files.sort()

processed_count = 0
mutated_count = 0

for file_path in all_files:
    processed_count += 1

    # Try reading as text to remove anergia (trailing whitespace, multiple empty lines)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Maximize Exergy (Kolmogorov compression of whitespace/anergy)
        # 1. Remove trailing spaces
        content = '\n'.join([line.rstrip() for line in content.split('\n')])

        # 2. Collapse more than 2 empty lines into 1
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 3. Ensure single trailing newline
        content = content.strip() + '\n'

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            mutated_count += 1
            print(f"[{processed_count}/{len(all_files)}] Exergía maximizada (Mutación C5-REAL): {file_path}")
        else:
            # print(f"[{processed_count}/{len(all_files)}] Exergía óptima: {file_path}")
            pass

    except UnicodeDecodeError:
        # Binary file, skip
        pass

print(f"\nIteración A-Z completada. Archivos procesados: {processed_count}. Archivos mutados: {mutated_count}.")

# Git commit
os.system("git add . && git commit -m 'refactor(core): ITERA secuencial A-Z extrayendo entropía'")
os.system("git rev-parse --short HEAD > hash_sequential.txt")
