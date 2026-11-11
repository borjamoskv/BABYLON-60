"""Regenera los vectores de prueba del verificador con oráculos ajenos a la implementación TypeScript.

Oráculos:
- BLAKE3: paquete ``blake3`` (bindings de la implementación oficial en Rust).
- Merkle v1: ``01_KISH_ENGINE/babylon60/attestation/merkle_b3.py`` de este repositorio, cargado por ruta.
- CBOR: ``cbor2`` con ``canonical=True``, solo sobre el perfil restringido (uint, texto, bytes, arrays).

Uso, desde la raíz del repositorio::

    uv run --locked python tools/ui_kernel_console/tests/fixtures/generate_vectors.py

Escribe ``blake3Kat.ts``, ``merkleV1Vectors.ts`` y ``cborVectors.ts`` junto a este archivo. Los
archivos generados se versionan; ``npm test`` los compara con la implementación TypeScript.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path

import blake3
import cbor2

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MERKLE_TWIN = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "attestation" / "merkle_b3.py"
PRAGMA = " // pragma: allowlist secret"
HEADER = "// Generado por tests/fixtures/generate_vectors.py. No editar a mano.\n"

BLAKE3_LENGTHS = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 63, 64, 65, 127, 128, 129, 1023, 1024, 1025, 2048, 2049, 3072, 3073,
    4096, 4097, 5120, 5121, 6144, 6145, 7168, 7169, 8192, 8193, 16384, 31744, 102400,
]


def load_merkle_twin():
    spec = importlib.util.spec_from_file_location("merkle_b3_repo", MERKLE_TWIN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar {MERKLE_TWIN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lcg_bytes(seed: int, count: int) -> bytes:
    """Bytes deterministas que la prueba TypeScript reproduce con el mismo generador congruencial."""
    out = bytearray()
    x = seed & 0xFFFFFFFF
    for _ in range(count):
        x = (1664525 * x + 1013904223) & 0xFFFFFFFF
        out.append((x >> 24) & 0xFF)
    return bytes(out)


def ts(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def hex_line(body: str) -> str:
    return f"  {body},{PRAGMA}\n"


def write_blake3() -> int:
    source = f"paquete blake3 {blake3.__version__} (implementación oficial)"
    lines = [HEADER, "\n", f"export const BLAKE3_KAT_SOURCE = {ts(source)};\n\n"]
    lines.append("/** Entrada de cada caso: bytes i % 251 para i en [0, len). */\n")
    lines.append("export const BLAKE3_KAT: readonly (readonly [len: number, hash: string])[] = [\n")
    for length in BLAKE3_LENGTHS:
        digest = blake3.blake3(bytes(i % 251 for i in range(length))).hexdigest()
        lines.append(hex_line(f"[{length}, {ts(digest)}]"))
    lines.append("];\n\n")
    lines.append(f"export const BLAKE3_ABC = {ts(blake3.blake3(b'abc').hexdigest())};{PRAGMA}\n")
    (HERE / "blake3Kat.ts").write_text("".join(lines), encoding="utf-8")
    return len(BLAKE3_LENGTHS)


def leaf_descriptor(kind: str, value: object) -> tuple[str, bytes]:
    if kind == "utf8":
        assert isinstance(value, str)
        return f"{{ t: \"utf8\", v: {ts(value)} }}", value.encode("utf-8")
    seed, count = value  # type: ignore[misc]
    return f"{{ t: \"lcg\", seed: {seed}, len: {count} }}", lcg_bytes(seed, count)


def write_merkle() -> int:
    mb3 = load_merkle_twin()
    source = (
        "01_KISH_ENGINE/babylon60/attestation/merkle_b3.py de este repositorio, "
        f"ejecutado con el paquete blake3 {blake3.__version__}"
    )
    lines = [HEADER, "\n", f"export const MERKLE_V1_SOURCE = {ts(source)};\n\n"]
    lines.append("export type LeafData = { readonly t: \"utf8\"; readonly v: string } | { readonly t: \"lcg\"; readonly seed: number; readonly len: number };\n\n")

    lines.append("export const LEAF_HASHES: readonly { readonly data: LeafData; readonly hash: string }[] = [\n")
    leaf_cases = [("utf8", ""), ("utf8", "a"), ("utf8", "BISIM_LEAF_0"), ("lcg", (1, 64)), ("lcg", (2, 1024)), ("lcg", (3, 1025)), ("lcg", (4, 5000))]
    for kind, value in leaf_cases:
        descriptor, data = leaf_descriptor(kind, value)
        lines.append(hex_line(f"{{ data: {descriptor}, hash: {ts(mb3.leaf_hash(data).hex())} }}"))
    lines.append("];\n\n")

    lines.append("/** Hijos izquierdo y derecho: bytes LCG de 32 bytes con las semillas indicadas. */\n")
    lines.append("export const NODE_HASHES: readonly { readonly leftSeed: number; readonly rightSeed: number; readonly hash: string }[] = [\n")
    for i in range(4):
        left, right = lcg_bytes(10 + i, 32), lcg_bytes(20 + i, 32)
        lines.append(hex_line(f"{{ leftSeed: {10 + i}, rightSeed: {20 + i}, hash: {ts(mb3.node_hash(left, right).hex())} }}"))
    lines.append("];\n\n")

    lines.append("/** Hojas BISIM_LEAF_{i} para i en [0, n), como en tests/test_merkle_b3.py del repositorio. */\n")
    lines.append("export const TEXT_ROOTS: readonly (readonly [n: number, root: string])[] = [\n")
    text_counts = list(range(1, 18)) + [31, 32, 33, 64, 65, 100, 101, 257]
    for n in text_counts:
        leaves = [f"BISIM_LEAF_{i}".encode() for i in range(n)]
        lines.append(hex_line(f"[{n}, {ts(mb3.build_root(leaves))}]"))
    lines.append("];\n\n")

    lines.append("/** Hoja i: bytes LCG con semilla seed * 1000 + i y longitud (i * 37) % 200. */\n")
    lines.append("export const BINARY_ROOTS: readonly { readonly n: number; readonly seed: number; readonly root: string }[] = [\n")
    binary_cases = [(1, 100), (2, 101), (3, 102), (5, 103), (6, 104), (7, 105), (9, 106)]
    for n, seed in binary_cases:
        leaves = [lcg_bytes(seed * 1000 + i, (i * 37) % 200) for i in range(n)]
        lines.append(hex_line(f"{{ n: {n}, seed: {seed}, root: {ts(mb3.build_root(leaves))} }}"))
    lines.append("];\n")
    (HERE / "merkleV1Vectors.ts").write_text("".join(lines), encoding="utf-8")
    return len(leaf_cases) + 4 + len(text_counts) + len(binary_cases)


def write_cbor() -> int:
    version = importlib.metadata.version("cbor2")
    cases: list[tuple[str, str, bytes]] = []

    def add(name: str, descriptor: str, value: object) -> None:
        cases.append((name, descriptor, cbor2.dumps(value, canonical=True)))

    for n in [0, 1, 10, 23, 24, 25, 100, 255, 256, 1000, 65535, 65536, 1000000, 4294967295, 4294967296, 1000000000000, 9007199254740991]:
        add(f"uint {n}", f"{{ t: \"int\", v: {n} }}", n)
    texts = ["", "a", "IETF", "\"\\", "\u00fc", "\u6c34", "\U00010151", "BABYLON60_EXEC_NODE_V1", "l\u00ednea\ncon\tcontrol\u0000y\u2028sep", "x" * 23, "x" * 24, "x" * 255, "x" * 256]
    for text in texts:
        add(f"text len {len(text)}", f"{{ t: \"text\", v: {ts(text)} }}", text)
    add("text repeat 40000", "{ t: \"textRepeat\", unit: \"\\u00f1\", count: 40000 }", "\u00f1" * 40000)
    for seed, count in [(6, 0), (7, 23), (8, 24), (9, 32), (10, 300), (11, 70000)]:
        add(f"bytes lcg {count}", f"{{ t: \"bytesLcg\", seed: {seed}, count: {count} }}", lcg_bytes(seed, count))
    add("empty array", "{ t: \"array\", v: [] }", [])
    add(
        "nested array",
        "{ t: \"array\", v: [{ t: \"int\", v: 1 }, { t: \"array\", v: [{ t: \"int\", v: 2 }, { t: \"int\", v: 3 }] }, "
        "{ t: \"array\", v: [{ t: \"text\", v: \"a\" }, { t: \"array\", v: [] }, { t: \"bytesLcg\", seed: 5, count: 2 }] }] }",
        [1, [2, 3], ["a", [], lcg_bytes(5, 2)]],
    )
    add("array 25", "{ t: \"array\", v: Array.from({ length: 25 }, (_, i) => ({ t: \"int\" as const, v: i })) }", list(range(25)))

    lines = [HEADER, "\n", f"export const CBOR_SOURCE = {ts('cbor2 ' + version + ' dumps(canonical=True)')};\n\n"]
    lines.append(
        "export type Desc =\n"
        "  | { readonly t: \"int\"; readonly v: number }\n"
        "  | { readonly t: \"text\"; readonly v: string }\n"
        "  | { readonly t: \"textRepeat\"; readonly unit: string; readonly count: number }\n"
        "  | { readonly t: \"bytesLcg\"; readonly seed: number; readonly count: number }\n"
        "  | { readonly t: \"array\"; readonly v: readonly Desc[] };\n\n"
    )
    lines.append("/** Codificaciones cortas: hex completo. Largas: longitud y BLAKE3 de la codificación. */\n")
    lines.append(
        "export const CBOR_VECTORS: readonly { readonly name: string; readonly value: Desc; readonly hex?: string; "
        "readonly len?: number; readonly blake3?: string }[] = [\n"
    )
    for name, descriptor, encoded in cases:
        if len(encoded) > 48:
            expected = f"len: {len(encoded)}, blake3: {ts(blake3.blake3(encoded).hexdigest())}"
        else:
            expected = f"hex: {ts(encoded.hex())}"
        lines.append(hex_line(f"{{ name: {ts(name)}, value: {descriptor}, {expected} }}"))
    lines.append("];\n")
    (HERE / "cborVectors.ts").write_text("".join(lines), encoding="utf-8")
    return len(cases)


def main() -> None:
    counts = {"blake3": write_blake3(), "merkle_v1": write_merkle(), "cbor": write_cbor()}
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
