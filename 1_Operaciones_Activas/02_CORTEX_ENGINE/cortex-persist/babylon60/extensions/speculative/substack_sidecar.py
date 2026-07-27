import argparse
import logging
import sqlite3
from pathlib import Path

from babylon60.services.email import send_reengagement_email

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CausalScheduler")

CORTEX_DB_PATH = Path("~/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/cortex-persist/cortex_data.db").expanduser()


def evaluate_retention(dry_run=True):
    """
    Scans the local database and evaluates 'last_sign_in_at' or 'days_active'.
    If an elite node has been inactive > 15 days, triggers re-engagement.
    """
    logger.info("Starting Causal Scheduler (Retention Evaluation)...")

    conn = sqlite3.connect(CORTEX_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Extract Elite at risk (days_active > 15 and of type import/music_media)
    cursor.execute("""
        SELECT email, name, days_active, opens, cluster
        FROM audience
        WHERE status = 'active'
          AND days_active >= 15
          AND cluster IN ('music_media', 'elite_individuals')
    """)

    risk_nodes = cursor.fetchall()

    logger.info("Elite Nodes evaluated: %s in imminent risk of Churn.", len(risk_nodes))

    for node in risk_nodes:
        logger.info(
            "[TAINT: RISK_OF_CHURN] %s (%s) - %s days without activity. Opens: %s.",
            node["name"],
            node["email"],
            node["days_active"],
            node["opens"],
        )

        if not dry_run:
            # Here Mailgun / local SMTP integration will go
            logger.warning("TRIGGERING TRANSACTION TO: %s", node["email"])

            # Connection resolved to cortex.services.email
            send_reengagement_email(node["email"], node["cluster"])

            # Update status to prevent spamming
            cursor.execute(
                "UPDATE audience SET status = 'churn_mitigated' WHERE email = ?", (node["email"],)
            )

    # Extract pure Volume (For Directed Reciprocity attacks)
    cursor.execute("""
        SELECT count(*) as total FROM audience WHERE source = 'global_enriched'
    """)
    volume_total = cursor.fetchone()["total"]
    logger.info("Volume Nodes available for Directed Reciprocity: %s", volume_total)

    if not dry_run:
        conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Substack Sidecar - Causal Retention Engine")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Deactivates dry-run and executes state mutations/sends",
    )

    args = parser.parse_args()

    evaluate_retention(dry_run=not args.execute)
