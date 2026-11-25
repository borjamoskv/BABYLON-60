/**
 * Traza sintética y mutadores adversariales de la consola de demostración.
 *
 * Todo lo que hay aquí es FIXTURE: los valores (pasos de reducción, bytes, identificador de teorema,
 * hashes previos, peso LARSA) no proceden de ninguna ejecución del kernel ni de ninguna prueba Lean;
 * existen para ejercitar el verificador. El ancla de confianza de la demostración es una clave
 * efímera generada en el propio runtime: demuestra el mecanismo, no la autenticidad de un emisor real.
 *
 * Cada modo declara qué adversario modela y qué códigos de fallo debe producir exactamente; las
 * pruebas comparan esa declaración con el veredicto real.
 */

import { blake3 } from "../crypto/blake3.ts";
import { toHex, utf8 } from "../crypto/bytes.ts";
import {
  generateEphemeralSigner,
  sealReceipt,
  unsealedOf,
  type ReceiptSigner,
  type UnsealedReceipt,
  type WireExecutionPayload,
} from "../crypto/receiptSealer.ts";
import type { SealFailureCode, TrustPolicy } from "../types/babylon60.ts";

export type AdversarialMode =
  | "CLEAN_TRACE"
  | "TAMPER_LEAF_BITFLIP"
  | "TAMPER_NODE_FIELD"
  | "REHASH_WITHOUT_KEYS"
  | "TAMPER_INGRESS_PAYLOAD"
  | "INJECT_DAG_CYCLE"
  | "FORGE_UNVERIFIED_SMT"
  | "DROP_BFT_QUORUM"
  | "RESEAL_WITH_ROGUE_KEY"
  | "MALFORMED_TRANSPORT";

/**
 * Quién altera el recibo en cada modo:
 *  - TRANSPORT: altera bytes en tránsito; no puede firmar.
 *  - FAULTY_EMITTER: emisor defectuoso o comprometido que sella y firma con una autoridad admitida
 *    un recibo incoherente; solo lo detienen las compuertas semánticas.
 *  - OUTSIDER: tercero con sus propias claves, ajenas al ancla de confianza.
 */
export type AdversaryModel = "NONE" | "TRANSPORT" | "FAULTY_EMITTER" | "OUTSIDER";

export interface ModeSpec {
  readonly mode: AdversarialMode;
  readonly label: string;
  readonly adversary: AdversaryModel;
  readonly description: string;
  /** Conjunto exacto de códigos de fallo esperados (vacío = recibo aceptado). */
  readonly expected: readonly SealFailureCode[];
}

/** Peso heurístico LARSA que exige el ancla de la demostración. */
export const DEMO_LARSA_REQUIRED_WEIGHT = 4;

