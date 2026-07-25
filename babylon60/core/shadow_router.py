from __future__ import annotations
import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from babylon60.core.crypto import Ed25519Signer, canonicalize_cbor, hash_sha3_256

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

class ShadowRouter:

    def __init__(self, signer: Ed25519Signer) -> None:
        key_material = os.environ.get('CORTEX_SHADOW_HMAC_KEY') or os.environ.get('CORTEX_MASTER_KEY')
        if not key_material:
            raise RuntimeError('FATAL: CORTEX_SHADOW_HMAC_KEY or CORTEX_MASTER_KEY env var required for proof-of-route commitments. Zero static fallback permitted.')
        self._commitment_key = key_material.encode('utf-8')
        self.signer = signer
        self.shadow_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    def _commit(self, data: bytes) -> str:
        return f'hmac-sha256:{hmac.new(self._commitment_key, data, hashlib.sha256).hexdigest()}'

    @staticmethod
    def _sha256_of(data: bytes) -> str:
        return f'sha256:{hashlib.sha256(data).hexdigest()}'

    def _jcs_hash(self, payload: Dict[str, Any]) -> str:
        return hash_sha3_256(canonicalize_cbor(payload))

    def _check_shadow_eligibility(self, context: Dict[str, Any]) -> bool:
        if context.get('contains_pii', False):
            return False
        if context.get('contains_secrets', False):
            return False
        if not context.get('consent_granted', True):
            return False
        return True

    async def _execute_route(self, model_id: str, prompt: str) -> Dict[str, Any]:
        start_ns = time.monotonic_ns()
        await asyncio.sleep(0.05)
        first_byte_ns = time.monotonic_ns()
        await asyncio.sleep(0.1)
        completed_ns = time.monotonic_ns()
        ttft_ms = (first_byte_ns - start_ns) // 1000000
        total_latency_ms = (completed_ns - start_ns) // 1000000
        return {'status': 'success', 'mode': 'simulation', 'ttft_ms': ttft_ms, 'total_latency_ms': total_latency_ms, 'input_tokens': 100, 'output_tokens': 50, 'cost_microusd': 4200, 'fallback_used': False, 'response_commitment': self._commit(b'response|' + prompt.encode('utf-8')), 'provider_receipt_hash': None}

    async def route_request(self, prompt: str, context: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        request_id = f'req_{secrets.token_hex(8)}'
        primary_model = 'provider-x/gemini-2.0-flash-2026-07-01'
        shadow_models = ['provider-y/agent-3.5-model-2026-06']
        policy_id = 'arcstride-v4.2.1'
        candidate_set = sorted([primary_model, *shadow_models])
        decision_payload = {'request_commitment': self._commit(b'request|' + prompt.encode('utf-8')), 'policy_id': policy_id, 'policy_hash': self._sha256_of(policy_id.encode('utf-8')), 'candidate_set_hash': self._sha256_of(json.dumps(candidate_set, separators=(',', ':')).encode('utf-8')), 'mode': 'simulation', 'selected_route': {'provider': 'provider-x', 'model_alias': 'gemini-2.0-flash', 'model_version': 'gemini-2.0-flash-2026-07-01', 'region': 'eu-west'}, 'predictions': {'quality_lcb_basis_points': 8400, 'ttft_p95_ms': 3400, 'expected_cost_microusd': 4200, 'failure_probability_basis_points': 60}, 'selection_propensity_basis_points': 9200, 'route_confidence_basis_points': 8300, 'shadow_eligible': self._check_shadow_eligibility(context)}
        decision_hash = self._jcs_hash(decision_payload)
        decision_receipt = {'schema': 'proof-of-route/decision/v0.2', 'receipt_id': f'dr_{secrets.token_hex(8)}', 'issued_at': _utc_now_iso(), 'payload': decision_payload, 'payload_hash': decision_hash, 'signature': {'algorithm': 'Ed25519', 'key_id': self.signer.key_id if self.signer else '', 'public_key': self.signer.public_key_hex if self.signer else '', 'value': self.signer.sign(decision_hash) if self.signer else ''}}
        if decision_payload['shadow_eligible']:
            for sm in shadow_models:
                self.shadow_queue.put_nowait({'model': sm, 'prompt': prompt, 'request_id': request_id, 'decision_hash': decision_hash})
        execution_metrics = await self._execute_route(primary_model, prompt)
        execution_payload = execution_metrics
        exec_hash = self._jcs_hash(execution_payload)
        execution_receipt = {'schema': 'proof-of-route/execution/v0.2', 'receipt_id': f'er_{secrets.token_hex(8)}', 'issued_at': _utc_now_iso(), 'decision_receipt_hash': decision_hash, 'payload': execution_payload, 'payload_hash': exec_hash, 'signature': {'algorithm': 'Ed25519', 'key_id': self.signer.key_id if self.signer else '', 'public_key': self.signer.public_key_hex if self.signer else '', 'value': self.signer.sign(exec_hash) if self.signer else ''}}
        return (decision_receipt, execution_receipt)

async def demo() -> None:
    os.environ.setdefault('CORTEX_SHADOW_HMAC_KEY', secrets.token_hex(32))
    signer = Ed25519Signer()
    router = ShadowRouter(signer)
    t0_receipt, t1_receipt = await router.route_request('Explain quantum gravity', {'contains_pii': False})
    print('Decision Receipt (T0):')
    print(json.dumps(t0_receipt, indent=2))
    print('\nExecution Receipt (T1):')
    print(json.dumps(t1_receipt, indent=2))
    print(f'\nShadows in isolated queue: {router.shadow_queue.qsize()}')
if __name__ == '__main__':
    asyncio.run(demo())