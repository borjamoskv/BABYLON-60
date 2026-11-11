/**
 * Texto apto para una consola forense: los caracteres de control, de formato bidireccional y de
 * anchura cero se muestran como escapes visibles, de modo que lo que se lee coincide con lo que hay.
 * Las clases se enumeran por rango fijo para no depender de la versión de Unicode del motor.
 */

const INVISIBLE_RANGES: readonly (readonly [number, number])[] = [
  [0x0000, 0x001f],
  [0x007f, 0x009f],
  [0x00ad, 0x00ad],
  [0x061c, 0x061c],
  [0x180e, 0x180e],
  [0x200b, 0x200f],
  [0x2028, 0x202e],
  [0x2060, 0x206f],
  [0xfeff, 0xfeff],
  [0xfff9, 0xfffb],
  [0x1d173, 0x1d17a],
  [0xe0000, 0xe007f],
];

function isInvisible(cp: number): boolean {
  for (const [lo, hi] of INVISIBLE_RANGES) {
    if (cp >= lo && cp <= hi) return true;
  }
  return false;
}

/** Devuelve `text` con escapes visibles y, si supera `maxCodePoints`, truncado con indicación de cuánto falta. */
export function visibleText(text: string, maxCodePoints = 512): string {
  let out = "";
  let count = 0;
  let consumed = 0;
  for (const ch of text) {
    if (count >= maxCodePoints) break;
    const cp = ch.codePointAt(0)!;
    const lone = cp >= 0xd800 && cp <= 0xdfff;
    out += lone || isInvisible(cp) ? `\\u{${cp.toString(16).toUpperCase()}}` : ch;
    count++;
    consumed += ch.length;
  }
  if (consumed < text.length) out += `… (+${text.length - consumed})`;
  return out;
}

/** Abrevia un hash `0x…`/`b3:…` conservando `head` caracteres iniciales y `tail` finales (0 = ninguno). */
export function shortHash(hash: string, head = 10, tail = 6): string {
  if (hash.length <= head + tail + 1) return hash;
  // slice(-0) devolvería la cadena completa: el sufijo solo existe si tail > 0.
  return `${hash.slice(0, head)}…${tail > 0 ? hash.slice(-tail) : ""}`;
}
