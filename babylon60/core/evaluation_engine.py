import math
import secrets
from datetime import datetime, timezone
from typing import Any

from babylon60.core.crypto import Ed25519Signer, canonicalize_cbor, hash_sha3_256


class EvaluatorT2:

    def __init__(self, signer: Ed25519Signer) -> None:
        self.signer = signer
        self.LAMBDA_Q = 0.8
        self.LAMBDA_L = 0.1
        self.LAMBDA_C = 0.1
        self.MAX_TTFT_MS = 10000.0
        self.MAX_COST_MICROUSD = 1000000.0
        self.P_FAIL = 5000
        self.P_PRIVACY = 20000

    def _jcs_hash(self, payload: dict[str, Any]) -> str:
        return hash_sha3_256(canonicalize_cbor(payload))

    def calculate_utility(self, quality_bp: int, execution_receipt: dict[str, Any], privacy_violation: bool=False) -> float:
        status = execution_receipt.get('status', 'success')
        is_fail = 1 if status != 'success' else 0
        ttft_ms = float(execution_receipt.get('ttft_ms', self.MAX_TTFT_MS))
        cost = float(execution_receipt.get('cost_microusd', self.MAX_COST_MICROUSD))
        L_e = max(0.0, 10000.0 * max(0.0, 1.0 - ttft_ms / self.MAX_TTFT_MS))
        log_cost = math.log1p(cost)
        log_max = math.log1p(self.MAX_COST_MICROUSD)
        C_e = max(0.0, 10000.0 * max(0.0, 1.0 - log_cost / log_max))
        U_e = self.LAMBDA_Q * float(quality_bp) + self.LAMBDA_L * L_e + self.LAMBDA_C * C_e
        U_e -= is_fail * self.P_FAIL
        if privacy_violation:
            U_e -= self.P_PRIVACY
        if not privacy_violation:
            return min(10000.0, max(0.0, U_e))
        return max(0.0, U_e)

    def compute_regret(self, decision_receipt: dict[str, Any], primary_execution: dict[str, Any], shadow_executions: list[dict[str, Any]], quality_scores: dict[str, int]) -> dict[str, Any]:
        primary_quality = quality_scores.get(primary_execution['receipt_id'], 0)
        u_primary = self.calculate_utility(primary_quality, primary_execution['payload'])
        propensities = {s['model']: s['propensity_score'] for s in decision_receipt['payload'].get('shadow_selections', [])}
        shadow_results = []
        weighted_regret_sum = 0.0
        weight_sum = 0.0
        max_shadow_u = 0.0
        for shadow in shadow_executions:
            model_alias = shadow['payload']['model_alias']
            shadow_q = quality_scores.get(shadow['receipt_id'], 0)
            u_shadow = self.calculate_utility(shadow_q, shadow['payload'])
            if u_shadow > max_shadow_u:
                max_shadow_u = u_shadow
            regret_m = max(0.0, u_shadow - u_primary)
            pi_m = propensities.get(model_alias, 1.0)
            weight = 1.0 / pi_m
            weighted_regret_sum += weight * regret_m
            weight_sum += weight
            shadow_results.append({'execution_receipt_id': shadow['receipt_id'], 'model_alias': model_alias, 'quality_basis_points': shadow_q, 'utility_basis_points': u_shadow, 'pairwise_regret_basis_points': regret_m, 'propensity_score': pi_m})
        ips_regret = weighted_regret_sum / weight_sum if weight_sum > 0 else 0.0
        proxy_regret_global = max(0.0, max_shadow_u - u_primary)
        eval_payload = {'decision_receipt_hash': decision_receipt['payload_hash'], 'primary_execution_receipt_id': primary_execution['receipt_id'], 'primary_utility_basis_points': u_primary, 'observed_proxy_regret_basis_points': proxy_regret_global, 'ips_weighted_regret_basis_points': ips_regret, 'shadow_evaluations': shadow_results}
        eval_hash = self._jcs_hash(eval_payload)
        evaluation_receipt = {'schema': 'proof-of-route/evaluation/v0.2', 'receipt_id': f'ev_{secrets.token_hex(8)}', 'issued_at': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'), 'payload': eval_payload, 'payload_hash': eval_hash, 'signature': {'algorithm': 'Ed25519', 'key_id': self.signer.key_id, 'public_key': self.signer.public_key_hex, 'value': self.signer.sign(eval_hash)}}
        return evaluation_receipt
if __name__ == '__main__':
    signer = Ed25519Signer()
    evaluator = EvaluatorT2(signer)
    print('EvaluatorT2 initialized in strict IPS mode (Basis Points).')