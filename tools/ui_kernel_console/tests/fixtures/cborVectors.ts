// Generado por tests/fixtures/generate_vectors.py. No editar a mano.

export const CBOR_SOURCE = "cbor2 6.2.1 dumps(canonical=True)";

export type Desc =
  | { readonly t: "int"; readonly v: number }
  | { readonly t: "text"; readonly v: string }
  | { readonly t: "textRepeat"; readonly unit: string; readonly count: number }
  | { readonly t: "bytesLcg"; readonly seed: number; readonly count: number }
  | { readonly t: "array"; readonly v: readonly Desc[] };

/** Codificaciones cortas: hex completo. Largas: longitud y BLAKE3 de la codificación. */
export const CBOR_VECTORS: readonly { readonly name: string; readonly value: Desc; readonly hex?: string; readonly len?: number; readonly blake3?: string }[] = [
  { name: "uint 0", value: { t: "int", v: 0 }, hex: "00" }, // pragma: allowlist secret
  { name: "uint 1", value: { t: "int", v: 1 }, hex: "01" }, // pragma: allowlist secret
  { name: "uint 10", value: { t: "int", v: 10 }, hex: "0a" }, // pragma: allowlist secret
  { name: "uint 23", value: { t: "int", v: 23 }, hex: "17" }, // pragma: allowlist secret
  { name: "uint 24", value: { t: "int", v: 24 }, hex: "1818" }, // pragma: allowlist secret
  { name: "uint 25", value: { t: "int", v: 25 }, hex: "1819" }, // pragma: allowlist secret
  { name: "uint 100", value: { t: "int", v: 100 }, hex: "1864" }, // pragma: allowlist secret
  { name: "uint 255", value: { t: "int", v: 255 }, hex: "18ff" }, // pragma: allowlist secret
  { name: "uint 256", value: { t: "int", v: 256 }, hex: "190100" }, // pragma: allowlist secret
  { name: "uint 1000", value: { t: "int", v: 1000 }, hex: "1903e8" }, // pragma: allowlist secret
  { name: "uint 65535", value: { t: "int", v: 65535 }, hex: "19ffff" }, // pragma: allowlist secret
  { name: "uint 65536", value: { t: "int", v: 65536 }, hex: "1a00010000" }, // pragma: allowlist secret
  { name: "uint 1000000", value: { t: "int", v: 1000000 }, hex: "1a000f4240" }, // pragma: allowlist secret
  { name: "uint 4294967295", value: { t: "int", v: 4294967295 }, hex: "1affffffff" }, // pragma: allowlist secret
  { name: "uint 4294967296", value: { t: "int", v: 4294967296 }, hex: "1b0000000100000000" }, // pragma: allowlist secret
  { name: "uint 1000000000000", value: { t: "int", v: 1000000000000 }, hex: "1b000000e8d4a51000" }, // pragma: allowlist secret
  { name: "uint 9007199254740991", value: { t: "int", v: 9007199254740991 }, hex: "1b001fffffffffffff" }, // pragma: allowlist secret
  { name: "text len 0", value: { t: "text", v: "" }, hex: "60" }, // pragma: allowlist secret
  { name: "text len 1", value: { t: "text", v: "a" }, hex: "6161" }, // pragma: allowlist secret
  { name: "text len 4", value: { t: "text", v: "IETF" }, hex: "6449455446" }, // pragma: allowlist secret
  { name: "text len 2", value: { t: "text", v: "\"\\" }, hex: "62225c" }, // pragma: allowlist secret
  { name: "text len 1", value: { t: "text", v: "\u00fc" }, hex: "62c3bc" }, // pragma: allowlist secret
  { name: "text len 1", value: { t: "text", v: "\u6c34" }, hex: "63e6b0b4" }, // pragma: allowlist secret
  { name: "text len 1", value: { t: "text", v: "\ud800\udd51" }, hex: "64f0908591" }, // pragma: allowlist secret
  { name: "text len 22", value: { t: "text", v: "BABYLON60_EXEC_NODE_V1" }, hex: "76424142594c4f4e36305f455845435f4e4f44455f5631" }, // pragma: allowlist secret
  { name: "text len 23", value: { t: "text", v: "l\u00ednea\ncon\tcontrol\u0000y\u2028sep" }, hex: "781a6cc3ad6e65610a636f6e09636f6e74726f6c0079e280a8736570" }, // pragma: allowlist secret
  { name: "text len 23", value: { t: "text", v: "xxxxxxxxxxxxxxxxxxxxxxx" }, hex: "777878787878787878787878787878787878787878787878" }, // pragma: allowlist secret
  { name: "text len 24", value: { t: "text", v: "xxxxxxxxxxxxxxxxxxxxxxxx" }, hex: "7818787878787878787878787878787878787878787878787878" }, // pragma: allowlist secret
  { name: "text len 255", value: { t: "text", v: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }, len: 257, blake3: "74fc6508025c578ee6759625b7fcf99261494a81757a1100acdd24ff6fe9c56e" }, // pragma: allowlist secret
  { name: "text len 256", value: { t: "text", v: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }, len: 259, blake3: "920666ebda91a1558c419513157dae5303054cac1af8c7d78846e2b5668292cc" }, // pragma: allowlist secret
  { name: "text repeat 40000", value: { t: "textRepeat", unit: "\u00f1", count: 40000 }, len: 80005, blake3: "77a00012f0a400daa66932df1039d07b836081a7a4df10f008f15e1a3f1820ac" }, // pragma: allowlist secret
  { name: "bytes lcg 0", value: { t: "bytesLcg", seed: 6, count: 0 }, hex: "40" }, // pragma: allowlist secret
  { name: "bytes lcg 23", value: { t: "bytesLcg", seed: 7, count: 23 }, hex: "573de99ced0cdb5c0d11fbf988738c9ac7c76b79da5c7b17" }, // pragma: allowlist secret
  { name: "bytes lcg 24", value: { t: "bytesLcg", seed: 8, count: 24 }, hex: "58183d014cf6b79acaf8930a6d376d7fd53eee6ec5bd0d0bc3d2" }, // pragma: allowlist secret
  { name: "bytes lcg 32", value: { t: "bytesLcg", seed: 9, count: 32 }, hex: "58203d18fb00615939e21619e1e667730fb5167212a0be9b6ee4113d6084bdb0a16b" }, // pragma: allowlist secret
  { name: "bytes lcg 300", value: { t: "bytesLcg", seed: 10, count: 300 }, len: 303, blake3: "e90cfe7a473fe8769147936f4cb92994699b96d5b012df2d2e5fd9787b7237e0" }, // pragma: allowlist secret
  { name: "bytes lcg 70000", value: { t: "bytesLcg", seed: 11, count: 70000 }, len: 70005, blake3: "26fe9982e63dc7e800f7819b70dce97672cdeaa0435b6faeaa4def5be961cc3a" }, // pragma: allowlist secret
  { name: "empty array", value: { t: "array", v: [] }, hex: "80" }, // pragma: allowlist secret
  { name: "nested array", value: { t: "array", v: [{ t: "int", v: 1 }, { t: "array", v: [{ t: "int", v: 2 }, { t: "int", v: 3 }] }, { t: "array", v: [{ t: "text", v: "a" }, { t: "array", v: [] }, { t: "bytesLcg", seed: 5, count: 2 }] }] }, hex: "830182020383616180423cbb" }, // pragma: allowlist secret
  { name: "array 25", value: { t: "array", v: Array.from({ length: 25 }, (_, i) => ({ t: "int" as const, v: i })) }, hex: "9819000102030405060708090a0b0c0d0e0f10111213141516171818" }, // pragma: allowlist secret
];
