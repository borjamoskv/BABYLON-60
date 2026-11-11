/** Generador congruencial compartido con tests/fixtures/generate_vectors.py. */
export function lcgBytes(seed: number, count: number): Uint8Array {
  const out = new Uint8Array(count);
  let x = seed >>> 0;
  for (let i = 0; i < count; i++) {
    x = (Math.imul(1664525, x) + 1013904223) >>> 0;
    out[i] = x >>> 24;
  }
  return out;
}