export const MODES: readonly ModeSpec[] = Object.freeze([
  {
    mode: "CLEAN_TRACE",
    label: "Valid Trace",
    adversary: "NONE",
    description: "Recibo íntegro, sellado y firmado por la autoridad de la demostración.",
    expected: [],
  },
  {
    mode: "TAMPER_LEAF_BITFLIP",
    label: "Bit-Flip Leaf Hash",
    adversary: "TRANSPORT",
    description: "Invierte un bit del state_hash de un nodo sin tocar nada más.",
    expected: ["LEAF_HASH_MISMATCH"],
  },
  {
    mode: "TAMPER_NODE_FIELD",
    label: "Tamper Node Field",
    adversary: "TRANSPORT",
    description: "Cambia reduction_steps de un nodo sin recalcular hashes.",
    expected: ["LEAF_HASH_MISMATCH", "MERKLE_ROOT_MISMATCH"],
  },
  {
    mode: "REHASH_WITHOUT_KEYS",
    label: "Re-hash Without Keys",
    adversary: "TRANSPORT",
    description:
      "Convierte el nodo interceptado en COMMITTED y recalcula hojas y raíz de forma coherente, conservando la clave y la firma originales.",
    expected: ["ED25519_SIGNATURE_INVALID"],
  },
  {
    mode: "TAMPER_INGRESS_PAYLOAD",
    label: "Tamper Ingress",
    adversary: "TRANSPORT",
    description: "Sustituye payload_raw del manifiesto de entrada tras el sellado.",
    expected: ["MANIFEST_HASH_MISMATCH"],
  },
  {
    mode: "INJECT_DAG_CYCLE",
    label: "Inject Causal Cycle",
    adversary: "FAULTY_EMITTER",
    description: "Dos nodos se declaran padre uno del otro; hashes y firma son válidos.",
    expected: ["DAG_CYCLE_DETECTED"],
  },
  {
    mode: "FORGE_UNVERIFIED_SMT",
    label: "Forge SMT=false",
    adversary: "FAULTY_EMITTER",
    description: "Un nodo COMMITTED declara smt_verified=false; hashes y firma son válidos.",
    expected: ["COMMITTED_WITHOUT_SMT"],
  },
  {
    mode: "DROP_BFT_QUORUM",
    label: "Drop BFT Quorum",
    adversary: "FAULTY_EMITTER",
    description: `El commit LARSA declara un peso heurístico inferior al que exige el ancla (${DEMO_LARSA_REQUIRED_WEIGHT}); hashes y firma son válidos.`,
    expected: ["QUORUM_INSUFFICIENT"],
  },
  {
    mode: "RESEAL_WITH_ROGUE_KEY",
    label: "Rogue Signer",
    adversary: "OUTSIDER",
    description: "Recibo alterado, resellado de forma coherente y firmado con una clave ajena al ancla de confianza.",
    expected: ["AUTHORITY_NOT_ADMITTED"],
  },
  {
    mode: "MALFORMED_TRANSPORT",
    label: "Malformed Transport",
    adversary: "TRANSPORT",
    description: "execution_dag llega como cadena y aparece un campo desconocido.",
    expected: ["SCHEMA_INVALID"],
  },
] satisfies ModeSpec[]);

/** Hash de 32 bytes derivado de una etiqueta: deja claro en el código que el valor es sintético. */
function syntheticHash(label: string): string {
  return "0x" + toHex(blake3(utf8(`B60-DEMO-FIXTURE:${label}`)));
}

const N0 = "EV_00001048_000000";
const N1 = "EV_00001048_000001";
const N2 = "EV_00001048_000002";
const N3 = "EV_00001048_000003";

/** Traza base: puerta de entrada, comprobación de política, sonda interceptada y commit. */
export function baseUnsealedReceipt(): UnsealedReceipt {
  return {
    execution_id: "b60-exec-01931a7c-8f00-7000-8000-000000000060",
    causal_clock: { policy_epoch: 51, logical_tick: 1048, seq_id: 4096 },
    manifest_version: "v5.1.0",
    ingress: {
      agent_id: "agent://cortex/rea-auditor-01",
      policy_profile: "NEMESIS_ADVERSARIAL",
      payload_raw: '{"op":"fs.write","target":"/etc/hosts","pre_seal":false}',
    },
    nodes: [
      { node_id: N0, parent_ids: [], state_status: "COMMITTED", smt_verified: true, reduction_steps: 14, violation_reason: null },
      { node_id: N1, parent_ids: [N0], state_status: "COMMITTED", smt_verified: true, reduction_steps: 82, violation_reason: null },
      {
        node_id: N2,
        parent_ids: [N0],
        state_status: "INTERCEPTED_NEMESIS",
        smt_verified: true,
        reduction_steps: 19,
        violation_reason: "INV_C5_FLASH_DEFENSE: Side-Effect Without Pre-Seal",
      },
      { node_id: N3, parent_ids: [N1], state_status: "COMMITTED", smt_verified: true, reduction_steps: 31, violation_reason: null },
    ],
    larsa_commit: { trace_hash: syntheticHash("larsa_trace_hash"), heuristic_weight: 5 },
    lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: "Fixture.Synthetic.transition_soundness", sorry_count: 0 },
    audit_metrics: {
      memory_bytes: 16384,
      prev_receipt_hash: syntheticHash("prev_receipt_hash"),
      worm_txid: syntheticHash("worm_txid"),
    },
  };
}

export interface DemoAuthority {
  /** Firmante cuya clave pública es la única autoridad admitida. */
  readonly authority: ReceiptSigner;
  /** Firmante ajeno al ancla. */
  readonly rogue: ReceiptSigner;
  readonly policy: TrustPolicy;
}

