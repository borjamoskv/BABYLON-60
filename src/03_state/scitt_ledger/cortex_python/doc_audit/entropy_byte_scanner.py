#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Low-Level Byte & Entropy Scanner (C5-REAL Agentic Engine)
Análisis de estructura de bytes, cálculo de Entropía de Shannon H(X) por sliding window,
detección de magic bytes, detección de esteganografía tipográfica en bytes crudos y
extracción de overlay data post-EOF con mapa visual de entropía (sparkline).
"""

import argparse
import json
import math
import os
import sys
from typing import Dict, List, Any, Optional, Tuple

# Magic signatures conocidas (Magic Bytes)
MAGIC_SIGNATURES: Dict[str, bytes] = {
    "PDF": b"%PDF-",
    "ZIP/DOCX/XLSX": b"PK\x03\x04",
    "ELF": b"\x7fELF",
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "GIF89a": b"GIF89a",
    "GIF87a": b"GIF87a",
    "GZIP": b"\x1f\x8b",
    "ZSTD": b"\x28\xb5\x2f\xfd",
    "7Z": b"7z\xbc\xaf\x27\x1c",
    "RAR": b"Rar!\x1a\x07",
    "MACH_O_64": b"\xcf\xfa\xed\xfe",
    "MACH_O_32": b"\xce\xfa\xed\xfe",
    "MACH_O_FAT": b"\xca\xfe\xba\xbe",
    "PE_EXE": b"MZ",
    "WASM": b"\x00asm",
    "SQLITE3": b"SQLite format 3\x00",
    "FLAC": b"fLaC",
    "OGG": b"OggS",
}

# Delimitadores de final de archivo conocidos (EOF Markers)
EOF_MARKERS: Dict[str, bytes] = {
    "PDF": b"%%EOF",
    "PNG": b"IEND\xaeB\x60\x82",
    "JPEG": b"\xff\xd9",
    "GIF": b"\x00\x3b",
    "ZIP": b"PK\x05\x06",
}

# Caracteres invisibles Unicode en bytes UTF-8 crudos
INVISIBLE_UNICODE_BYTES: Dict[str, bytes] = {
    "ZWSP (U+200B)": b"\xe2\x80\x8b",
    "ZWNJ (U+200C)": b"\xe2\x80\x8c",
    "ZWJ (U+200D)": b"\xe2\x80\x8d",
    "ZWNBSP (U+FEFF)": b"\xef\xbb\xbf",
    "RLO (U+202E)": b"\xe2\x80\xae",
}

SPARKLINE_CHARS = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


def calculate_shannon_entropy(data: bytes) -> float:
    """
    Calcula la Entropía de Shannon H(X) sobre un bloque de bytes.
    H(X) = - sum(p(x) * log2(p(x)))
    Retorna un valor entre 0.0 y 8.0 bits/byte.
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


def generate_entropy_sparkline(entropies: List[float]) -> str:
    """
    Genera una representación visual tipo sparkline UTF-8 para la distribución de entropía.
    """
    if not entropies:
        return ""
    sparkline = []
    for e in entropies:
        # Mapear 0.0..8.0 al rango de índices 0..7
        idx = min(7, max(0, int((e / 8.0) * 8)))
        sparkline.append(SPARKLINE_CHARS[idx])
    return "".join(sparkline)


