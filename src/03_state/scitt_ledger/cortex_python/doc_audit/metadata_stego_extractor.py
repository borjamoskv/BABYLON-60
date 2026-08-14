#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Low-Level Metadata & Steganography Extractor (C5-REAL Agentic Engine)
Extracción de metadatos XMP / Info Dictionaries, detección de caracteres invisibles
Zero-Width (U+200B..U+200D, U+FEFF, U+202E) y homóglifos.
"""

import re
import sys
from typing import Dict, List, Any

# Rangos Unicode de caracteres invisibles y Zero-Width
ZERO_WIDTH_CHARS = {
    "\u200B": "Zero Width Space (U+200B)",
    "\u200C": "Zero Width Non-Joiner (U+200C)",
    "\u200D": "Zero Width Joiner (U+200D)",
    "\uFEFF": "Zero Width No-Break Space / BOM (U+FEFF)",
    "\u202E": "Right-To-Left Override (U+202E)",
    "\u200E": "Left-To-Right Mark (U+200E)",
    "\u200F": "Right-To-Left Mark (U+200F)"
}

# Rangos de Homóglifos Cirílicos / Griego comunes intercalados en texto Latino
HOMOGLYPH_CYRILLIC = set("аеорсхуАВЕКМНОРСТХ") # Caracteres cirílicos idénticos visualmente a latinos

class MetadataStegoExtractor:
    """
    Inspector forense de metadatos crudos y canales de esteganografía.
    """

    def inspect_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()

        text_content = raw_bytes.decode("utf-8", errors="ignore")

        # 1. Extracción de Metadatos /Info
        info_dict: Dict[str, str] = {}
        info_match = re.search(rb"/Info\s+(\d+\s+\d+\s+R)", raw_bytes)
        if info_match:
            info_dict["info_reference"] = info_match.group(1).decode("ascii")

        # Claves estándar de /Info
        for key in [b"Author", b"Creator", b"Producer", b"CreationDate", b"ModDate", b"Title", b"Subject"]:
            val_match = re.search(rb"/" + key + rb"\s*\((.*?)\)", raw_bytes)
            if val_match:
                info_dict[key.decode("ascii")] = val_match.group(1).decode("utf-8", errors="ignore")

        # 2. Extracción de Bloques XMP Metadata XML
        xmp_packets: List[str] = []
        xmp_matches = re.findall(rb"<\?xpacket begin=.*?<\?xpacket end=.*?\?>", raw_bytes, re.DOTALL)
        for xmp in xmp_matches:
            xmp_packets.append(xmp.decode("utf-8", errors="ignore")[:300] + "...")

        # 3. Detección de Caracteres Invisibles / Zero-Width Steganography
        zero_width_counts: Dict[str, int] = {}
        total_zero_width = 0

        for char, name in ZERO_WIDTH_CHARS.items():
            count = text_content.count(char)
            if count > 0:
                zero_width_counts[name] = count
                total_zero_width += count

        # 4. Decodificación de Secuencia Esteganográfica si existen Zero-Width
        stego_binary_payload = ""
        if "\u200B" in text_content or "\u200C" in text_content:
            stego_map = {"\u200B": "0", "\u200C": "1"}
            bits = [stego_map[char] for char in text_content if char in stego_map]
            stego_binary_payload = "".join(bits)

        # 5. Detección de Homóglifos
        homoglyphs_detected = 0
        for char in text_content:
            if char in HOMOGLYPH_CYRILLIC:
                homoglyphs_detected += 1

        return {
            "filepath": filepath,
            "info_metadata": info_dict,
            "xmp_packets_found": len(xmp_packets),
            "zero_width_counts": zero_width_counts,
            "total_zero_width_chars": total_zero_width,
            "stego_binary_bits_len": len(stego_binary_payload),
            "homoglyphs_detected": homoglyphs_detected,
            "has_steganography": (total_zero_width > 5) or (len(stego_binary_payload) >= 8) or (homoglyphs_detected > 0)
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 metadata_stego_extractor.py <archivo>")
        sys.exit(1)
    extractor = MetadataStegoExtractor()
    res = extractor.inspect_file(sys.argv[1])
    print(f"[MetadataStegoExtractor] Diagnóstico de {sys.argv[1]}:")
    for k, v in res.items():
        print(f"  {k}: {v}")
