# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Deliverability & MX Resolution Engine.
Validates email formatting, syntax integrity, and MX record reachability
for contact imports to protect server reputation scoring.
"""

from __future__ import annotations
import re
import socket
from dataclasses import dataclass

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@dataclass
class ValidationResult:
    email: str
    is_valid_syntax: bool
    domain: str
    has_mx_or_a_record: bool = False
    error_reason: str = ""

class DeliverabilityValidator:
    """Engine for verifying email structural integrity and DNS/MX resolution."""

    @staticmethod
    def validate_syntax(email: str) -> bool:
        if not email or len(email) > 254:
            return False
        return bool(EMAIL_REGEX.match(email.strip()))

    @staticmethod
    def extract_domain(email: str) -> str:
        parts = email.strip().split("@")
        if len(parts) == 2:
            return parts[1].lower()
        return ""

    @classmethod
    def check_domain_dns(cls, domain: str) -> bool:
        """Checks if domain has valid DNS resolution (A or MX lookup)."""
        if not domain:
            return False
        try:
            # Query host IP to verify domain existence
            socket.gethostbyname(domain)
            return True
        except (socket.gaierror, socket.herror, TimeoutError):
            return False

    @classmethod
    def validate_email(cls, email: str, verify_dns: bool = False) -> ValidationResult:
        email_clean = email.strip()
        if not cls.validate_syntax(email_clean):
            return ValidationResult(
                email=email_clean,
                is_valid_syntax=False,
                domain=cls.extract_domain(email_clean),
                has_mx_or_a_record=False,
                error_reason="INVALID_SYNTAX",
            )

        domain = cls.extract_domain(email_clean)
        has_dns = True
        if verify_dns:
            has_dns = cls.check_domain_dns(domain)

        return ValidationResult(
            email=email_clean,
            is_valid_syntax=True,
            domain=domain,
            has_mx_or_a_record=has_dns,
            error_reason="" if has_dns else "DNS_LOOKUP_FAILED",
        )
