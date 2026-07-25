import hashlib
import json
import time
from typing import Any


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_payload(payload: dict[str, Any]) -> str:
    return sha256_text(canonical_json(payload))


class EpistemicHalt(Exception):
    pass


class ReplayKernel:
    def __init__(self, db: Any, policy_version: str):
        self.db = db
        self.policy_version = policy_version

    async def current_head_hash(self) -> str:
        async with self.db.execute(
            "\n            SELECT event_hash\n            FROM ledger_events\n            ORDER BY sequence_id DESC\n            LIMIT 1\n            "
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else "GENESIS"

    async def propose_model_output(
        self, *, provider: str, model: str, prompt: str, params: dict[str, Any], output: str, context_hash: str
    ) -> str:
        payload = {
            "type": "MODEL_PROPOSAL",
            "provider": provider,
            "model": model,
            "prompt_hash": sha256_text(prompt),
            "params": params,
            "output_hash": sha256_text(output),
            "context_hash": context_hash,
            "policy_version": self.policy_version,
        }
        proposal_hash = hash_payload(payload)
        await self.db.execute(
            "\n            INSERT INTO model_proposals (\n                proposal_hash,\n                provider,\n                model,\n                prompt,\n                params_json,\n                output,\n                context_hash,\n                created_at\n            )\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ",
            (proposal_hash, provider, model, prompt, canonical_json(params), output, context_hash, int(time.time())),
        )
        return proposal_hash

    async def admit_event(self, *, kind: str, payload: dict[str, Any], source_proposal_hash: str | None = None) -> str:
        parent_hash = await self.current_head_hash()
        event = {
            "kind": kind,
            "payload": payload,
            "parent_hash": parent_hash,
            "source_proposal_hash": source_proposal_hash,
            "policy_version": self.policy_version,
        }
        event_hash = hash_payload(event)
        self._validate_event(event)
        await self.db.execute(
            "\n            INSERT INTO ledger_events (\n                event_hash,\n                parent_hash,\n                kind,\n                payload_json,\n                source_proposal_hash,\n                policy_version,\n                created_at\n            )\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n            ",
            (
                event_hash,
                parent_hash,
                kind,
                canonical_json(payload),
                source_proposal_hash,
                self.policy_version,
                int(time.time()),
            ),
        )
        return event_hash

    def _validate_event(self, event: dict[str, Any]) -> None:
        if not event["kind"]:
            raise EpistemicHalt("Evento sin kind")
        if not isinstance(event["payload"], dict):
            raise EpistemicHalt("Payload no canónico")
        if not event["policy_version"]:
            raise EpistemicHalt("Evento sin policy_version")
        if event["parent_hash"] is None:
            raise EpistemicHalt("Evento sin parent_hash")


pass
