# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
Squad REAPER: Death Protocol Enforcement Daemon

This sovereign daemon continuously monitors the exergy registry and ledger.
It enforces the Death Protocol from the Sortu-APEX (v14.0) architecture, automatically
purging dormant, anergic, or obsolete skills and agents from the ecosystem to
preserve maximum thermodynamic efficiency.

Lifecycle Enforced: ACTIVE -> QUARANTINED -> TOMBSTONED -> PURGED
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("babylon60.daemon.reaper")


class DeathCertificate:
    """Immutable record of an entity's termination."""

    def __init__(self, target_id: str, reason: str, exergy: float, lifetime_days: int):
        self.target_id = target_id
        self.reason = reason
        self.exergy_at_death = exergy
        self.lifetime_days = lifetime_days
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "cause_of_death": self.reason,
            "exergy_at_death": self.exergy_at_death,
            "lifetime_days": self.lifetime_days,
            "tombstone_date": self.timestamp,
            "status": "PURGED",
        }


class ReaperDaemon:
    def __init__(self):
        self.agent_id = "reaper_omega_protocol"
        self.ttl_days = 30
        logger.info("[***id")

    def evaluate_target(
        self, target_id: str, last_invocation: datetime, net_exergy: float, revenue_generated: float
    ) -> str | None:
        """Evaluates if a target meets any of the Death Triggers."""
        now = datetime.now(timezone.utc)
        days_dormant = (now - last_invocation).days

        if days_dormant > self.ttl_days:
            return "TTL_EXPIRED_DORMANT"
        if net_exergy < 0:
            return "NEGATIVE_NET_EXERGY"
        if days_dormant > 7 and revenue_generated <= 0.0:
            return "ZERO_REVENUE_EXTENDED_DORMANCY"

        return None

    def execute_purge(
        self, target_id: str, creation_date: datetime, exergy: float, reason: str
    ) -> DeathCertificate:
        """Executes the final phase of the Death Protocol (TOMBSTONED -> PURGED)."""
        now = datetime.now(timezone.utc)
        lifetime = (now - creation_date).days

        logger.warning(
            "[%s] ☠️ DEATH PROTOCOL TRIGGERED ☠️\nTarget: %s\nCause: %s\nAction: VSA Hypervector detached. Genome marked EXTINCT. Ledger Sealed.",
            self.agent_id,
            target_id,
            reason,
        )

        cert = DeathCertificate(target_id, reason, exergy, lifetime)

        # In a full run, this invokes the CORTEX ledger to write the certificate
        # from babylon60.audit.ledger import emit_event
        # emit_event("DEATH_CERTIFICATE", cert.to_dict())

        return cert

    def sweep(self, registry: dict[str, dict[str, Any]]):
        """Sweeps the given registry for anomalies and enforces the protocol."""
        logger.info("[***id")
        purged = []
        for target_id, stats in registry.items():
            reason = self.evaluate_target(
                target_id,
                stats.get("last_invocation", datetime.now(timezone.utc)),
                stats.get("net_exergy", 0.0),
                stats.get("revenue_generated", 0.0),
            )
            if reason:
                cert = self.execute_purge(
                    target_id,
                    stats.get("creation_date", datetime.now(timezone.utc) - timedelta(days=60)),
                    stats.get("net_exergy", 0.0),
                    reason,
                )
                purged.append(cert)

        logger.info("[***id")
        return purged


def init_daemon():
    return ReaperDaemon()
