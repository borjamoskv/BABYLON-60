import asyncio
import time
import hashlib
import json
import secrets
from typing import Dict, Any, Tuple


class Ed25519Signer:
    def sign(self, payload_hash: str) -> str:
        return "base64url:mock_signature"


class ShadowRouter:
    def __init__(self) -> None:
        self.signer = None  # type: ignore
        self.shadow_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    def _jcs_hash(self, payload: dict) -> str:
        canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    def _check_shadow_eligibility(self, context: dict) -> bool:
        if context.get("contains_pii", False):
            return False
        if context.get("contains_secrets", False):
            return False
        if not context.get("consent_granted", True):
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
        return {
            "status": "success",
            "ttft_ms": ttft_ms,
            "total_latency_ms": total_latency_ms,
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_microusd": 4200,
            "fallback_used": False,
            "response_commitment": f"hmac-sha256:{secrets.token_hex(32)}",
            "provider_receipt_hash": f"sha256:{secrets.token_hex(32)}",
        }

    async def route_request(self, prompt: str, context: dict) -> Tuple[Dict, Dict]:
        request_id = f"req_{secrets.token_hex(8)}"
        primary_model = "provider-x/gemini-2.0-flash-2026-07-01"
        shadow_models = ["provider-y/claude-3.5-sonnet-2026-06"]
        decision_payload = {
            "request_commitment": f"hmac-sha256:{secrets.token_hex(32)}",
            "policy_id": "arcstride-v4.2.1",
            "policy_hash": f"sha256:{secrets.token_hex(32)}",
            "candidate_set_hash": f"sha256:{secrets.token_hex(32)}",
            "selected_route": {
                "provider": "provider-x",
                "model_alias": "gemini-2.0-flash",
                "model_version": "gemini-2.0-flash-2026-07-01",
                "region": "eu-west",
            },
            "predictions": {
                "quality_lcb_basis_points": 8400,
                "ttft_p95_ms": 3400,
                "expected_cost_microusd": 4200,
                "failure_probability_basis_points": 60,
            },
            "selection_propensity_basis_points": 9200,
            "route_confidence_basis_points": 8300,
            "shadow_eligible": self._check_shadow_eligibility(context),
        }
        decision_hash = self._jcs_hash(decision_payload)
        decision_receipt = {
            "schema": "proof-of-route/decision/v0.2",
            "receipt_id": f"dr_{secrets.token_hex(8)}",
            "issued_at": "2026-07-10T14:32:08.442Z",
            "payload": decision_payload,
            "payload_hash": decision_hash,
            "signature": {
                "algorithm": "Ed25519",
                "key_id": "did:key:z6Mkmock",
                "value": self.signer.sign(decision_hash),  # type: ignore
            },
        }
        if decision_payload["shadow_eligible"]:
            for sm in shadow_models:
                self.shadow_queue.put_nowait(
                    {
                        "model": sm,
                        "prompt": prompt,
                        "request_id": request_id,
                        "decision_hash": decision_hash,
                    }
                )
        execution_metrics = await self._execute_route(primary_model, prompt)
        execution_payload = execution_metrics
        exec_hash = self._jcs_hash(execution_payload)
        execution_receipt = {
            "schema": "proof-of-route/execution/v0.2",
            "receipt_id": f"er_{secrets.token_hex(8)}",
            "decision_receipt_hash": decision_hash,
            "payload": execution_payload,
            "payload_hash": exec_hash,
            "signature": {
                "algorithm": "Ed25519",
                "key_id": "did:key:z6Mkmock",
                "value": self.signer.sign(exec_hash),  # type: ignore
            },
        }
        return (decision_receipt, execution_receipt)


async def demo():
    signer = Ed25519Signer()
    router = ShadowRouter(signer)
    t0_receipt, t1_receipt = await router.route_request(
        "Explain quantum gravity", {"contains_pii": False}
    )
    print("Decision Receipt (T0):")
    print(json.dumps(t0_receipt, indent=2))
    print("\nExecution Receipt (T1):")
    print(json.dumps(t1_receipt, indent=2))
    print(f"\nShadows in isolated queue: {router.shadow_queue.qsize()}")


if __name__ == "__main__":
    asyncio.run(demo())
