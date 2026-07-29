#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - SUBSTACK SUBSCRIBER SEGMENTATION & DELIVERABILITY ENGINE
import sys
import os
import json
import re
import csv
import argparse
from collections import defaultdict
from typing import Dict, List, Tuple, Any

class SubstackSegmenterEngine:
    """C5-REAL Substack lead validation, deliverability audit, and cohort clustering engine."""

    def __init__(self, db_path: str = "output/subscriber_analysis.json"):
        self.db_path = db_path
        self.db_map = self._load_db()

        self.cohort_rules = [
            ("COHORTE_URBAN_FREESTYLE", [
                "freestyle", "rap", "chuty", "aczino", "wos", "skone", "gazir", "bnet",
                "arkano", "kiddkeo", "relsb", "morad", "trueno", "rapder", "zasko", "blon",
                "skiper", "lancer", "letra", "sweetpain", "mrego", "hander", "jado", "bta",
                "errece", "stuart", "mecha", "larrix", "zaina", "naista", "cacha", "nitro",
                "acertijo", "jokker", "vallest", "marithea", "lokillo", "filosofo", "jaze", "strike", "stick"
            ]),
            ("COHORTE_LIFESTYLE_INFLUENCERS", [
                "pombo", "dulceida", "gonu", "villarreal", "riumbau", "hernand", "postureo",
                "vives", "carriedo", "rosa", "lalachus", "jedet", "bernad", "fuste"
            ]),
            ("COHORTE_TECH_SCIENCE", [
                "dotcsv", "quantum", "cdeciencia", "gentile", "cazaustre", "moure", "midu",
                "pragmatic", "bytebytego", "swyx", "vickiboykis", "hillel"
            ]),
            ("COHORTE_GAMING_STREAMING", [
                "auron", "xokas", "willyrex", "vegetta", "rubius", "ibai", "spreen", "mariana",
                "quackity", "fernan", "luisito", "djmariio", "spursito", "knekro", "alexby",
                "mangel", "dross", "visualpolitik", "viruzz", "gona", "fedelobo", "clavero",
                "perxitaa", "gemita", "mayichi", "rivers", "guarnizo", "arigameplays", "amablitz"
            ])
        ]

        self.spam_trigger_words = [
            "gratis", "gana dinero", "oferta", "urgente", "haz clic", "clic aquí", "$$$",
            "100% gratis", "ingresos", "multiplica", "inversión", "garantizado", "sin riesgo"
        ]

    def _load_db(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return {}
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item.get("email", "").lower(): item for item in data if "email" in item}
        except Exception:
            return {}

    def validate_email_syntax(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    def classify_email(self, email: str, name: str = "") -> str:
        text = f"{email.lower()} {name.lower()}"
        for cohort, keywords in self.cohort_rules:
            if any(kw in text for kw in keywords):
                return cohort
        return "COHORTE_GENERAL_MEDIA"

    def audit_spam_risk(self, subject: str, body: str) -> Tuple[int, List[str]]:
        score = 0
        reasons = []

        if subject.isupper():
            score += 30
            reasons.append("Subject is 100% UPPERCASE (+30 risk)")

        found_triggers = [w for w in self.spam_trigger_words if w in subject.lower() or w in body.lower()]
        if found_triggers:
            penalty = len(found_triggers) * 15
            score += penalty
            reasons.append(f"Spam trigger words found: {found_triggers} (+{penalty} risk)")

        if any(shortener in body.lower() for shortener in ["bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly"]):
            score += 25
            reasons.append("Link shorteners detected (+25 risk)")

        if subject.count("!") > 2 or body.count("!!!") > 0:
            score += 15
            reasons.append("Excessive exclamation marks (+15 risk)")

        if not any(phrase in body.lower() for phrase in ["responde", "reply", "contesta", "qué opinas"]):
            score += 10
            reasons.append("No reply-prompt CTA found to boost sender reputation (+10 risk)")

        score = min(score, 100)
        return score, reasons

    def process_emails(self, email_list: List[str], output_dir: str = "output") -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        valid = []
        invalid = []
        segments = defaultdict(list)

        for raw_e in email_list:
            e = raw_e.strip()
            if not e:
                continue
            if not self.validate_email_syntax(e):
                invalid.append(e)
                continue

            db_meta = self.db_map.get(e.lower(), {})
            name = db_meta.get("name", e.split("@")[0])
            cohort = self.classify_email(e, name)

            valid.append(e)
            segments[cohort].append({"email": e, "name": name, "db_status": bool(db_meta)})

        exported_files = []
        for cohort, items in segments.items():
            filepath = os.path.join(output_dir, f"{cohort.lower()}.csv")
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["email", "first_name", "cohort", "verified_db"])
                for item in items:
                    writer.writerow([item["email"], item["name"], cohort, item["db_status"]])
            exported_files.append(filepath)

        return {
            "total_input": len(email_list),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "invalid_emails": invalid,
            "cohort_breakdown": {k: len(v) for k, v in segments.items()},
            "exported_files": exported_files
        }

def main():
    parser = argparse.ArgumentParser(description="Substack Subscriber Segmentation & Deliverability Engine")
    parser.add_argument("--emails", type=str, help="Comma-separated email string or path to email list file")
    parser.add_argument("--subject", type=str, default="", help="Optional email subject line to audit for spam risk")
    parser.add_argument("--body", type=str, default="", help="Optional email body content to audit for spam risk")
    parser.add_argument("--outdir", type=str, default="output", help="Directory to save exported CSV cohorts")
    args = parser.parse_args()

    engine = SubstackSegmenterEngine()

    if args.subject or args.body:
        score, reasons = engine.audit_spam_risk(args.subject, args.body)
        print(f"\n--- DELIVERABILITY & SPAM AUDIT ---")
        print(f"Spam Risk Score: {score}/100 ({'HIGH RISK' if score >= 40 else 'SAFE'})")
        if reasons:
            print("Risk Factors:")
            for r in reasons:
                print(f"  - {r}")
        else:
            print("  No spam risk factors detected.")

    if args.emails:
        if os.path.exists(args.emails):
            with open(args.emails, "r", encoding="utf-8") as f:
                raw_text = f.read()
        else:
            raw_text = args.emails

        email_list = [e.strip() for e in raw_text.replace("\n", ",").split(",") if e.strip()]
        res = engine.process_emails(email_list, args.outdir)

        print(f"\n--- SEGMENTATION RESULTS ---")
        print(f"Total Evaluated: {res['total_input']}")
        print(f"Valid Syntax: {res['valid_count']}")
        print(f"Invalid Syntax: {res['invalid_count']}")

        print("\nCohorts:")
        for cohort, count in res['cohort_breakdown'].items():
            print(f"  [{cohort}]: {count} leads")

        print("\nExported Files:")
        for fpath in res['exported_files']:
            print(f"  - {fpath}")

if __name__ == "__main__":
    main()
