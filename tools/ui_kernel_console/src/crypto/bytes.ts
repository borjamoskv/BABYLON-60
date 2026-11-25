/** Utilidades de bytes compartidas por el verificador. Todas son puras y deterministas. */

const HEX = "0123456789abcdef";
const utf8Encoder = new TextEncoder();

/** Hex en minúsculas, sin prefijo. */
export function toHex(bytes: Uint8Array): string {
  let out = "";
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i]!;
    out += HEX[b >>> 4]! + HEX[b & 0x0f]!;
  }
  return out;
}

/**
 * Decodifica hex estricto: solo `[0-9a-f]`, longitud par y exactamente `byteLength` bytes.
 * Devuelve `null` ante cualquier otra entrada; nunca rellena ni trunca.
 */
export function fromHexStrict(hex: string, byteLength: number): Uint8Array | null {
  if (hex.length !== byteLength * 2) return null;
  const out = new Uint8Array(byteLength);
  for (let i = 0; i < byteLength; i++) {
    const hi = hexNibble(hex.charCodeAt(i * 2));
    const lo = hexNibble(hex.charCodeAt(i * 2 + 1));
    if (hi < 0 || lo < 0) return null;
    out[i] = (hi << 4) | lo;
  }
  return out;
}

function hexNibble(code: number): number {
  if (code >= 0x30 && code <= 0x39) return code - 0x30; // 0-9
  if (code >= 0x61 && code <= 0x66) return code - 0x61 + 10; // a-f (solo minúsculas)
  return -1;
}

/** `true` si la cadena no contiene sustitutos UTF-16 sueltos (equivale a String.prototype.isWellFormed). */
export function isWellFormedString(s: string): boolean {
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff) {
      const next = i + 1 < s.length ? s.charCodeAt(i + 1) : 0;
      if (next < 0xdc00 || next > 0xdfff) return false;
      i++;
    } else if (c >= 0xdc00 && c <= 0xdfff) {
      return false;
    }
  }
  return true;
}

/**
 * UTF-8 de una cadena bien formada. Lanza si hay sustitutos sueltos: TextEncoder los sustituiría por
 * U+FFFD y dos cadenas distintas producirían los mismos bytes canónicos.
 */
export function utf8(s: string): Uint8Array {
  if (!isWellFormedString(s)) {
    throw new TypeError("utf8: la cadena contiene sustitutos UTF-16 sueltos");
  }
  return utf8Encoder.encode(s);
}

/** Orden lexicográfico por bytes (el mismo que `Ord` para `[u8]` en Rust y `bytes` en Python). */
export function compareBytes(a: Uint8Array, b: Uint8Array): number {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    const d = a[i]! - b[i]!;
    if (d !== 0) return d < 0 ? -1 : 1;
  }
  return a.length === b.length ? 0 : a.length < b.length ? -1 : 1;
}

export function bytesEqual(a: Uint8Array, b: Uint8Array): boolean {
  return a.length === b.length && compareBytes(a, b) === 0;
}

export function concatBytes(...parts: readonly Uint8Array[]): Uint8Array {
  let total = 0;
  for (const p of parts) total += p.length;
  const out = new Uint8Array(total);
  let offset = 0;
  for (const p of parts) {
    out.set(p, offset);
    offset += p.length;
  }
  return out;
}

/** Entero sin signo de 64 bits en little-endian a partir de un entero seguro no negativo. */
export function u64le(n: number): Uint8Array {
  if (!Number.isSafeInteger(n) || n < 0) {
    throw new RangeError("u64le: se requiere un entero seguro no negativo");
  }
  const out = new Uint8Array(8);
  let lo = n % 0x1_0000_0000;
  let hi = Math.floor(n / 0x1_0000_0000);
  for (let i = 0; i < 4; i++) {
    out[i] = lo & 0xff;
    lo = Math.floor(lo / 256);
    out[4 + i] = hi & 0xff;
    hi = Math.floor(hi / 256);
  }
  return out;
}
