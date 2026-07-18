import json
import hashlib
import time
from typing import Any, Dict, Optional


def canonical_json(obj: Any) -> str:
    """
    Serialización determinista.
    Prohíbe que dos representaciones distintas del mismo objeto
    produzcan hashes diferentes.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_payload(payload: Dict[str, Any]) -> str:
    return sha256_text(canonical_json(payload))


class EpistemicHalt(Exception):
    pass


class ReplayKernel:
    """
    Núcleo determinista de admisión de eventos.

    Los modelos externos NO escriben estado.
    Solo producen propuestas.

    Este kernel decide qué propuesta entra al ledger.
    """

    def __init__(self, db: Any, policy_version: str):
        self.db = db
        self.policy_version = policy_version

    async def current_head_hash(self) -> str:
        async with self.db.execute(
            """
            SELECT event_hash
            FROM ledger_events
            ORDER BY sequence_id DESC
            LIMIT 1
            """
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else "GENESIS"

    async def propose_model_output(
        self,
        *,
        provider: str,
        model: str,
        prompt: str,
        params: Dict[str, Any],
        output: str,
        context_hash: str,
    ) -> str:
        """
        Registra una salida de modelo como PROPUESTA.
        No modifica el estado canónico.
        """

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
            """
            INSERT INTO model_proposals (
                proposal_hash,
                provider,
                model,
                prompt,
                params_json,
                output,
                context_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_hash,
                provider,
                model,
                prompt,
                canonical_json(params),
                output,
                context_hash,
                int(time.time()),
            ),
        )

        return proposal_hash

    async def admit_event(
        self,
        *,
        kind: str,
        payload: Dict[str, Any],
        source_proposal_hash: Optional[str] = None,
    ) -> str:
        """
        Admite un evento al ledger si pasa invariantes.
        Esta es la única puerta legítima de mutación de estado.
        """

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
            """
            INSERT INTO ledger_events (
                event_hash,
                parent_hash,
                kind,
                payload_json,
                source_proposal_hash,
                policy_version,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
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

    def _validate_event(self, event: Dict[str, Any]) -> None:
        """
        Invariantes mínimas.
        Aquí luego conectas invariants.py.
        """

        if not event["kind"]:
            raise EpistemicHalt("Evento sin kind")

        if not isinstance(event["payload"], dict):
            raise EpistemicHalt("Payload no canónico")

        if not event["policy_version"]:
            raise EpistemicHalt("Evento sin policy_version")

        if event["parent_hash"] is None:
            raise EpistemicHalt("Evento sin parent_hash")


pass
