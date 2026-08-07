# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Substack Subscriber Thermodynamic Audit & Transducer Engine.
Audits, categorizes, and segments Substack subscriber exports according to exergy ratings,
deliverability risk, and institutional audience profiles.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, field
from pathlib import Path
import os
import tempfile
from typing import Any

VIP_KEYWORDS: list[str] = [
    "openai",
    "huggingface",
    "foundersfund",
    "microstrategy",
    "bittensor",
    "sentient",
    "nillion",
    "dydx",
    "ninjatune",
    "mixmag",
    "ostgut",
    "sohoradio",
    "hypebeast",
    "audaxrenovables",
    "berria",
    "media-attack",
    "audioshake",
    "loudwomen",
    "convequity",
    "securebio",
]

INFLUENCER_KEYWORDS: list[str] = [
    "contacto@gmail.com",
    "elxokas",
    "wallstreetwolverine",
    "alxelmundo",
    "pedritoviral",
    "davooxeneize",
    "kiddkeo",
    "dalasito",
    "trilineyt",
    "moradcontacto",
    "lauraescanescontacto",
    "soyunapringadacontacto",
    "henaralvarezcontacto",
]

@dataclass
class SubscriberRecord:
    email: str
    subscriber_type: str
    activity: int
    name: str = ""
    start_date: str = ""
    revenue: float = 0.0

    @classmethod
    def from_row(cls, row: dict[str, str]) -> SubscriberRecord:
        email = row.get("Email", "").strip()
        sub_type = row.get("Type", "Free").strip()

        act_raw = row.get("Activity", "0").strip()
        try:
            activity = int(act_raw)
        except ValueError:
            activity = 0

        name = row.get("Name", "").strip()
        start_date = row.get("Start date", "").strip()

        rev_str = row.get("Revenue", "0").replace("$", "").replace(",", "").strip()
        try:
            revenue = float(rev_str) if rev_str else 0.0
        except ValueError:
            revenue = 0.0

        return cls(
            email=email,
            subscriber_type=sub_type,
            activity=activity,
            name=name,
            start_date=start_date,
            revenue=revenue,
        )

    def is_vip(self) -> bool:
        email_lower = self.email.lower()
        return any(kw in email_lower for kw in VIP_KEYWORDS)

    def is_influencer_cold_import(self) -> bool:
        email_lower = self.email.lower()
        return any(kw in email_lower for kw in INFLUENCER_KEYWORDS)

@dataclass
class AuditSummary:
    total_subscribers: int
    total_revenue: float
    comp_count: int
    free_count: int
    author_count: int
    activity_distribution: dict[int, int]
    vip_count: int
    high_exergy_count: int
    deliverability_hazard_count: int
    cohorts: dict[str, dict[str, Any]] = field(default_factory=dict)

class SubstackSubscriberAuditor:
    """Engine for performing physical exergy audits and deliverability segmentation on Substack subscriber exports."""

    def __init__(self, subscribers: list[SubscriberRecord]) -> None:
        self.subscribers = subscribers

    @classmethod
    def from_csv(cls, filepath: str | Path) -> SubstackSubscriberAuditor:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Subscriber CSV file not found: {path}")

        records: list[SubscriberRecord] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(SubscriberRecord.from_row(row))
        return cls(records)

    def generate_summary(self) -> AuditSummary:
        total = len(self.subscribers)
        rev_total = sum(s.revenue for s in self.subscribers)
        comp_count = sum(1 for s in self.subscribers if s.subscriber_type == "Comp")
        free_count = sum(1 for s in self.subscribers if s.subscriber_type == "Free")
        author_count = sum(1 for s in self.subscribers if s.subscriber_type == "Author")

        act_dist: dict[int, int] = {i: 0 for i in range(6)}
        for s in self.subscribers:
            act_dist[s.activity] = act_dist.get(s.activity, 0) + 1

        vips = [s for s in self.subscribers if s.is_vip()]
        high_exergy = [s for s in self.subscribers if s.activity >= 3]
        hazards = [s for s in self.subscribers if s.activity == 0 and s.subscriber_type == "Comp"]

        # Group by cohorts
        cohort_groups: dict[str, list[SubscriberRecord]] = {}
        for s in self.subscribers:
            date_key = s.start_date[:10] if s.start_date else "Unknown"
            cohort_groups.setdefault(date_key, []).append(s)

        cohort_summary: dict[str, dict[str, Any]] = {}
        for date_key, group in cohort_groups.items():
            g_total = len(group)
            g_comp = sum(1 for s in group if s.subscriber_type == "Comp")
            g_active = sum(1 for s in group if s.activity >= 3)
            g_zombies = sum(1 for s in group if s.activity == 0)
            cohort_summary[date_key] = {
                "total": g_total,
                "comp": g_comp,
                "active_ge_3": g_active,
                "zombies_act_0": g_zombies,
                "retention_rate": round((g_active / g_total) * 100, 2) if g_total > 0 else 0.0,
            }

        return AuditSummary(
            total_subscribers=total,
            total_revenue=rev_total,
            comp_count=comp_count,
            free_count=free_count,
            author_count=author_count,
            activity_distribution=act_dist,
            vip_count=len(vips),
            high_exergy_count=len(high_exergy),
            deliverability_hazard_count=len(hazards),
            cohorts=cohort_summary,
        )

    def classify_tiers(self) -> dict[str, list[SubscriberRecord]]:
        """Classifies subscribers into 4 Exergy Tiers for deliverability protection & targeting."""
        tiers: dict[str, list[SubscriberRecord]] = {
            "tier1_c5real_core": [],
            "tier2_engaged": [],
            "tier3_low_activity": [],
            "tier4_deliverability_hazard": [],
        }

        for s in self.subscribers:
            if s.activity >= 4 or (s.is_vip() and s.activity >= 1):
                tiers["tier1_c5real_core"].append(s)
            elif s.activity in (2, 3):
                tiers["tier2_engaged"].append(s)
            elif s.activity == 1:
                tiers["tier3_low_activity"].append(s)
            else:
                tiers["tier4_deliverability_hazard"].append(s)

        return tiers

    def export_segmented_csvs(self, output_dir: str | Path) -> dict[str, str]:
        """Atomically exports segmented CSVs into output_dir (using .tmp + os.replace for Ω41 compliance)."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        tiers = self.classify_tiers()
        created_files: dict[str, str] = {}

        for tier_name, records in tiers.items():
            file_dest = out_path / f"{tier_name}.csv"
            # Atomic write via tempfile
            with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=out_path, delete=False) as tf:
                tmp_name = tf.name
                writer = csv.writer(tf)
                writer.writerow(["Email", "Type", "Activity", "Name", "StartDate", "Revenue"])
                for r in records:
                    writer.writerow(
                        [
                            r.email,
                            r.subscriber_type,
                            r.activity,
                            r.name,
                            r.start_date,
                            r.revenue,
                        ]
                    )

            os.replace(tmp_name, file_dest)
            created_files[tier_name] = str(file_dest)

        return created_files
