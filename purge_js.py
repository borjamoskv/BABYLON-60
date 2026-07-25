import os
import re

def purge_semantic_friction(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para preservar strings y purgar comentarios
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"|`(?:\\.|[^\\`])*`',
        re.DOTALL | re.MULTILINE
    )

    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""  # Aniquilar anergía
        return s       # Preservar string

    new_content = re.sub(pattern, replacer, content)
    # Limpiar saltos de línea huérfanos
    new_content = re.sub(r'^\s*$\n', '', new_content, flags=re.MULTILINE)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    targets = [
        "babylon60-ide/extension/background.js",
        "babylon60-ide/extension/content.js",
        "babylon60-ide/extension/popup.js",
        "babylon60-ide/frontend/src/api.js",
        "babylon60-ide/frontend/src/cinematic_engine.js",
        "babylon60-ide/frontend/src/main.js",
        "babylon60-ide/frontend/src/ontology.js",
        "babylon60-ide/frontend/src/router.js",
        "babylon60-ide/frontend/vite.config.js",
        "cortex/frontend/cinematic_engine.js"
    ]
    for target in targets:
        if os.path.exists(target):
            purge_semantic_friction(target)
            print(f"C5-REAL: Entropía purgada en {target}")

if __name__ == "__main__":
    main()
