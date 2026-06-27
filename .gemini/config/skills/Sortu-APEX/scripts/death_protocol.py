# C5-REAL
"""
SORTU-Ω v14.0.0 Death Protocol.
TTL enforcement. Exergy purge. Registry consolidation.
"""
import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("sortu-death-protocol")

DEFAULT_TTL_DAYS = 30
GRACE_PERIOD_DAYS = 7
TOMBSTONE_PURGE_DAYS = 14
MAX_ACTIVE_SKILLS = 50

@dataclass
class DeathCertificate:
    """Struct: Termination record."""
    skill_name: str
    born: str
    died: str
    lifetime_days: int
    total_invocations: int
    total_exergy: float
    cause_of_death: str
    archived_to: str
    genome_gene_status: str = "EXTINCT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "born": self.born,
            "died": self.died,
            "lifetime_days": self.lifetime_days,
            "total_invocations": self.total_invocations,
            "total_exergy": self.total_exergy,
            "cause_of_death": self.cause_of_death,
            "archived_to": self.archived_to,
            "genome_gene_status": self.genome_gene_status,
            "hash": "",
        }

    def seal(self) -> str:
        """Return SHA-256 ledger seal."""
        d = self.to_dict()
        raw = json.dumps(d, sort_keys=True)
        d["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return d["hash"]

class DeathTrigger:
    """Evaluate pipeline conditions."""

    @staticmethod
    def ttl_expired(last_invocation: str, ttl_days: int = DEFAULT_TTL_DAYS) -> bool:
        """Return bool: TTL expired."""
        try:
            last = datetime.fromisoformat(last_invocation).replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - last) > timedelta(days=ttl_days)
        except (ValueError, TypeError):
            return True

    @staticmethod
    def negative_exergy(exergy: float) -> bool:
        """Return bool: Exergy < 0.0."""
        return exergy < 0.0

    @staticmethod
    def orphaned_dependency(depends_on: list[str], active_names: set[str]) -> bool:
        """Return bool: Missing dependency."""
        if not depends_on:
            return False
        return any(dep not in active_names for dep in depends_on)

    @staticmethod
    def zero_revenue(exergy: float, invocations: int) -> bool:
        """Return bool: Zero yield."""
        return invocations == 0 and exergy <= 0.0

class DeathProtocol:
    """
    Engine: Skill termination.
    Pipeline: ACTIVE -> QUARANTINED(7d) -> TOMBSTONED(14d) -> PURGED.
    """

    def __init__(
        self,
        skills_dir: str | None = None,
        archive_dir: str | None = None,
    ) -> None:
        self.skills_dir = Path(skills_dir or os.path.expanduser("~/.gemini/antigravity/skills"))
        self.archive_dir = Path(archive_dir or os.path.expanduser("~/.gemini/antigravity/archive"))
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.trigger = DeathTrigger()
        self.certificates: list[DeathCertificate] = []

    def audit(self, registry: dict[str, Any]) -> dict[str, Any]:
        """Return state recommendations."""
        active = registry.get("active_skills", [])
        quarantined = registry.get("quarantined_skills", [])
        tombstoned = registry.get("tombstoned_skills", [])
        active_names = {s["name"] for s in active}

        recommendations = {
            "quarantine": [],
            "tombstone": [],
            "purge": [],
            "healthy": [],
        }

        for skill in active:
            name = skill["name"]
            triggers_fired = []

            if self.trigger.ttl_expired(skill.get("last_invocation", "")):
                triggers_fired.append("TTL_EXPIRED")
            if self.trigger.negative_exergy(skill.get("exergy", 0.0)):
                triggers_fired.append("NEGATIVE_EXERGY")
            depends = skill.get("depends_on", [])
            if self.trigger.orphaned_dependency(depends, active_names):
                triggers_fired.append("ORPHANED_DEPENDENCY")
            if self.trigger.zero_revenue(skill.get("exergy", 0.0), skill.get("total_invocations", 0)):
                triggers_fired.append("ZERO_REVENUE")

            if triggers_fired:
                recommendations["quarantine"].append({"name": name, "triggers": triggers_fired})
            else:
                recommendations["healthy"].append(name)

        now = datetime.now(timezone.utc)
        for skill in quarantined:
            try:
                q_time = datetime.fromisoformat(skill.get("quarantined_at", "")).replace(tzinfo=timezone.utc)
                if (now - q_time) > timedelta(days=GRACE_PERIOD_DAYS):
                    recommendations["tombstone"].append(skill["name"])
            except (ValueError, TypeError):
                recommendations["tombstone"].append(skill["name"])

        for skill in tombstoned:
            try:
                t_time = datetime.fromisoformat(skill.get("tombstoned_at", "")).replace(tzinfo=timezone.utc)
                if (now - t_time) > timedelta(days=TOMBSTONE_PURGE_DAYS):
                    recommendations["purge"].append(skill["name"])
            except (ValueError, TypeError):
                recommendations["purge"].append(skill["name"])

        return recommendations

    def archive_skill(self, skill_name: str) -> str:
        """Execute L3 storage push."""
        src = self.skills_dir / skill_name
        if not src.exists():
            return ""

        archive_path = self.archive_dir / f"{skill_name}.tar.sha256"
        dst = self.archive_dir / skill_name
        
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

        content_hash = hashlib.sha256()
        for fpath in sorted(dst.rglob("*")):
            if fpath.is_file():
                content_hash.update(fpath.read_bytes())

        archive_path.write_text(content_hash.hexdigest())
        logger.info(f"Archived {skill_name} -> {archive_path}")
        return str(archive_path)

    def execute_purge(self, skill_name: str) -> DeathCertificate | None:
        """Execute sequence: archive -> remove -> certificate."""
        src = self.skills_dir / skill_name
        if not src.exists():
            return None

        archive_path = self.archive_skill(skill_name)
        cert = DeathCertificate(
            skill_name=skill_name,
            born="unknown",
            died=datetime.now(timezone.utc).isoformat(),
            lifetime_days=0,
            total_invocations=0,
            total_exergy=0.0,
            cause_of_death="DEATH_PROTOCOL_EXECUTION",
            archived_to=archive_path,
        )
        cert.seal()
        self.certificates.append(cert)
        shutil.rmtree(src)
        logger.info(f"PURGED: {skill_name} | Hash: {cert.to_dict()['hash']}")
        return cert

    def report(self, recommendations: dict[str, Any]) -> str:
        """Return YAML audit report."""
        lines = [
            "Timestamp: " + datetime.now(timezone.utc).isoformat(),
            "Metrics:",
            f"  Healthy: {len(recommendations['healthy'])}",
            f"  Quarantine: {len(recommendations['quarantine'])}",
            f"  Tombstone: {len(recommendations['tombstone'])}",
            f"  Purge: {len(recommendations['purge'])}",
            "State:",
            "  Healthy:"
        ]
        for name in recommendations["healthy"]:
            lines.append(f"    - {name}")
        
        lines.append("  Quarantine:")
        for item in recommendations["quarantine"]:
            lines.append(f"    - name: {item['name']}")
            lines.append(f"      triggers: {item['triggers']}")
            
        lines.append("  Tombstone:")
        for name in recommendations["tombstone"]:
            lines.append(f"    - {name}")
            
        lines.append("  Purge:")
        for name in recommendations["purge"]:
            lines.append(f"    - {name}")
            
        return "\n".join(lines)
