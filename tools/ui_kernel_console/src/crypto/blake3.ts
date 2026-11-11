/**
 * BLAKE3 (modo hash sin clave, salida de 32 bytes) en TypeScript sin dependencias.
 *
 * Motivo: `INV_C5_ONWIRE_CANON` fija BLAKE3 como hash canónico de formatos nuevos y WebCrypto no lo
 * ofrece. La implementación sigue la referencia pública (IV de SHA-256, 7 rondas, permutación de
 * mensaje, árbol binario de chunks de 1024 bytes) y se contrasta en `tests/blake3.test.ts` con los
 * vectores de `tests/vectors/blake3_kat.json`, generados por la implementación oficial.
 *
 * Solo procesa datos públicos (verificación); no se usa con secretos.
 */

const IV: readonly number[] = [
  0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
];
const MSG_PERMUTATION: readonly number[] = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8];

const CHUNK_START = 1;
const CHUNK_END = 2;
const PARENT = 4;
const ROOT = 8;

const BLOCK_LEN = 64;
const CHUNK_LEN = 1024;
const TWO_32 = 0x1_0000_0000;

/** Longitud máxima admitida: mantiene el contador de chunks en aritmética entera exacta. */
export const BLAKE3_MAX_INPUT_BYTES = 0x4000_0000; // 1 GiB

function rotr(x: number, n: number): number {
  return (x >>> n) | (x << (32 - n));
}

// `s` es Uint32Array: cada asignación reduce módulo 2^32, y las sumas de tres operandos de 32 bits
// caben exactas en un double, de modo que la aritmética coincide con u32::wrapping_add.
function g(s: Uint32Array, a: number, b: number, c: number, d: number, mx: number, my: number): void {
  s[a] = s[a]! + s[b]! + mx;
  s[d] = rotr(s[d]! ^ s[a]!, 16);
  s[c] = s[c]! + s[d]!;
  s[b] = rotr(s[b]! ^ s[c]!, 12);
  s[a] = s[a]! + s[b]! + my;
  s[d] = rotr(s[d]! ^ s[a]!, 8);
  s[c] = s[c]! + s[d]!;
  s[b] = rotr(s[b]! ^ s[c]!, 7);
}

function round(s: Uint32Array, m: Uint32Array): void {
  g(s, 0, 4, 8, 12, m[0]!, m[1]!);
  g(s, 1, 5, 9, 13, m[2]!, m[3]!);
  g(s, 2, 6, 10, 14, m[4]!, m[5]!);
  g(s, 3, 7, 11, 15, m[6]!, m[7]!);
  g(s, 0, 5, 10, 15, m[8]!, m[9]!);
  g(s, 1, 6, 11, 12, m[10]!, m[11]!);
  g(s, 2, 7, 8, 13, m[12]!, m[13]!);
  g(s, 3, 4, 9, 14, m[14]!, m[15]!);
}

/** Función de compresión. Devuelve los 16 words de estado; los 8 primeros son el valor de encadenado. */
function compress(
  cv: Uint32Array,
  blockWords: Uint32Array,
  counter: number,
  blockLen: number,
  flags: number
): Uint32Array {
  const s = new Uint32Array(16);
  for (let i = 0; i < 8; i++) s[i] = cv[i]!;
  for (let i = 0; i < 4; i++) s[8 + i] = IV[i]!;
  s[12] = counter % TWO_32;
  s[13] = Math.floor(counter / TWO_32);
  s[14] = blockLen;
  s[15] = flags;

  let m = blockWords;
  for (let r = 0; r < 7; r++) {
    round(s, m);
    if (r < 6) {
      const next = new Uint32Array(16);
      for (let i = 0; i < 16; i++) next[i] = m[MSG_PERMUTATION[i]!]!;
      m = next;
    }
  }
  for (let i = 0; i < 8; i++) {
    s[i] = s[i]! ^ s[i + 8]!;
    s[i + 8] = s[i + 8]! ^ cv[i]!;
  }
  return s;
}

