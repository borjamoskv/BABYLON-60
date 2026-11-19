#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ D1 MAIL BRIDGE & OTP EXTRACTOR | DOMAIN: channels.d1 | STATE: C5-REAL
# ============================================================================
"""
D1 Mail Bridge to Cloudflare D1 (babylon60-mail-db).
Extracts incoming OTP codes and security alerts across all sovereign social channels:
  - instagram@babylon60.com (@babylon60.ai)
  - x@babylon60.com (X / Twitter)
  - linkedin@babylon60.com (LinkedIn)
"""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import List, Optional


@dataclass(frozen=True)
class D1InstagramMessage:
    """Represents a security/verification email from Instagram, X, or LinkedIn stored in D1."""
    id: str
    from_address: str
    to_address: str
    subject: str
    received_utc: str
    otp_code: Optional[str]
    snippet: str
    platform: str = "social"


class D1MailListener:
    """Queries Cloudflare D1 babylon60-mail-db for Instagram, X, and LinkedIn OTPs and alerts."""

    MAIL_PROJECT_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/babylon60-mail")

    def __init__(self, db_name: str = "babylon60-mail-db"):
        self.db_name = db_name
        self.wrangler_bin = shutil.which("wrangler") or shutil.which("npx")

    @classmethod
    def detect_platform(cls, from_address: str, to_address: str, subject: str) -> str:
        """Identifies whether the email belongs to Instagram, X, or LinkedIn."""
        combined = f"{from_address} {to_address} {subject}".lower()
        if "instagram" in combined:
            return "instagram"
        if "x.com" in combined or "twitter" in combined or "x@babylon60.com" in combined or "verificación de x" in combined:
            return "x"
        if "linkedin" in combined:
            return "linkedin"
        return "social"

    @classmethod
    def extract_otp_from_text(cls, text: str) -> Optional[str]:
        """Extracts 6-digit verification code from Instagram, X, or LinkedIn email body/subject."""
        if not text:
            return None
        patterns = [
            r"\b(\d{6})\b\s+is\s+your\s+Instagram\s+code",
            r"confirm\s+your\s+identity:\s*(\d{6})",
            r"\b(\d{6})\b\s+es\s+tu\s+c[oó]digo\s+de\s+verificaci[oó]n\s+de\s+X",
            r"\b(\d{6})\b\s+is\s+your\s+X\s+verification\s+code",
            r"LinkedIn.*?(\d{6})",
            r"c[oó]digo\s+de\s+(?:confirmaci[oó]n|verificaci[oó]n|seguridad).*?(\d{6})",
            r"verification\s+code.*?(\d{6})",
            r"\b(\d{6})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        return None

    def query_recent_instagram_emails(
        self,
        limit: int = 5,
        platform_filter: Optional[str] = None,
    ) -> List[D1InstagramMessage]:
        """Queries remote D1 database for recent emails across Instagram, X, and LinkedIn."""
        if not self.wrangler_bin:
            return []

        sql_query = (
            f"SELECT id, from_address, to_address, subject, snippet, body_html, "
            f"datetime(received_at/1000, 'unixepoch') as received_utc "
            f"FROM emails WHERE "
            f"to_address LIKE '%instagram@babylon60.com%' OR "
            f"to_address LIKE '%x@babylon60.com%' OR "
            f"to_address LIKE '%linkedin@babylon60.com%' OR "
            f"from_address LIKE '%instagram%' OR "
            f"from_address LIKE '%x.com%' OR "
            f"from_address LIKE '%twitter%' OR "
            f"from_address LIKE '%linkedin%' "
            f"ORDER BY received_at DESC LIMIT {limit};"
        )

        use_project_dir = self.MAIL_PROJECT_DIR.exists()
        target_db = "DB" if use_project_dir else self.db_name
        cwd_path = str(self.MAIL_PROJECT_DIR) if use_project_dir else "/tmp"

        cmd = [
            "npx", "wrangler", "d1", "execute", target_db,
            "--remote",
            "--command", sql_query,
            "--json",
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd_path)
            if res.returncode != 0:
                return []

            data = json.loads(res.stdout)
            rows = data[0].get("results", []) if data else []
            messages: List[D1InstagramMessage] = []

            for row in rows:
                body = row.get("body_html") or row.get("snippet") or ""
                clean_text = re.sub(r"<style[^>]*>.*?</style>", " ", body, flags=re.S)
                clean_text = re.sub(r"<[^>]+>", " ", clean_text)
                subject = row.get("subject", "")
                from_addr = row.get("from_address", "")
                to_addr = row.get("to_address", "")

                platform = self.detect_platform(from_addr, to_addr, subject)
                if platform_filter and platform != platform_filter.lower():
                    continue

                combined = f"{subject} {clean_text}"
                otp = self.extract_otp_from_text(combined)

                messages.append(
                    D1InstagramMessage(
                        id=row.get("id", ""),
                        from_address=from_addr,
                        to_address=to_addr,
                        subject=subject,
                        received_utc=row.get("received_utc", ""),
                        otp_code=otp,
                        snippet=(row.get("snippet") or "")[:200],
                        platform=platform,
                    )
                )

            return messages
        except Exception:
            return []
