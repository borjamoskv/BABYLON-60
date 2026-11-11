/**
 * Comprobaciones sobre el texto JSON antes de verificarlo, las mismas que aplica el crate de
 * referencia (`rust/src/json_text.rs` y el propio `serde_json`). Fijan una única forma aceptable del
 * recibo en texto, de modo que `JSON.parse` y `serde_json` acepten exactamente los mismos textos:
 *
 * - números: solo enteros en forma canónica, sin fracción, sin exponente y sin `-0`. `JSON.parse`
 *   convierte `14.0` en `14`; `serde_json` lo conserva como flotante y su esquema lo rechaza;
 * - anidamiento: como máximo 127 contenedores, el límite de recursión de `serde_json`;
 * - sustitutos UTF-16: solo en pares válidos, escapados o no. `JSON.parse` admite `"\ud800"`;
 *   `serde_json` no, y una cadena así no tiene codificación UTF-8.
 *
 * Precondición: `text` ya fue aceptado por `JSON.parse`.
 */

/** Profundidad máxima de anidamiento admitida. */
export const MAX_JSON_DEPTH = 127;

/** Detalle común a todo texto que `serde_json` no llegaría a interpretar. */
export const JSON_FORM_DETAIL = "el texto recibido no es JSON válido en la forma admitida";

const isHigh = (u: number): boolean => u >= 0xd800 && u <= 0xdbff;
const isLow = (u: number): boolean => u >= 0xdc00 && u <= 0xdfff;
const HEX4 = /^[0-9a-fA-F]{4}$/;

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

const NUMBER_CHAR = /[0-9.eE+-]/;

/**
 * Motivo por el que `serde_json` no aceptaría el texto, o `null`. Como en Rust, los defectos de
 * forma (anidamiento, sustitutos) prevalecen sobre los números, que solo se examinan después.
 */
export function jsonTextIssue(text: string): string | null {
  let depth = 0;
  let firstBadNumber: string | null = null;
  let i = 0;
  while (i < text.length) {
    const unit = text.charCodeAt(i);
    if (unit === 0x22) {
      const length = stringLiteralLength(text, i);
      if (length < 0) return JSON_FORM_DETAIL;
      i += length;
    } else if (unit === 0x5b || unit === 0x7b) {
      depth += 1;
      if (depth > MAX_JSON_DEPTH) return JSON_FORM_DETAIL;
      i += 1;
    } else if (unit === 0x5d || unit === 0x7d) {
      depth -= 1;
      i += 1;
    } else if (unit === 0x2d || (unit >= 0x30 && unit <= 0x39)) {
      const start = i;
      i += 1;
      while (i < text.length && NUMBER_CHAR.test(text[i]!)) i += 1;
      const token = text.slice(start, i);
      if (firstBadNumber === null && (/[.eE]/.test(token) || token === "-0")) firstBadNumber = token;
    } else {
      i += 1;
    }
  }
  return firstBadNumber === null ? null : `número no entero o no canónico en el texto: ${firstBadNumber}`;
}
