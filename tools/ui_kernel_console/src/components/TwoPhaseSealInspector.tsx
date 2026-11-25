/**
 * Inspector del sello en dos fases.
 *
 * No muestra un sello global: cada fila dice qué se comparó y con qué resultado.
 *  - COINCIDE: el cliente lo recalculó o lo comprobó contra el ancla de confianza.
 *  - DECLARADO: lo declara el emisor y lo cubre la firma comprobada; el cliente no lo comprueba.
 *  - NO_VERIFICADO: no se comprobó.
 * Con veredicto negativo solo se muestran los códigos de fallo y el cotejo forense, rotulado como
 * no confiable.
 */

import type { ReactElement } from "react";
import { isAcceptedReceipt } from "../crypto/sealVerifier.ts";
import type { AcceptedReceipt, AssuranceLevel, FailureDiagnostics, VerificationVerdict } from "../types/babylon60.ts";
import { STATE_CLASS } from "./theme.ts";
import { shortHash, visibleText } from "./visibleText.ts";

export interface TwoPhaseSealInspectorProps {
  /** `null` mientras la comprobación está en curso. */
  readonly verdict: VerificationVerdict | null;
}

function Row({
  label,
  value,
  state,
  danger = false,
}: {
  readonly label: string;
  readonly value: string;
  readonly state?: AssuranceLevel;
  readonly danger?: boolean;
}): ReactElement {
  return (
    <div className="b60-row">
      <span className="b60-row__label">{label}</span>
      <span className="b60-row__value">
        <code className={danger ? "b60-row__value b60-danger" : "b60-row__value"}>{value}</code>
        {state !== undefined && <span className={STATE_CLASS[state]}>[{state}]</span>}
      </span>
    </div>
  );
}

function shell(rejected: boolean, status: string, statusClass: string, body: ReactElement): ReactElement {
  return (
    <section aria-label="Inspector del sello en dos fases" className={rejected ? "b60-panel b60-panel--rejected" : "b60-panel"}>
      <header className="b60-panel__header">
        <span>3. TWO-PHASE SEAL INSPECTOR</span>
        <span className={statusClass}>{status}</span>
      </header>
      <div className="b60-panel__body">{body}</div>
    </section>
  );
}

function AcceptedBody({ receipt }: { readonly receipt: AcceptedReceipt }): ReactElement {
  const { payload, assurances } = receipt;
  const seal = payload.cryptographic_seal;
  const clock = payload.causal_clock;
  const audit = payload.audit_metrics;
  return (
    <>
      <Row label="EXECUTION_ID" value={payload.execution_id} state={assurances.manifest_binding} />
      <Row
        label="CAUSAL_CLOCK (E:T:S)"
        value={`epoch=${clock.policy_epoch} | tick=${clock.logical_tick} | seq=${clock.seq_id}`}
        state={assurances.manifest_binding}
      />
      <Row
        label="INGRESS"
        value={`${payload.ingress.agent_id} · ${payload.ingress.policy_profile} · ${payload.manifest_version}`}
        state={assurances.manifest_binding}
      />
      <Row label="INGRESS_PAYLOAD_RAW" value={visibleText(payload.ingress.payload_raw, 240)} state={assurances.manifest_binding} />
      <Row
        label="PHASE_1_MANIFEST_HASH"
        value={`${seal.phase_one_manifest_hash} — recalculado desde ingress y comparado con el declarado`}
        state={assurances.manifest_binding}
      />
      <Row
        label="PHASE_2_MERKLE_ROOT (v1)"
        value={`${seal.phase_two_merkle_root} — recalculada hoja a hoja y comparada con la declarada`}
        state={assurances.merkle_root}
      />
      <Row
        label="AUTHORITY_SIGNATURE"
        value={`firma Ed25519 (COSE_Sign1) del sobre comprobada contra la autoridad admitida ${shortHash(receipt.signer, 10, 6)}`}
        state={assurances.authority_signature}
      />
      <Row label="RECEIPT_HASH" value={`${receipt.receipt_hash} — derivado del sobre comprobado`} state="COINCIDE" />
      <Row
        label="LARSA_COMMIT"
        value={`peso heurístico declarado ${seal.larsa_commit.heuristic_weight} ≥ exigido por el ancla ${receipt.larsa_required_weight} · trace_hash ${shortHash(seal.larsa_commit.trace_hash, 10, 6)}`}
        state={assurances.larsa_commit}
      />
      <Row
        label="LEAN4_PROOF"
        value={`${seal.lean4_proof.theorem_ident} — estado declarado ${seal.lean4_proof.status}, sorry=${seal.lean4_proof.sorry_count}`}
        state={assurances.lean4_proof}
      />
      <Row label="L0_PREV_RECEIPT_HASH" value={audit.prev_receipt_hash} state={assurances.chain_link} />
      <Row label="L0_WORM_TXID" value={`${audit.worm_txid} · ${audit.memory_bytes} B`} state={assurances.worm_audit} />
      <p className="b60-limits">
        Alcance: COINCIDE significa que el cliente recalculó o comprobó ese dato. DECLARADO significa que lo afirma el
        emisor bajo su firma: el cliente no ejecuta Lean ni observa el consenso LARSA. NO_VERIFICADO: el anfitrión no
        aportó el recibo anterior como punto de control. Una firma válida no establece quién controla la clave, ni que
        el efecto descrito ocurriera, ni que la entrada fuera veraz.
      </p>
    </>
  );
}

