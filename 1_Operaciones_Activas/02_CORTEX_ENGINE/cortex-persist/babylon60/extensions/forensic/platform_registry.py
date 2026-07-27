# [C5-REAL] Exergy-Maximized
"""Platform Registry — Multi-platform bounty submission routing.

Maps platform identifiers to their submission formats, URLs,
and adapter configurations.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported bounty platforms."""

    SHERLOCK = "sherlock"
    CANTINA = "cantina"
    IMMUNEFI = "immunefi"
    BUGCROWD = "bugcrowd"
    ETHEREUM_FOUNDATION = "ethereum_foundation"


class Severity(Enum):
    """Standardized severity levels across platforms."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass(frozen=True)
class PlatformConfig:
    """Configuration for a bounty platform."""

    platform: Platform
    name: str
    url: str
    submission_url: str
    requires_kyc: bool = False
    requires_poc: bool = True
    reward_model: str = "fixed"
    submission_format: str = "markdown"
    supported_severities: tuple[Severity, ...] = (
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
    )


# Platform Registry — single source of truth
PLATFORM_REGISTRY: dict[Platform, PlatformConfig] = {
    Platform.SHERLOCK: PlatformConfig(
        platform=Platform.SHERLOCK,
        name="Sherlock",
        url="https://app.sherlock.xyz",
        submission_url="https://app.sherlock.xyz/audits/contests",
        requires_kyc=False,
        requires_poc=True,
        reward_model="competitive_audit",
        submission_format="sherlock_markdown",
    ),
    Platform.CANTINA: PlatformConfig(
        platform=Platform.CANTINA,
        name="Cantina",
        url="https://cantina.xyz",
        submission_url="https://cantina.xyz/opportunities",
        requires_kyc=False,
        requires_poc=True,
        reward_model="10pct_funds_at_risk",
        submission_format="cantina_markdown",
    ),
    Platform.IMMUNEFI: PlatformConfig(
        platform=Platform.IMMUNEFI,
        name="Immunefi",
        url="https://immunefi.com",
        submission_url="https://immunefi.com/explore/",
        requires_kyc=True,
        requires_poc=True,
        reward_model="10pct_funds_at_risk",
        submission_format="immunefi_markdown",
    ),
    Platform.BUGCROWD: PlatformConfig(
        platform=Platform.BUGCROWD,
        name="Bugcrowd",
        url="https://bugcrowd.com",
        submission_url="https://bugcrowd.com/programs",
        requires_kyc=False,
        requires_poc=True,
        reward_model="severity_tiers",
        submission_format="bugcrowd_markdown",
    ),
    Platform.ETHEREUM_FOUNDATION: PlatformConfig(
        platform=Platform.ETHEREUM_FOUNDATION,
        name="Ethereum Foundation",
        url="https://ethereum.org/en/bug-bounty/",
        submission_url="https://ethereum.org/en/bug-bounty/",
        requires_kyc=False,
        requires_poc=True,
        reward_model="fixed",
        submission_format="markdown",
        supported_severities=(Severity.CRITICAL, Severity.HIGH),
    ),
}


@dataclass
class Finding:
    """A vulnerability finding ready for submission."""

    title: str
    severity: Severity
    target_name: str
    target_url: str
    vulnerability_type: str
    description: str
    impact: str
    proof_of_concept: str
    recommendation: str
    code_snippet: str = ""
    forge_output: str = ""
    taint_hash: str = ""
    metadata: dict = field(default_factory=dict)


def get_platform(platform_id: str) -> PlatformConfig:
    """Resolve a platform config by ID string."""
    try:
        platform = Platform(platform_id.lower())
    except ValueError as e:
        msg = f"Unknown platform: {platform_id}. Valid: {[p.value for p in Platform]}"
        raise ValueError(msg) from e
    return PLATFORM_REGISTRY[platform]


def list_platforms() -> list[PlatformConfig]:
    """Return all registered platforms."""
    return list(PLATFORM_REGISTRY.values())
