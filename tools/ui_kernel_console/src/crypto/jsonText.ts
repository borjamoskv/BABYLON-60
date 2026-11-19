/**
 * Comprobaciones sobre el texto JSON antes de verificarlo, las mismas que aplica el crate de
 * referencia (`rust/src/json_text.rs`, `rust/src/verify.rs`). Fijan una única forma aceptable del
 * texto, de modo que `JSON.parse` y `serde_json` acepten exactamente los mismos textos:
 *
 * - claves repetidas: ninguna, en ningún objeto. `JSON.parse` y `serde_json` conservan la última y
 *   descartan la primera; un consumidor que lea la primera vería un valor que nada cubre;
 * - anidamiento: como máximo 127 contenedores, el límite de recursión de `serde_json`;
 * - sustitutos UTF-16: solo en pares válidos, escapados o no. `JSON.parse` admite `"\ud800"`;
 *   `serde_json` no, y una cadena así no tiene codificación UTF-8;
 * - números, solo en el recibo (`mode === "receipt"`): enteros canónicos, sin fracción, sin
 *   exponente y sin `-0`. En el ancla (`mode === "anchor"`) un número vale por su valor, como en
 *   `Number.isSafeInteger` tras `JSON.parse`, así que `4.0` y `4e0` son el entero 4.
 *
 * Precondición: `text` ya fue aceptado por `JSON.parse`.
 */

/** Profundidad máxima de anidamiento admitida. */
export const MAX_JSON_DEPTH = 127;

/** Detalle común a todo texto que `serde_json` no llegaría a interpretar. */
export const JSON_FORM_DETAIL = "el texto recibido no es JSON válido en la forma admitida";

/** Qué comprobar en los números: el recibo exige forma canónica; el ancla, solo valor. */
export type JsonTextMode = "receipt" | "anchor";

const isHigh = (u: number): boolean => u >= 0xd800 && u <= 0xdbff;
const isLow = (u: number): boolean => u >= 0xdc00 && u <= 0xdfff;
const HEX4 = /^[0-9a-fA-F]{4}$/;
const NUMBER_CHAR = /[0-9.eE+-]/;

/** Unidad UTF-16 de un escape `\uXXXX` que empieza en `i`, o `null` si no lo hay. */
function escapedUnit(text: string, i: number): number | null {
  if (text.charCodeAt(i) !== 0x5c || text.charCodeAt(i + 1) !== 0x75) return null;
  const hex = text.slice(i + 2, i + 6);
  return HEX4.test(hex) ? parseInt(hex, 16) : null;
}

/**
 * Longitud del literal de cadena que empieza en `start` (comillas incluidas), o -1 si contiene
 * un sustituto UTF-16 sin pareja, escapado o no.
 */
function stringLiteralLength(text: string, start: number): number {
  let i = start + 1;
  while (i < text.length) {
    const unit = text.charCodeAt(i);
    if (unit === 0x22) return i + 1 - start;
    if (unit === 0x5c) {
      const escaped = escapedUnit(text, i);
      if (escaped === null) {
        i += 2;
      } else if (isHigh(escaped)) {
        const pair = escapedUnit(text, i + 6);
        if (pair === null || !isLow(pair)) return -1;
        i += 12;
      } else if (isLow(escaped)) {
        return -1;
      } else {
        i += 6;
      }
    } else if (isHigh(unit)) {
      if (!isLow(text.charCodeAt(i + 1))) return -1;
      i += 2;
    } else if (isLow(unit)) {
      return -1;
    } else {
      i += 1;
    }
  }
  return -1;
}

/** Primer carácter que no es espacio JSON desde `at`, o `undefined`. */
function nextSignificantChar(text: string, at: number): string | undefined {
  for (let i = at; i < text.length; i++) {
    const c = text[i]!;
    if (c !== " " && c !== "\t" && c !== "\n" && c !== "\r") return c;
  }
  return undefined;
}

/**
 * Motivo por el que el texto no se admite, o `null`. Recorre la estructura: una cadena seguida de
 * `:` dentro de un objeto es una clave, y se compara ya decodificada (`"a"` y `"a"` son la
 * misma). Claves repetidas en objetos distintos no cuentan. Como en Rust, los defectos de forma
 * (anidamiento, sustitutos, claves repetidas) prevalecen sobre los números.
 */
export function jsonTextIssue(text: string, mode: JsonTextMode = "receipt"): string | null {
  // Pila de contenedores: un Set con las claves vistas para un objeto, `null` para un array.
  const stack: Array<Set<string> | null> = [];
  let firstBadNumber: string | null = null;
  let i = 0;
  while (i < text.length) {
    const unit = text.charCodeAt(i);
    if (unit === 0x22) {
      const length = stringLiteralLength(text, i);
      if (length < 0) return JSON_FORM_DETAIL;
      const top = stack[stack.length - 1];
      if (top !== undefined && top !== null && nextSignificantChar(text, i + length) === ":") {
        // El literal ya fue validado por JSON.parse, así que decodificarlo es seguro.
        const key = JSON.parse(text.slice(i, i + length)) as string;
        if (top.has(key)) return `clave duplicada: ${key}`;
        top.add(key);
      }
      i += length;
    } else if (unit === 0x7b || unit === 0x5b) {
      stack.push(unit === 0x7b ? new Set<string>() : null);
      if (stack.length > MAX_JSON_DEPTH) return JSON_FORM_DETAIL;
      i += 1;
    } else if (unit === 0x7d || unit === 0x5d) {
      stack.pop();
      i += 1;
    } else if (unit === 0x2d || (unit >= 0x30 && unit <= 0x39)) {
      const start = i;
      i += 1;
      while (i < text.length && NUMBER_CHAR.test(text[i]!)) i += 1;
      const token = text.slice(start, i);
      const canonical = !(/[.eE]/.test(token) || token === "-0");
      if (mode === "receipt" && firstBadNumber === null && !canonical) firstBadNumber = token;
    } else {
      i += 1;
    }
  }
  return firstBadNumber === null ? null : `número no entero o no canónico en el texto: ${firstBadNumber}`;
}