function orDash(value: string | number | null): string {
  return value === null ? "—" : String(value);
}

function RejectedBody({
  codes,
  diagnostics,
}: {
  readonly codes: readonly string[];
  readonly diagnostics: FailureDiagnostics | null;
}): ReactElement {
  const rootDiffers = diagnostics !== null && diagnostics.computed_merkle_root !== diagnostics.declared_merkle_root;
  const manifestDiffers = diagnostics !== null && diagnostics.computed_manifest_hash !== diagnostics.declared_manifest_hash;
  return (
    <>
      <Row label="FAILURE_CODES" value={codes.join(", ")} danger />
      {diagnostics !== null && (
        <>
          <Row label="DECLARED_MERKLE_ROOT" value={orDash(diagnostics.declared_merkle_root)} />
          <Row
            label="CLIENT_RECOMPUTED_ROOT"
            value={`${orDash(diagnostics.computed_merkle_root)}${diagnostics.computed_merkle_root === null ? "" : rootDiffers ? " — NO COINCIDE" : " — coincide"}`}
            danger={rootDiffers}
          />
          <Row label="DECLARED_MANIFEST_HASH" value={orDash(diagnostics.declared_manifest_hash)} />
          <Row
            label="CLIENT_RECOMPUTED_MANIFEST"
            value={`${orDash(diagnostics.computed_manifest_hash)}${diagnostics.computed_manifest_hash === null ? "" : manifestDiffers ? " — NO COINCIDE" : " — coincide"}`}
            danger={manifestDiffers}
          />
          <Row label="NODE_COUNT" value={orDash(diagnostics.node_count)} />
        </>
      )}
      <p className="b60-limits">
        Cotejo forense de un recibo RECHAZADO: los valores «declarados» proceden de una entrada no confiable y no deben
        usarse para decidir nada.
      </p>
    </>
  );
}

export function TwoPhaseSealInspector({ verdict }: TwoPhaseSealInspectorProps): ReactElement {
  if (verdict === null) {
    return shell(false, "VERIFYING…", "b60-muted", <p className="b60-limits">Comprobaciones locales en curso.</p>);
  }
  if (verdict.ok && isAcceptedReceipt(verdict.receipt)) {
    return shell(false, "COMPROBACIONES LOCALES: COINCIDEN", "b60-ok", <AcceptedBody receipt={verdict.receipt} />);
  }
  const codes = verdict.ok ? ["UNVERIFIED_INPUT"] : [...new Set(verdict.failures.map((f) => f.code))];
  return shell(true, "RECHAZADO", "b60-danger", <RejectedBody codes={codes} diagnostics={verdict.ok ? null : verdict.diagnostics} />);
}
