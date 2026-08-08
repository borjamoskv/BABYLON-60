#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Low-Level Byte & Entropy Scanner (C5-REAL Agentic Engine)
Análisis de estructura de bytes, cálculo de Entropía de Shannon H(X) por sliding window,
detección de magic bytes y detección de overlay data post-EOF.
"""

import math
import os
import sys
from typing import Dict, List, Tuple, Any

# Magic signatures conocidas (Magic Bytes)
MAGIC_SIGNATURES: Dict[str, bytes] = {
    "PDF": b"%PDF-",
    "ZIP/DOCX": b"PK\x03\x04",
    "ELF": b"\x7fELF",
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "GZIP": b"\x1f\x8b",
    "MACH_O_64": b"\xcf\xfa\xed\xfe",
    "MACH_O_32": b"\xce\xfa\xed\xfe",
    "RIFF/WAV": b"RIFF"
}

# Delimitadores de final de archivo conocidos (EOF Markers)
EOF_MARKERS: Dict[str, bytes] = {
    "PDF": b"%%EOF",
    "PNG": b"IEND\xaeB`\x82",
    "JPEG": b"\xff\xd9"
}

def calculate_shannon_entropy(data: bytes) -> float:
    """
    Calcula la Entropía de Shannon H(X) sobre un bloque de bytes.
    H(X) = - sum(p(x) * log2(p(x)))
    Retorna un valor entre 0.0 y 8.0.
    """
    if not data:
        return 0.0
    length = len(data)
    counts: Dict[int, int] = {}
    for byte in data:
        counts[byte] = counts.get(byte, 0) + 1

    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

class ByteEntropyScanner:
    """
    Escáner forense de bajo nivel para flujos binarios.
    """

    def __init__(self, window_size: int = 512, step_size: int = 256):
        self.window_size = window_size
        self.step_size = step_size

    def scan_file(self, filepath: str) -> Dict[str, Any]:
        """
        Escanea el archivo binario y retorna el diagnóstico de bajo nivel.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        with open(filepath, "rb") as f:
            content = f.read()

        file_size = len(content)
        global_entropy = calculate_shannon_entropy(content)

        # Detectar Magic Bytes
        detected_format = "UNKNOWN"
        magic_match = False
        for fmt, sig in MAGIC_SIGNATURES.items():
            if content.startswith(sig):
                detected_format = fmt
                magic_match = True
                break

        # Análisis de ventana deslizante (Sliding Window Entropy)
        window_entropies: List[Dict[str, Any]] = []
        high_entropy_regions = 0
        max_entropy = 0.0

        for offset in range(0, max(1, file_size - self.window_size + 1), self.step_size):
            chunk = content[offset : offset + self.window_size]
            entropy = calculate_shannon_entropy(chunk)
            if entropy > max_entropy:
                max_entropy = entropy

            is_high = entropy > 7.5
            if is_high:
                high_entropy_regions += 1

            window_entropies.append({
                "offset": offset,
                "size": len(chunk),
                "entropy": round(entropy, 4),
                "is_high_entropy": is_high
            })

        # Detección de Overlay Data (Datos tras el marcador EOF formal)
        overlay_bytes = 0
        eof_detected = False
        eof_offset = -1
        overlay_format = "NONE"

        if detected_format == "PDF":
            last_eof = content.rfind(EOF_MARKERS["PDF"])
            if last_eof != -1:
                eof_detected = True
                eof_offset = last_eof + len(EOF_MARKERS["PDF"])
                # Permitir saltos de línea finales (\r, \n)
                trailing = content[eof_offset:].lstrip(b"\r\n\t ")
                overlay_bytes = len(trailing)
                if overlay_bytes > 0:
                    # Inspección recursiva del payload aislado
                    for fmt, sig in MAGIC_SIGNATURES.items():
                        if trailing.startswith(sig):
                            overlay_format = fmt
                            break
        elif detected_format == "PNG":
            iend_idx = content.find(EOF_MARKERS["PNG"])
            if iend_idx != -1:
                eof_detected = True
                eof_offset = iend_idx + len(EOF_MARKERS["PNG"])
                trailing = content[eof_offset:].lstrip(b"\r\n\t ")
                overlay_bytes = len(trailing)
                if overlay_bytes > 0:
                    for fmt, sig in MAGIC_SIGNATURES.items():
                        if trailing.startswith(sig):
                            overlay_format = fmt
                            break

        return {
            "filepath": filepath,
            "file_size": file_size,
            "global_entropy": round(global_entropy, 4),
            "max_window_entropy": round(max_entropy, 4),
            "detected_format": detected_format,
            "magic_matched": magic_match,
            "high_entropy_blocks_count": high_entropy_regions,
            "total_windows_scanned": len(window_entropies),
            "eof_detected": eof_detected,
            "eof_offset": eof_offset,
            "overlay_bytes_detected": overlay_bytes,
            "overlay_format_detected": overlay_format,
            "has_anomaly": (overlay_bytes > 0) or (global_entropy > 7.8 and detected_format not in ["ZIP/DOCX", "GZIP"])
        }

    def scan_bytes(self, content: bytes, label: str = "<memory>") -> Dict[str, Any]:
        """
        Análisis in-memory de un slice de bytes arbitrario (Zero-Disk I/O).
        Usado para la disección recursiva de payloads aislados del overlay.
        """
        file_size = len(content)
        if file_size == 0:
            return {
                "filepath": label,
                "file_size": 0,
                "global_entropy": 0.0,
                "max_window_entropy": 0.0,
                "detected_format": "EMPTY",
                "magic_matched": False,
                "high_entropy_blocks_count": 0,
                "total_windows_scanned": 0,
                "eof_detected": False,
                "eof_offset": -1,
                "overlay_bytes_detected": 0,
                "overlay_format_detected": "NONE",
                "has_anomaly": False,
            }

        global_entropy = calculate_shannon_entropy(content)

        detected_format = "UNKNOWN"
        magic_match = False
        for fmt, sig in MAGIC_SIGNATURES.items():
            if content.startswith(sig):
                detected_format = fmt
                magic_match = True
                break

        high_entropy_regions = 0
        max_entropy = 0.0
        windows_scanned = 0
        for offset in range(0, max(1, file_size - self.window_size + 1), self.step_size):
            chunk = content[offset : offset + self.window_size]
            entropy = calculate_shannon_entropy(chunk)
            if entropy > max_entropy:
                max_entropy = entropy
            if entropy > 7.5:
                high_entropy_regions += 1
            windows_scanned += 1

        return {
            "filepath": label,
            "file_size": file_size,
            "global_entropy": round(global_entropy, 4),
            "max_window_entropy": round(max_entropy, 4),
            "detected_format": detected_format,
            "magic_matched": magic_match,
            "high_entropy_blocks_count": high_entropy_regions,
            "total_windows_scanned": windows_scanned,
            "eof_detected": False,
            "eof_offset": -1,
            "overlay_bytes_detected": 0,
            "overlay_format_detected": "NONE",
            "has_anomaly": global_entropy > 7.8 and detected_format not in ["ZIP/DOCX", "GZIP"],
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 entropy_byte_scanner.py <archivo>")
        sys.exit(1)
    scanner = ByteEntropyScanner()
    res = scanner.scan_file(sys.argv[1])
    print(f"[EntropyByteScanner] Diagnóstico de {sys.argv[1]}:")
    for k, v in res.items():
        print(f"  {k}: {v}")
