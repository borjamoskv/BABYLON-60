/**
 * Codificador CBOR determinista restringido, bisimilar con el del kernel
 * (`src/acs_bridge.rs`, «Restricted deterministic CBOR profile»):
 *
 *   arrays de longitud definida, enteros sin signo, cadenas de bytes y cadenas de texto;
 *   cabeceras en su forma más corta; sin mapas, coma flotante, negativos, etiquetas, valores
 *   simples ni longitudes indefinidas.
 *
 * Sin mapas no hay orden de claves que acordar, y sin coma flotante ni valores simples cada dato
 * tiene una única codificación. El verificador solo codifica (reconstruye los bytes a partir de
 * campos ya validados); nunca decodifica CBOR ajeno.
 */

import { utf8 } from "./bytes.ts";

export class CborEncodeError extends Error {
  override readonly name = "CborEncodeError";
}

/** Entero sin signo (number seguro), texto, bytes o array de lo anterior. */
export type CborValue = number | string | Uint8Array | readonly CborValue[];

const TWO_32 = 0x1_0000_0000;
const MAX_DEPTH = 8;

class ByteWriter {
  private buf = new Uint8Array(256);
  private len = 0;

  private reserve(extra: number): void {
    const needed = this.len + extra;
    if (needed <= this.buf.length) return;
    let cap = this.buf.length;
    while (cap < needed) cap *= 2;
    const next = new Uint8Array(cap);
    next.set(this.buf.subarray(0, this.len));
    this.buf = next;
  }

  byte(b: number): void {
    this.reserve(1);
    this.buf[this.len++] = b;
  }

  bytes(src: Uint8Array): void {
    this.reserve(src.length);
    this.buf.set(src, this.len);
    this.len += src.length;
  }

  finish(): Uint8Array {
    return this.buf.slice(0, this.len);
  }
}

/** Cabecera de tipo mayor con el argumento en su forma más corta (igual que `head` en el kernel). */
function writeHead(w: ByteWriter, major: number, n: number): void {
  if (!Number.isSafeInteger(n) || n < 0) {
    throw new CborEncodeError("argumento CBOR fuera del rango [0, 2^53-1]");
  }
  const m = major << 5;
  if (n < 24) {
    w.byte(m | n);
  } else if (n < 0x100) {
    w.byte(m | 24);
    w.byte(n);
  } else if (n < 0x1_0000) {
    w.byte(m | 25);
    w.byte(n >>> 8);
    w.byte(n & 0xff);
  } else if (n < TWO_32) {
    w.byte(m | 26);
    w.byte((n >>> 24) & 0xff);
    w.byte((n >>> 16) & 0xff);
    w.byte((n >>> 8) & 0xff);
    w.byte(n & 0xff);
  } else {
    const hi = Math.floor(n / TWO_32);
    const lo = n % TWO_32;
    w.byte(m | 27);
    w.byte((hi >>> 24) & 0xff);
    w.byte((hi >>> 16) & 0xff);
    w.byte((hi >>> 8) & 0xff);
    w.byte(hi & 0xff);
    w.byte((lo >>> 24) & 0xff);
    w.byte((lo >>> 16) & 0xff);
    w.byte((lo >>> 8) & 0xff);
    w.byte(lo & 0xff);
  }
}

function writeValue(w: ByteWriter, v: CborValue, depth: number): void {
  if (depth > MAX_DEPTH) throw new CborEncodeError("anidamiento CBOR excesivo");

  if (typeof v === "number") {
    if (!Number.isSafeInteger(v) || v < 0) {
      throw new CborEncodeError("solo se codifican enteros sin signo en [0, 2^53-1]");
    }
    return writeHead(w, 0, v === 0 ? 0 : v); // -0 es el entero cero
  }

  if (typeof v === "string") {
    let encoded: Uint8Array;
    try {
      encoded = utf8(v);
    } catch {
      throw new CborEncodeError("cadena de texto mal formada (sustituto UTF-16 suelto)");
    }
    writeHead(w, 3, encoded.length);
    return w.bytes(encoded);
  }

  if (v instanceof Uint8Array) {
    writeHead(w, 2, v.length);
    return w.bytes(v);
  }

  if (Array.isArray(v)) {
    writeHead(w, 4, v.length);
    for (const item of v as readonly CborValue[]) writeValue(w, item, depth + 1);
    return;
  }

  throw new CborEncodeError("tipo fuera del perfil restringido (solo uint, texto, bytes y arrays)");
}

/** Codifica `value` en el perfil restringido. Lanza `CborEncodeError` ante cualquier otro valor. */
export function encodeCbor(value: CborValue): Uint8Array {
  const w = new ByteWriter();
  writeValue(w, value, 0);
  return w.finish();
}