/** Lee hasta 64 bytes como 16 words little-endian, rellenando con ceros. */
function blockToWords(data: Uint8Array, offset: number, len: number): Uint32Array {
  const words = new Uint32Array(16);
  for (let i = 0; i < len; i++) {
    const w = i >>> 2;
    words[w] = words[w]! | (data[offset + i]! << ((i & 3) * 8));
  }
  return words;
}

interface PendingOutput {
  readonly cv: Uint32Array;
  readonly words: Uint32Array;
  readonly counter: number;
  readonly blockLen: number;
  readonly flags: number;
}

/** Procesa un chunk (1..1024 bytes, o 0 solo para la entrada vacía) hasta dejar pendiente su último bloque. */
function chunkOutput(data: Uint8Array, offset: number, len: number, chunkCounter: number): PendingOutput {
  let cv: Uint32Array = new Uint32Array(IV);
  const blocks = len === 0 ? 1 : Math.ceil(len / BLOCK_LEN);
  for (let b = 0; b < blocks - 1; b++) {
    const words = blockToWords(data, offset + b * BLOCK_LEN, BLOCK_LEN);
    const flags = b === 0 ? CHUNK_START : 0;
    cv = compress(cv, words, chunkCounter, BLOCK_LEN, flags).subarray(0, 8);
  }
  const lastOffset = offset + (blocks - 1) * BLOCK_LEN;
  const lastLen = len - (blocks - 1) * BLOCK_LEN;
  const flags = (blocks === 1 ? CHUNK_START : 0) | CHUNK_END;
  return {
    cv,
    words: blockToWords(data, lastOffset, lastLen),
    counter: chunkCounter,
    blockLen: lastLen,
    flags,
  };
}

function parentOutput(left: Uint32Array, right: Uint32Array): PendingOutput {
  const words = new Uint32Array(16);
  words.set(left.subarray(0, 8), 0);
  words.set(right.subarray(0, 8), 8);
  return { cv: new Uint32Array(IV), words, counter: 0, blockLen: BLOCK_LEN, flags: PARENT };
}

function chainingValue(o: PendingOutput): Uint32Array {
  return compress(o.cv, o.words, o.counter, o.blockLen, o.flags).subarray(0, 8);
}

/** Digest BLAKE3 de 32 bytes. */
export function blake3(input: Uint8Array): Uint8Array {
  const total = input.length;
  if (total > BLAKE3_MAX_INPUT_BYTES) {
    throw new RangeError(`blake3: entrada de ${total} bytes supera el máximo admitido`);
  }
  const chunks = total === 0 ? 1 : Math.ceil(total / CHUNK_LEN);
  const stack: Uint32Array[] = [];

  // Todos los chunks salvo el último se cierran y se fusionan en la pila según los ceros finales
  // del número de chunks completados (un subárbol completo por cada bit a cero).
  for (let c = 0; c < chunks - 1; c++) {
    let cv = chainingValue(chunkOutput(input, c * CHUNK_LEN, CHUNK_LEN, c));
    let completed = c + 1;
    while (completed % 2 === 0) {
      const left = stack.pop();
      if (left === undefined) throw new Error("blake3: pila de subárboles inconsistente");
      cv = chainingValue(parentOutput(left, cv));
      completed = completed / 2;
    }
    stack.push(cv);
  }

  const lastOffset = (chunks - 1) * CHUNK_LEN;
  let output = chunkOutput(input, lastOffset, total - lastOffset, chunks - 1);
  while (stack.length > 0) {
    const left = stack.pop()!;
    output = parentOutput(left, chainingValue(output));
  }

  const rootWords = compress(output.cv, output.words, 0, output.blockLen, output.flags | ROOT);
  const out = new Uint8Array(32);
  for (let i = 0; i < 8; i++) {
    const w = rootWords[i]!;
    out[i * 4] = w & 0xff;
    out[i * 4 + 1] = (w >>> 8) & 0xff;
    out[i * 4 + 2] = (w >>> 16) & 0xff;
    out[i * 4 + 3] = (w >>> 24) & 0xff;
  }
  return out;
}
