/**
 * Verificación Ed25519 sobre WebCrypto nativo, con autoprueba de respuesta conocida.
 *
 * Antes de la primera verificación real se comprueban dos vectores de RFC 8032 §7.1 (deben validar)
 * y uno alterado (no debe validar). Si el runtime no ofrece Ed25519, o responde otra cosa, toda
 * verificación devuelve `UNSUPPORTED_RUNTIME` y el recibo se rechaza: un entorno sin la primitiva,
 * o con una sustituta que acepta cualquier firma, no puede producir un veredicto positivo.
 */

import { fromHexStrict } from "./bytes.ts";
import { classifyPoint, isStrictSignatureEncoding } from "./ed25519Point.ts";

export type Ed25519Outcome = "VALID" | "INVALID" | "BAD_PUBLIC_KEY" | "UNSUPPORTED_RUNTIME";

/** Subconjunto de SubtleCrypto que usa el verificador (permite inyectar un runtime en pruebas). */
export interface SubtleVerifyLike {
  importKey(
    format: "raw",
    keyData: ArrayBuffer,
    algorithm: { name: string },
    extractable: boolean,
    keyUsages: readonly KeyUsage[]
  ): Promise<CryptoKey>;
  verify(algorithm: { name: string }, key: CryptoKey, signature: ArrayBuffer, data: ArrayBuffer): Promise<boolean>;
}

export interface Ed25519Verifier {
  verify(publicKey: Uint8Array, signature: Uint8Array, message: Uint8Array): Promise<Ed25519Outcome>;
}

const ALGORITHM = Object.freeze({ name: "Ed25519" });

// RFC 8032 §7.1, TEST 1 (mensaje vacío) y TEST 2 (mensaje 0x72).
const KAT = [
  {
    publicKey: "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", // pragma: allowlist secret
    message: "",
    signature:
      "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b", // pragma: allowlist secret
  },
  {
    publicKey: "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", // pragma: allowlist secret
    message: "72",
    signature:
      "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00", // pragma: allowlist secret
  },
] as const;

function exactBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.slice().buffer;
}

function unhex(hex: string): Uint8Array {
  const out = fromHexStrict(hex, hex.length / 2);
  if (out === null) throw new Error("vector de autoprueba mal formado");
  return out;
}

async function rawVerify(
  subtle: SubtleVerifyLike,
  publicKey: Uint8Array,
  signature: Uint8Array,
  message: Uint8Array
): Promise<"VALID" | "INVALID" | "IMPORT_FAILED"> {
  let key: CryptoKey;
  try {
    key = await subtle.importKey("raw", exactBuffer(publicKey), ALGORITHM, false, ["verify"]);
  } catch {
    return "IMPORT_FAILED";
  }
  try {
    const ok = await subtle.verify(ALGORITHM, key, exactBuffer(signature), exactBuffer(message));
    return ok === true ? "VALID" : "INVALID";
  } catch {
    return "INVALID";
  }
}

async function selfTest(subtle: SubtleVerifyLike): Promise<boolean> {
  for (const v of KAT) {
    const outcome = await rawVerify(subtle, unhex(v.publicKey), unhex(v.signature), unhex(v.message));
    if (outcome !== "VALID") return false;
  }
  const first = KAT[0];
  const altered = await rawVerify(subtle, unhex(first.publicKey), unhex(first.signature), new Uint8Array([0x00]));
  return altered === "INVALID";
}

/**
 * Crea un verificador ligado a `subtle`. Con `undefined` (runtime sin WebCrypto) todas las
 * verificaciones devuelven `UNSUPPORTED_RUNTIME`.
 */
export function createEd25519Verifier(subtle: SubtleVerifyLike | undefined): Ed25519Verifier {
  let ready: Promise<boolean> | null = null;

  return {
    async verify(publicKey, signature, message) {
      if (subtle === undefined || typeof subtle.importKey !== "function" || typeof subtle.verify !== "function") {
        return "UNSUPPORTED_RUNTIME";
      }
      if (ready === null) {
        ready = selfTest(subtle).catch(() => false);
      }
      if (!(await ready)) return "UNSUPPORTED_RUNTIME";
      // Criterio estricto antes de consultar al runtime: los verificadores nativos difieren en
      // claves de orden pequeño, codificaciones no canónicas y S no reducido.
      if (publicKey.length !== 32 || classifyPoint(publicKey) !== "OK") return "BAD_PUBLIC_KEY";
      if (!isStrictSignatureEncoding(signature)) return "INVALID";

      const outcome = await rawVerify(subtle, publicKey, signature, message);
      return outcome === "IMPORT_FAILED" ? "BAD_PUBLIC_KEY" : outcome;
    },
  };
}

/** WebCrypto del entorno, o `undefined` si no existe. Se consulta en cada uso, no al cargar el módulo. */
export function ambientSubtle(): SubtleVerifyLike | undefined {
  const c = (globalThis as { crypto?: { subtle?: unknown } }).crypto;
  const subtle = c?.subtle;
  return typeof subtle === "object" && subtle !== null ? (subtle as SubtleVerifyLike) : undefined;
}
