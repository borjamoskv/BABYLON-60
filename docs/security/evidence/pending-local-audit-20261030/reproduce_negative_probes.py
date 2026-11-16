from __future__ import annotations
import json
from babylon60.verification.finding_contract import Finding, ReproductionRun, Outcome, is_verified
from babylon60.memory.provenance_arbiter import (ProvenanceEnvelope, EventIdentityTuple, DerivationKind, AttributionClaim, ClaimScope, ProvenanceLevel, evaluate_provenance_claim)

def main() -> None:
    finding = Finding("malformed-digest", "behavior", "z" * 64, "producer")
    run = ReproductionRun("malformed-digest", "z" * 64, "behavior", Outcome.REPRODUCED, "verifier")
    envelope = ProvenanceEnvelope(content="fixture", host_platform="fixture", derivation_kind=DerivationKind.ORIGINAL_MESSAGE, event_tuple=EventIdentityTuple("fixture", "c", "m", 1, 1), native_export_digest_b3="b3:not-a-digest")
    claim = AttributionClaim("forged-export", ClaimScope.NATIVE_MESSAGE_TRANSCRIPT, claimed_platform="fixture", claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED)
    decision = evaluate_provenance_claim(envelope, claim)
    result = {"finding_contract_accepts_nonhex_digest": is_verified(finding, [run]), "provenance_outcome_for_malformed_export": decision.outcome.value, "effects_executed": False}
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["finding_contract_accepts_nonhex_digest"] or decision.outcome.value == "ATTESTED" else 0)

if __name__ == "__main__":
    main()