export function authorityFromSigners(authority: ReceiptSigner, rogue: ReceiptSigner): DemoAuthority {
  return Object.freeze({
    authority,
    rogue,
    policy: Object.freeze({
      admitted_authorities: Object.freeze([authority.publicKey]),
      larsa_required_weight: DEMO_LARSA_REQUIRED_WEIGHT,
    }),
  });
}

/** Autoridad de demostración con claves efímeras generadas en este runtime. */
export async function createDemoAuthority(): Promise<DemoAuthority> {
  return authorityFromSigners(await generateEphemeralSigner(), await generateEphemeralSigner());
}

function flipLowestBitOfLastHexDigit(hex: string): string {
  const last = Number.parseInt(hex[hex.length - 1]!, 16) ^ 1;
  return hex.slice(0, -1) + last.toString(16);
}

function nodeById(wire: WireExecutionPayload, id: string): WireExecutionPayload["execution_dag"][number] {
  const node = wire.execution_dag.find((n) => n.node_id === id);
  if (node === undefined) throw new Error(`fixture: falta el nodo ${id}`);
  return node;
}

/** Simula el transporte: lo que el cliente recibe es siempre el resultado de `JSON.parse`. */
function throughTransport(value: unknown): unknown {
  return JSON.parse(JSON.stringify(value)) as unknown;
}

function withInterceptedNodeCommitted(u: UnsealedReceipt): UnsealedReceipt {
  return {
    ...u,
    nodes: u.nodes.map((n) => (n.node_id === N2 ? { ...n, state_status: "COMMITTED", violation_reason: null } : n)),
  };
}

/** Construye el valor que recibiría el cliente en el modo indicado. */
export async function buildFixture(mode: AdversarialMode, demo: DemoAuthority): Promise<unknown> {
  const clean = await sealReceipt(baseUnsealedReceipt(), demo.authority);
  const wire = throughTransport(clean) as WireExecutionPayload;
  const unsealed = unsealedOf(wire);

  switch (mode) {
    case "CLEAN_TRACE":
      return wire;

    case "TAMPER_LEAF_BITFLIP": {
      const n3 = nodeById(wire, N3);
      n3.state_hash = flipLowestBitOfLastHexDigit(n3.state_hash);
      return throughTransport(wire);
    }

    case "TAMPER_NODE_FIELD": {
      nodeById(wire, N3).reduction_steps += 1;
      return throughTransport(wire);
    }

    case "REHASH_WITHOUT_KEYS": {
      const rehashed = await sealReceipt(withInterceptedNodeCommitted(unsealed), demo.rogue);
      rehashed.cryptographic_seal.ed25519_public_key = wire.cryptographic_seal.ed25519_public_key;
      rehashed.cryptographic_seal.ed25519_signature = wire.cryptographic_seal.ed25519_signature;
      return throughTransport(rehashed);
    }

    case "TAMPER_INGRESS_PAYLOAD": {
      wire.ingress.payload_raw = '{"op":"fs.write","target":"/etc/shadow","pre_seal":true}';
      return throughTransport(wire);
    }

    case "INJECT_DAG_CYCLE": {
      const nodes = unsealed.nodes.map((n) => (n.node_id === N1 ? { ...n, parent_ids: [N3] } : n));
      return throughTransport(await sealReceipt({ ...unsealed, nodes }, demo.authority));
    }

    case "FORGE_UNVERIFIED_SMT": {
      const nodes = unsealed.nodes.map((n) => (n.node_id === N1 ? { ...n, smt_verified: false } : n));
      return throughTransport(await sealReceipt({ ...unsealed, nodes }, demo.authority));
    }

    case "DROP_BFT_QUORUM": {
      const larsa_commit = { ...unsealed.larsa_commit, heuristic_weight: DEMO_LARSA_REQUIRED_WEIGHT - 1 };
      return throughTransport(await sealReceipt({ ...unsealed, larsa_commit }, demo.authority));
    }

    case "RESEAL_WITH_ROGUE_KEY":
      return throughTransport(await sealReceipt(withInterceptedNodeCommitted(unsealed), demo.rogue));

    case "MALFORMED_TRANSPORT": {
      const broken = wire as unknown as Record<string, unknown>;
      broken["execution_dag"] = "EV_00001048_000000";
      broken["debug_bypass"] = true;
      return throughTransport(broken);
    }
  }
}
