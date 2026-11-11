/**
 * Validación de puntos Ed25519 (aritmética pública, sin secretos).
 *
 * Motivo: los verificadores Ed25519 nativos no coinciden en los casos degenerados. Con una clave
 * pública de orden pequeño (por ejemplo la identidad `0x01 00…00`) hay runtimes que aceptan la firma
 * trivial `R = identidad, S = 0` para cualquier mensaje; `tests/ed25519Point.test.ts` lo reproduce en
 * este runtime. Una clave así en el ancla de confianza anularía toda la verificación, y una `R`
 * así haría que este cliente aceptase lo que `verify_strict` de ed25519-dalek rechaza.
 *
 * Criterio (el de RFC 8032 estricto / `verify_strict`):
 *  - codificación canónica: y < p, y si x = 0 el bit de signo es 0;
 *  - el punto está en la curva;
 *  - el punto no es de orden pequeño: [8]P ≠ identidad;
 *  - el escalar S de la firma es canónico: S < ℓ.
 */

const P = 2n ** 255n - 19n;
const L = 2n ** 252n + 27742317777372353535851937790883648493n;

function mod(a: bigint): bigint {
  const r = a % P;
  return r >= 0n ? r : r + P;
}

function modPow(base: bigint, exponent: bigint): bigint {
  let result = 1n;
  let b = mod(base);
  let e = exponent;
  while (e > 0n) {
    if ((e & 1n) === 1n) result = (result * b) % P;
    b = (b * b) % P;
    e >>= 1n;
  }
  return result;
}

function inv(a: bigint): bigint {
  return modPow(a, P - 2n);
}

/** d = −121665/121666 (mod p), parámetro de la curva −x² + y² = 1 + d·x²·y². */
const D = mod(-121665n * inv(121666n));
/** √−1 (mod p). */
const SQRT_M1 = modPow(2n, (P - 1n) / 4n);

export interface AffinePoint {
  readonly x: bigint;
  readonly y: bigint;
}

export const IDENTITY: AffinePoint = Object.freeze({ x: 0n, y: 1n });

function littleEndianToBigInt(bytes: Uint8Array): bigint {
  let value = 0n;
  for (let i = bytes.length - 1; i >= 0; i--) value = (value << 8n) | BigInt(bytes[i]!);
  return value;
}

/** Decodifica un punto comprimido de 32 bytes con las reglas estrictas; `null` si no es canónico o no está en la curva. */
export function decodePointStrict(bytes: Uint8Array): AffinePoint | null {
  if (bytes.length !== 32) return null;
  const raw = littleEndianToBigInt(bytes);
  const sign = raw >> 255n;
  const y = raw & ((1n << 255n) - 1n);
  if (y >= P) return null;

  const y2 = (y * y) % P;
  const u = mod(y2 - 1n);
  const v = mod(D * y2 + 1n);
  // x = u·v³·(u·v⁷)^((p−5)/8)
  const v3 = (((v * v) % P) * v) % P;
  const v7 = (((v3 * v3) % P) * v) % P;
  let x = (((u * v3) % P) * modPow((u * v7) % P, (P - 5n) / 8n)) % P;
  const vx2 = (v * ((x * x) % P)) % P;
  if (vx2 === u) {
    // raíz correcta
  } else if (vx2 === mod(-u)) {
    x = (x * SQRT_M1) % P;
  } else {
    return null;
  }
  if (x === 0n && sign === 1n) return null;
  if ((x & 1n) !== sign) x = mod(-x);
  return { x, y };
}

/** Suma en la curva de Edwards torcida con a = −1 (fórmula afín completa). */
export function pointAdd(p: AffinePoint, q: AffinePoint): AffinePoint {
  const x1y2 = (p.x * q.y) % P;
  const y1x2 = (p.y * q.x) % P;
  const y1y2 = (p.y * q.y) % P;
  const x1x2 = (p.x * q.x) % P;
  const dxy = (((D * x1x2) % P) * y1y2) % P;
  const x3 = (mod(x1y2 + y1x2) * inv(mod(1n + dxy))) % P;
  const y3 = (mod(y1y2 + x1x2) * inv(mod(1n - dxy))) % P;
  return { x: x3, y: y3 };
}

export function isIdentity(p: AffinePoint): boolean {
  return p.x === 0n && p.y === 1n;
}

/** `true` si [8]P es la identidad (P pertenece al subgrupo de torsión de orden 8). */
export function hasSmallOrder(p: AffinePoint): boolean {
  let q = p;
  for (let i = 0; i < 3; i++) q = pointAdd(q, q);
  return isIdentity(q);
}

export type PointVerdict = "OK" | "NON_CANONICAL_OR_OFF_CURVE" | "SMALL_ORDER";

/** Clasifica una codificación de 32 bytes como clave pública (o componente R) aceptable o no. */
export function classifyPoint(bytes: Uint8Array): PointVerdict {
  const point = decodePointStrict(bytes);
  if (point === null) return "NON_CANONICAL_OR_OFF_CURVE";
  return hasSmallOrder(point) ? "SMALL_ORDER" : "OK";
}

/** `true` si la firma de 64 bytes tiene R aceptable y S canónico (S < ℓ). No verifica la firma. */
export function isStrictSignatureEncoding(signature: Uint8Array): boolean {
  if (signature.length !== 64) return false;
  if (classifyPoint(signature.subarray(0, 32)) !== "OK") return false;
  return littleEndianToBigInt(signature.subarray(32, 64)) < L;
}

/** Orden del subgrupo primo, expuesto para pruebas de la ley de grupo. */
export const SUBGROUP_ORDER = L;