class ByteEntropyScanner:
    """
    Escáner forense de bajo nivel para flujos binarios y análisis de entropía.
    """

    def __init__(self, window_size: int = 512, step_size: int = 256):
        self.window_size = window_size
        self.step_size = step_size

    def _detect_magic(self, content: bytes) -> Tuple[str, bool]:
        """Identifica firmas de cabecera en los primeros bytes del stream."""
        if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
            return "WEBP", True
        if len(content) >= 12 and content[4:8] == b"ftyp":
            return "MP4/MOV", True
        if len(content) >= 262 and content[257:262] == b"ustar":
            return "TAR", True

        for fmt, sig in MAGIC_SIGNATURES.items():
            if content.startswith(sig):
                return fmt, True
        return "UNKNOWN", False

    def _detect_unicode_stego_bytes(self, content: bytes) -> Dict[str, int]:
        """Detecta la presencia de secuencias UTF-8 de caracteres invisibles."""
        stego_counts: Dict[str, int] = {}
        for name, pattern in INVISIBLE_UNICODE_BYTES.items():
            count = content.count(pattern)
            if count > 0:
                stego_counts[name] = count
        return stego_counts

    def _check_overlay_data(self, content: bytes, detected_format: str) -> Tuple[bool, int, int, str, Optional[bytes]]:
        if detected_format not in ["PDF", "PNG", "JPEG"]:
            return False, -1, 0, "NONE", None

        marker = EOF_MARKERS[detected_format]
        idx = content.find(marker) if detected_format == "PNG" else content.rfind(marker)
        
        if idx == -1:
            return False, -1, 0, "NONE", None

        eof_offset = idx + len(marker)
        trailing = content[eof_offset:].lstrip(b"\r\n\t ")
        overlay_bytes = len(trailing)
        
        if overlay_bytes == 0:
            return True, eof_offset, 0, "NONE", None

        overlay_format, _ = self._detect_magic(trailing)
        return True, eof_offset, overlay_bytes, overlay_format, trailing

    def scan_file(self, filepath: str) -> Dict[str, Any]:
        """
        Escanea el archivo binario y retorna el diagnóstico de bajo nivel.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        with open(filepath, "rb") as f:
            content = f.read()

        res = self.scan_bytes(content, label=filepath)

        # Detección de Overlay Data específica para archivos con marcadores EOF conocidos
        detected_format = res["detected_format"]
        eof_detected, eof_offset, overlay_bytes, overlay_format, overlay_data = self._check_overlay_data(content, detected_format)

        res.update({
            "eof_detected": eof_detected,
            "eof_offset": eof_offset,
            "overlay_bytes_detected": overlay_bytes,
            "overlay_format_detected": overlay_format,
            "has_anomaly": (overlay_bytes > 0)
            or (res["global_entropy"] > 7.8 and detected_format not in ["ZIP/DOCX/XLSX", "GZIP", "7Z", "RAR", "ZSTD"])
            or len(res["stego_unicode_counts"]) > 0,
        })
        self._last_overlay_data = overlay_data
        return res

    def scan_bytes(self, content: bytes, label: str = "<memory>") -> Dict[str, Any]:
        """
        Análisis in-memory de un slice de bytes arbitrario (Zero-Disk I/O).
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
                "entropy_sparkline": "",
                "stego_unicode_counts": {},
                "eof_detected": False,
                "eof_offset": -1,
                "overlay_bytes_detected": 0,
                "overlay_format_detected": "NONE",
                "has_anomaly": False,
            }

        global_entropy = calculate_shannon_entropy(content)
        detected_format, magic_match = self._detect_magic(content)
        stego_unicode_counts = self._detect_unicode_stego_bytes(content)

        window_entropies: List[float] = []
        high_entropy_regions = 0
        max_entropy = 0.0

        for offset in range(0, max(1, file_size - self.window_size + 1), self.step_size):
            chunk = content[offset : offset + self.window_size]
            entropy = calculate_shannon_entropy(chunk)
            if entropy > max_entropy:
                max_entropy = entropy
            if entropy > 7.5:
                high_entropy_regions += 1
            window_entropies.append(round(entropy, 4))

        sparkline = generate_entropy_sparkline(window_entropies)

        return {
            "filepath": label,
            "file_size": file_size,
            "global_entropy": round(global_entropy, 4),
            "max_window_entropy": round(max_entropy, 4),
            "detected_format": detected_format,
            "magic_matched": magic_match,
            "high_entropy_blocks_count": high_entropy_regions,
            "total_windows_scanned": len(window_entropies),
            "entropy_sparkline": sparkline,
            "stego_unicode_counts": stego_unicode_counts,
            "eof_detected": False,
            "eof_offset": -1,
            "overlay_bytes_detected": 0,
            "overlay_format_detected": "NONE",
            "has_anomaly": (global_entropy > 7.8 and detected_format not in ["ZIP/DOCX/XLSX", "GZIP", "7Z", "RAR", "ZSTD"])
            or len(stego_unicode_counts) > 0,
        }

    def save_overlay(self, output_path: str) -> bool:
        """Guarda el payload de overlay detectado en disco."""
        data = getattr(self, "_last_overlay_data", None)
        if not data:
            return False
        with open(output_path, "wb") as f:
            f.write(data)
        return True


def main():
    parser = argparse.ArgumentParser(description="Low-Level Byte & Entropy Scanner (C5-REAL Engine)")
    parser.add_argument("file", help="Ruta al archivo binario a auditar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")
    parser.add_argument("--window", type=int, default=512, help="Tamaño de la ventana deslizante en bytes (default: 512)")
    parser.add_argument("--step", type=int, default=256, help="Paso de la ventana deslizante en bytes (default: 256)")
    parser.add_argument("--extract-overlay", help="Ruta donde extraer el payload de overlay si se detecta")

    args = parser.parse_args()

    scanner = ByteEntropyScanner(window_size=args.window, step_size=args.step)
    try:
        res = scanner.scan_file(args.file)
    except Exception as e:
        print(f"Error al analizar el archivo: {e}", file=sys.stderr)
        sys.exit(1)

    if args.extract_overlay and res.get("overlay_bytes_detected", 0) > 0:
        if scanner.save_overlay(args.extract_overlay):
            res["overlay_extracted_to"] = args.extract_overlay

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"[EntropyByteScanner] Diagnóstico forense de bajo nivel:")
        print(f"  Archivo:                  {res['filepath']}")
        print(f"  Tamaño:                   {res['file_size']} bytes")
        print(f"  Formato Detectado:        {res['detected_format']} (Magic Match: {res['magic_matched']})")
        print(f"  Entropía Global H(X):     {res['global_entropy']} bits/byte")
        print(f"  Entropía Máxima Ventana:  {res['max_window_entropy']} bits/byte")
        print(f"  Bloques Alta Entropía:    {res['high_entropy_blocks_count']} / {res['total_windows_scanned']}")
        print(f"  Mapa Sparkline Entropía:  [{res['entropy_sparkline']}]")
        if res.get("stego_unicode_counts"):
            print(f"  Stego Unicode Detectado:  {res['stego_unicode_counts']}")
        if res.get("eof_detected"):
            print(f"  EOF Marcador Detectado:   Sí (Offset: {res['eof_offset']})")
            print(f"  Bytes Overlay Post-EOF:   {res['overlay_bytes_detected']} bytes (Formato: {res['overlay_format_detected']})")
        print(f"  Anomalía Detectada:       {'SÍ ⚠️' if res['has_anomaly'] else 'NO (Normal)'}")


if __name__ == "__main__":
    main()
