#!/usr/bin/env python3
"""
C5-REAL OSINT Validator for Substack Author Dataset (BABYLON-60)
Strict zero-inference verification, schema integrity, and affinity score audit.
"""

import json
import re
import sys
from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parent.parent / "SUBSTACK" / "osint_babylon60_authors.json"

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_REGEX = re.compile(r"^https?://")

REQUIRED_FIELDS = [
    "author_id",
    "name",
    "handle",
    "substack_url",
    "profile_url",
    "public_email",
    "email_location_url",
    "email_provenance",
    "affinity_score",
    "affinity_breakdown",
    "evidence",
    "verification_status",
    "timestamp_utc"
]

def validate_dataset():
    if not DATASET_PATH.exists():
        print(f"[FAIL] Dataset file not found at: {DATASET_PATH}")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("dataset_metadata", {})
    authors = data.get("authors", [])

    print("=" * 70)
    print(f" █▄ C5-REAL OSINT VALIDATOR — {meta.get('project', 'UNKNOWN')}")
    print(f" Total records evaluated: {len(authors)}")
    print(f" Privacy Doctrine: {meta.get('ethical_compliance', {}).get('privacy_doctrine')}")
    print("=" * 70)

    errors = []
    warnings = []

    for idx, author in enumerate(authors, 1):
        author_id = author.get("author_id", f"INDEX_{idx}")
        print(f"\n[RECORD {idx}/8] Verifying: {author_id} ({author.get('name')})")

        # 1. Required fields check
        missing = [field for field in REQUIRED_FIELDS if field not in author]
        if missing:
            errors.append(f"[{author_id}] Missing required fields: {missing}")
            continue

        # 2. Email format & Zero-Inference Check
        email = author.get("public_email", "")
        if not EMAIL_REGEX.match(email):
            errors.append(f"[{author_id}] Invalid public_email format: '{email}'")

        snippet = author.get("evidence", {}).get("snippet", "")
        if email.lower() not in snippet.lower():
            errors.append(
                f"[{author_id}] ZERO-INFERENCE VIOLATION: Email '{email}' is not explicitly present in snippet evidence!"
            )
        else:
            print(f"  ✓ Provenance verified: Email '{email}' present in text snippet.")

        # 3. URL format check
        for url_field in ["substack_url", "profile_url", "email_location_url"]:
            url_val = author.get(url_field, "")
            if not URL_REGEX.match(url_val):
                errors.append(f"[{author_id}] Invalid URL in field {url_field}: '{url_val}'")

        # 4. Affinity Score Integrity Check
        breakdown = author.get("affinity_breakdown", {})
        direct_s = breakdown.get("direct_mention_score", 0)
        them_s = breakdown.get("thematic_alignment_score", 0)
        mail_s = breakdown.get("public_email_score", 0)
        calc_score = direct_s + them_s + mail_s
        rep_score = author.get("affinity_score", 0)

        if calc_score != rep_score:
            errors.append(
                f"[{author_id}] SCORE MISMATCH: Reported score {rep_score} != Calculated ({direct_s} + {them_s} + {mail_s} = {calc_score})"
            )
        else:
            print(f"  ✓ Affinity score integrity verified: {rep_score} pts (Breakdown: Direct={direct_s}, Thematic={them_s}, Email={mail_s})")

        # 5. Verification status
        v_status = author.get("verification_status")
        if v_status != "C5_REAL_VERIFIED":
            warnings.append(f"[{author_id}] Non-standard verification status: '{v_status}'")

    print("\n" + "=" * 70)
    if errors:
        print(f"❌ VALIDATION FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ ALL RECORDS VERIFIED C5-REAL — ZERO INFERENCE VIOLATIONS DETECTED")
        print(f"   Validated 8/8 records cleanly against OSINT schema.")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    validate_dataset()
