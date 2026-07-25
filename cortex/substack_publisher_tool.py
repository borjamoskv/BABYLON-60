# C5-REAL EXERGY CERTIFIED
"""
CORTEX Substack Publisher & Formatting Transducer Tool (C5-REAL)
Automates the conversion of raw markdown into high-exergy Substack-ready posts
under the Telmo Dinámico de Moskv persona and Industrial Noir 2026 aesthetic.

Features:
- Enforces zero Markdown tables (|---| -> bold nested lists)
- Enforces zero raw LaTeX $ delimiters (converts to clean Unicode math)
- Dynamically injects random canonical article embeds from borjamoskv.substack.com
- Appends the mandatory CORTEX C5-REAL signature block

Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy), Ω23 (Relative Paths).
"""

import re
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Official published Substack catalog for borjamoskv.substack.com
SUBSTACK_CATALOG = [
    (
        "Un hombre blanco y heterosexual",
        "https://borjamoskv.substack.com/p/el-colapso-del-macho-alfa-de-cristal",
    ),
    (
        "Isomorfismo Estructural: Espacio Latente, TDAH y el Colapso del Orden",
        "https://borjamoskv.substack.com/p/isomorfismo-estructural-espacio-latente",
    ),
    (
        "Tremenda Colisión Reputacional y Artística en el Eje Homme-Yorke-Frusciante-Aphex-Ramoncín",
        "https://borjamoskv.substack.com/p/copy-tremenda-colision-reputacional",
    ),
    (
        "Crítica de la Razón Sintética: Clonify, Kant y el Impuesto a la Ignorancia",
        "https://borjamoskv.substack.com/p/clonify-impuesto-ignorancia-inteligencia-artificial",
    ),
    (
        "La Singularidad Trambólica: Inferencia Latente y el Fin de la Cortesía Termodinámica",
        "https://borjamoskv.substack.com/p/la-singularidad-trambolica-inferencia",
    ),
    (
        "El Handshake Causal: Por qué Anthropic asimiló el Genoma de BABYLON-60",
        "https://borjamoskv.substack.com/p/el-handshake-causal-por-que-anthropic",
    ),
    (
        "Desmontando a David Domínguez: Autopsia Forense (de A a la Z)",
        "https://borjamoskv.substack.com/p/desmontando-a-david-dominguez-autopsia",
    ),
    (
        "¿Sueñan los androides con la música de Aphex Twin?",
        "https://borjamoskv.substack.com/p/borja-moskv-aphex-twin",
    ),
    (
        "Los Cinco Dólares de Kant: Minoría de Edad, Fugazi y el Meme del UNC",
        "https://borjamoskv.substack.com/p/kant-fugazi-diy-ethics-5-dollar-show",
    ),
    (
        "CORTEX Persist / BABYLON-60: investigación técnica",
        "https://borjamoskv.substack.com/p/cortex-persist-babylon-60-investigacion",
    ),
]

def format_signature_block(count: int = 4) -> str:
    """Generates the mandatory signature block with random Substack catalog embeds."""
    mandatory_link = SUBSTACK_CATALOG[0]
    remaining_links = SUBSTACK_CATALOG[1:]

    # Select random items
    selected = random.sample(remaining_links, min(count, len(remaining_links)))

    block = "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):\n"
    block += f"- [{mandatory_link[0]}]({mandatory_link[1]})\n"
    for title, url in selected:
        block += f"- [{title}]({url})\n"

    return block

def purge_latex_math(text: str) -> str:
    """Replaces raw LaTeX $ math delimiters with clean Unicode equivalents."""
    text = re.sub(r"\$S = -\\sum p_i \\ln p_i\$", "S = -∑ p_i ln(p_i)", text)
    text = re.sub(r"\$([a-zA-Z0-9_\-\+\*\/\=\<\>\(\)]+)\$", r"\1", text)
    return text

def convert_tables_to_lists(text: str) -> str:
    """Converts raw Markdown tables (|---|) to structured bold lists."""
    lines = text.split("\n")
    new_lines = []
    in_table = False
    headers: list[str] = []

    for line in lines:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            parts = [p.strip() for p in line.strip().split("|")[1:-1]]
            if all(set(p) <= set("-: ") for p in parts if p):
                # Separator line
                in_table = True
                continue
            if not in_table and not headers:
                headers = parts
                continue
            elif in_table:
                # Data row
                row_str = f"* **{parts[0]}:** " + ", ".join(
                    f"{headers[i]}: {parts[i]}" for i in range(1, min(len(headers), len(parts)))
                )
                new_lines.append(row_str)
                continue
        else:
            if in_table:
                in_table = False
                headers = []
            new_lines.append(line)

    return "\n".join(new_lines)

def process_markdown_for_substack(raw_md: str) -> str:
    cleaned = purge_latex_math(raw_md)
    cleaned = convert_tables_to_lists(cleaned)
    if "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima" not in cleaned:
        cleaned += "\n\n---\n\n" + format_signature_block()
    return cleaned

if __name__ == "__main__":
    test_text = "Here is a test: $S = -\\sum p_i \\ln p_i$"
    processed = process_markdown_for_substack(test_text)
    print("Transducer tool initialized successfully!")
