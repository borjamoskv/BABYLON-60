"""
REAPER — Platform-Specific Report Formatter

Auto-generates submission-ready reports from findings.
Templates for: Immunefi, Sherlock, Code4rena, Hats.
"""
from datetime import datetime, timezone
from pathlib import Path

from cortex_bounty.config import SUBMISSIONS_DIR


IMMUNEFI_TEMPLATE = """# {title}

## Bug Description
{description}

## Impact
{impact}

## Risk Breakdown
- **Difficulty to Exploit:** {difficulty}
- **Weakness:** {weakness}

## Recommendation
{recommendation}

## Proof of Concept
{poc}

## References
{references}
"""

SHERLOCK_TEMPLATE = """# {title}

## Summary
{description}

## Vulnerability Detail
{detail}

## Impact
{impact}

## Code Snippet
{code_snippet}

## Tool used
Manual Review + CORTEX VENOM Scanner

## Recommendation
{recommendation}
"""

CODE4RENA_TEMPLATE = """# [{severity}] {title}

## Lines of code
{lines_of_code}

## Vulnerability details
{description}

### Impact
{impact}

### Proof of Concept
{poc}

### Recommended Mitigation Steps
{recommendation}
"""


class ReportFormatter:
    """Generates submission-ready reports from structured finding data."""

    def format_immunefi(self, data: dict) -> str:
        return IMMUNEFI_TEMPLATE.format(
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            impact=data.get("impact", ""),
            difficulty=data.get("difficulty", "Medium"),
            weakness=data.get("weakness", ""),
            recommendation=data.get("recommendation", ""),
            poc=data.get("poc", "No PoC provided"),
            references=data.get("references", ""),
        )

    def format_sherlock(self, data: dict) -> str:
        return SHERLOCK_TEMPLATE.format(
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            detail=data.get("detail", data.get("description", "")),
            impact=data.get("impact", ""),
            code_snippet=data.get("code_snippet", ""),
            recommendation=data.get("recommendation", ""),
        )

    def format_code4rena(self, data: dict) -> str:
        return CODE4RENA_TEMPLATE.format(
            severity=data.get("severity", "M").upper(),
            title=data.get("title", "Untitled"),
            lines_of_code=data.get("lines_of_code", ""),
            description=data.get("description", ""),
            impact=data.get("impact", ""),
            poc=data.get("poc", ""),
            recommendation=data.get("recommendation", ""),
        )

    def format(self, platform: str, data: dict) -> str:
        """Format for any platform."""
        formatters = {
            "immunefi": self.format_immunefi,
            "sherlock": self.format_sherlock,
            "code4rena": self.format_code4rena,
            "c4": self.format_code4rena,
        }
        formatter = formatters.get(platform.lower())
        if not formatter:
            raise ValueError(f"Unknown platform: {platform}")
        return formatter(data)

    def save_submission(self, platform: str, data: dict, hunt_id: str = "") -> Path:
        """Format, save, and return path to submission file."""
        content = self.format(platform, data)
        SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = data.get("title", "untitled").lower().replace(" ", "-")[:40]
        filename = f"SUBMIT_{platform.upper()}_{slug}_{timestamp}.md"

        filepath = SUBMISSIONS_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath
