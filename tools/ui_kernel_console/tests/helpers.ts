import assert from "node:assert/strict";
import { ed25519SignerFromSeed, sealReceipt, type ReceiptSigner, type UnsealedReceipt, type WireExecutionPayload } from "../src/crypto/receiptSealer.ts";
import { authorityFromSigners, baseUnsealedReceipt, type DemoAuthority } from "../src/demo/fixture.ts";
import type { VerificationVerdict } from "../src/types/babylon60.ts";

export const N0 = "EV_00001048_000000";
export const N1 = "EV_00001048_000001";
export const N2 = "EV_00001048_000002";
export const N3 = "EV_00001048_000003";

/**
 * Semillas de software de prueba, las mismas que usan los vectores dorados ACS del kernel
 * (el byte 0x11 repetido, 0x22 repetido, ...). Son públicas y no protegen nada.
 */
const TEST_SEED_BYTES = ["11", "22", "33", "44"] as const;

let cachedSigners: Promise<{ authorities: ReceiptSigner[]; outsider: ReceiptSigner }> | null = null;

/** Firmantes de prueba deterministas: tres autoridades y un tercero ajeno al ancla. */
export function testSigners(): Promise<{ authorities: ReceiptSigner[]; outsider: ReceiptSigner }> {
  cachedSigners ??= (async () => {
    const all: ReceiptSigner[] = [];
    for (const byte of TEST_SEED_BYTES) all.push(await ed25519SignerFromSeed(byte.repeat(32)));
    return { authorities: all.slice(0, 3), outsider: all[3]! };
  })();
  return cachedSigners;
}

/** Ancla de pruebas: la clave derivada de la semilla 0x11 repetida es la única autoridad admitida. */
export async function testAuthority(): Promise<DemoAuthority> {
  const { authorities, outsider } = await testSigners();
  return authorityFromSigners(authorities[0]!, outsider);
}

/** Copia por el transporte: el verificador siempre recibe el resultado de JSON.parse. */
export function viaJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

type Mutable<T> = T extends readonly (infer U)[] ? Mutable<U>[] : T extends object ? { -readonly [K in keyof T]: Mutable<T[K]> } : T;
export type MutableUnsealed = Mutable<UnsealedReceipt>;

export async function sealed(mutate?: (u: MutableUnsealed) => void, signer?: ReceiptSigner): Promise<WireExecutionPayload> {
  const demo = await testAuthority();
  const u = viaJson(baseUnsealedReceipt()) as MutableUnsealed;
  mutate?.(u);
  return viaJson(await sealReceipt(u as UnsealedReceipt, signer ?? demo.authority));
}

export function codesOf(verdict: VerificationVerdict): string[] {
  return [...new Set(verdict.failures.map((f) => f.code))].sort();
}

export function expectRejected(verdict: VerificationVerdict, expected: readonly string[], label = ""): void {
  assert.equal(verdict.ok, false, `${label}: debía rechazarse`);
  assert.equal(verdict.receipt, null, label);
  assert.deepEqual(codesOf(verdict), [...expected].sort(), `${label}: ${JSON.stringify(verdict.failures)}`);
}
