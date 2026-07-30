# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Gemini PRO Key Collector & Validator (C5-REAL).
Verifica e inyecta dinámicamente claves API de Gemini PRO en .env.
"""

import os
import sys
import json
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def validate_gemini_key(api_key: str) -> bool:
    """Valida una clave API consultando los modelos disponibles."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            return len(models) > 0
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False

def append_keys_to_env(keys: list[str]) -> int:
    """Valida y añade claves verificadas a .env."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    existing_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    valid_added = 0
    new_lines = []

    # Contar cuántas claves GEMINI_API_KEY_XX existen ya
    idx = 1
    while f"GEMINI_API_KEY_{idx:02d}" in existing_content:
        idx += 1

    for k in keys:
        k_clean = k.strip()
        if not k_clean or k_clean in existing_content:
            continue

        print(f"🔍 Validando clave [{k_clean[:8]}...{k_clean[-4:]}]...")
        if validate_gemini_key(k_clean):
            var_name = f"GEMINI_API_KEY_{idx:02d}"
            new_lines.append(f'{var_name}="{k_clean}"\n')
            print(f"✅ Clave válida! Registrada como {var_name}")
            idx += 1
            valid_added += 1
        else:
            print("❌ Clave inválida o sin acceso a Gemini API.")

    if new_lines:
        with open(env_path, "a", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"\n🎉 {valid_added} clave(s) registrada(s) con éxito en .env.")
    else:
        print("\n⚠️ No se añadieron claves nuevas.")

    return valid_added

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_keys = sys.argv[1:]
        append_keys_to_env(input_keys)
    else:
        print("Uso: python3 scripts/gemini_pool_collector.py <KEY_1> <KEY_2> ... <KEY_N>")
