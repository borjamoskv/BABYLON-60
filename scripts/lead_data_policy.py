"""Private storage and provenance boundaries for synthetic and commercial records."""

from collections.abc import Mapping
from pathlib import Path
import re
import sqlite3

VAULT_DIR = Path.home() / "20_VAULT" / "MARKETING_OUTREACH"
MATRIX_PREFIX = "SYNTHETIC_STRESS_TEST_MATRIX_NOT_FOR_COMMERCIAL_OUTREACH"
MATRIX_CLASSIFICATION = "[SYNTHETIC_STRESS_TEST_MATRIX · NOT FOR COMMERCIAL OUTREACH]"
COMMERCIAL_DIR = VAULT_DIR / "verified_contacts"
COMMERCIAL_DB_PATH = COMMERCIAL_DIR / "contacts.db"
CAMPAIGNS_DIR = COMMERCIAL_DIR / "campaigns"


def latest_matrix_jsonl() -> Path:
    candidates = VAULT_DIR.glob(f"{MATRIX_PREFIX}__v*__leads_10000_enterprise_babylon60.jsonl")
    versions = []
    for path in candidates:
        match = re.fullmatch(re.escape(MATRIX_PREFIX) + r"__v(\d+)__leads_10000_enterprise_babylon60\.jsonl", path.name)
        if match:
            versions.append((int(match.group(1)), path))
    return (
        max(versions, key=lambda item: item[0])[1]
        if versions
        else (VAULT_DIR / f"{MATRIX_PREFIX}__v2__leads_10000_enterprise_babylon60.jsonl")
    )


def require_commercial_record(record: Mapping[str, object]) -> None:
    """Require explicit provenance; this check does not establish legal permission to contact."""
    markers = " ".join(
        str(record.get(key, "")) for key in ("classification", "record_classification", "verification_status", "status")
    ).upper()
    if "SYNTHETIC" in markers or "NOT FOR COMMERCIAL OUTREACH" in markers:
        raise ValueError("Registro sintético bloqueado para campañas y borradores comerciales.")
    if record.get("record_classification") != "REAL_CONTACT":
        raise ValueError("Falta una clasificación explícita de contacto real con procedencia.")
    for field in ("source_reference", "verified_at"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Falta evidencia de procedencia: {field}.")


def open_synthetic_database() -> sqlite3.Connection | None:
    """Open only a classified private index, without creating or updating files."""
    path = latest_matrix_jsonl().with_suffix(".db")
    if not path.is_file():
        return None
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT classification FROM matrix_metadata").fetchall()
        if rows != [(MATRIX_CLASSIFICATION,)]:
            raise ValueError("Índice sin clasificación sintética válida; reconstruye el índice.")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(leads)")}
        required = {
            "lead_id",
            "company_name",
            "domain",
            "sector",
            "city",
            "country",
            "target_role",
            "contact_email",
            "eu_ai_act_risk_classification",
            "babylon60_pitch_vector",
            "status",
        }
        if not required <= columns:
            raise ValueError("Esquema de matriz incompleto; reconstruye el índice.")
    except Exception:
        conn.close()
        raise
    return conn
