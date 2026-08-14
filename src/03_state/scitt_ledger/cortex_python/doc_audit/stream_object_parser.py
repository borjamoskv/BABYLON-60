#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Low-Level Stream & Object Parser (C5-REAL Agentic Engine)
Análisis de objetos binarios, descompresión zlib/FlateDecode en tiempo real,
inspección de diccionarios y búsqueda de disparadores ejecutables (/JavaScript, /Launch).
"""

import re
import sys
import zlib
from typing import Dict, List, Any

RISKY_TOKENS = [
    rb"/JavaScript", rb"/JS", rb"/Launch", rb"/EmbeddedFiles",
    rb"/OpenAction", rb"/AA", rb"/URI", rb"/SubmitForm", rb"/ImportData"
]

class StreamObjectParser:
    """
    Parser forense de objetos PDF/Streams a bajo nivel.
    """

    def _process_stream(self, body: bytes, risky_token_matches: Dict[str, int]) -> tuple[bool, int, int]:
        stream_match = re.search(rb"stream\r?\n(.*?\r?\n)endstream", body, re.DOTALL)
        if not stream_match:
            return False, 0, 0
            
        raw_stream = stream_match.group(1)
        try:
            decompressed_data = zlib.decompress(raw_stream)
            for token in RISKY_TOKENS:
                token_str = token.decode("ascii")
                if token in decompressed_data:
                    risky_token_matches[token_str] = risky_token_matches.get(token_str, 0) + 1
            return True, len(decompressed_data), 0
        except Exception:
            return True, 0, 1

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, "rb") as f:
            content = f.read()

        # Localizar objetos 'N M obj ... endobj'
        obj_pattern = re.compile(rb"(\d+)\s+(\d+)\s+obj(.*?)endobj", re.DOTALL)
        objects = obj_pattern.findall(content)

        parsed_objects: List[Dict[str, Any]] = []
        risky_token_matches: Dict[str, int] = {}
        streams_decompressed = 0
        decompression_failures = 0

        for num_b, gen_b, body in objects:
            obj_id = f"{num_b.decode('ascii', errors='ignore')}_{gen_b.decode('ascii', errors='ignore')}"

            # Buscar tokens de riesgo en el cuerpo crudo del objeto
            for token in RISKY_TOKENS:
                token_str = token.decode("ascii")
                if token in body:
                    risky_token_matches[token_str] = risky_token_matches.get(token_str, 0) + 1

            is_compressed, decompressed_size, failures = self._process_stream(body, risky_token_matches)
            if is_compressed and failures == 0:
                streams_decompressed += 1
            decompression_failures += failures

            parsed_objects.append({
                "obj_id": obj_id,
                "raw_size": len(body),
                "is_compressed": is_compressed,
                "decompressed_size": decompressed_size
            })

        # Extraer entradas XRef si existen
        xref_match = re.findall(rb"xref\r?\n(\d+)\s+(\d+)", content)
        xref_declared_objects = 0
        for start, count in xref_match:
            try:
                xref_declared_objects += int(count)
            except ValueError:
                pass

        return {
            "filepath": filepath,
            "total_objects_found": len(parsed_objects),
            "xref_declared_objects": xref_declared_objects,
            "streams_decompressed": streams_decompressed,
            "decompression_failures": decompression_failures,
            "risky_tokens_detected": risky_token_matches,
            "has_executable_risks": len(risky_token_matches) > 0,
            "has_orphan_objects": len(parsed_objects) > xref_declared_objects if xref_declared_objects > 0 else False
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 stream_object_parser.py <archivo>")
        sys.exit(1)
    parser = StreamObjectParser()
    res = parser.parse_file(sys.argv[1])
    print(f"[StreamObjectParser] Diagnóstico de {sys.argv[1]}:")
    for k, v in res.items():
        print(f"  {k}: {v}")
