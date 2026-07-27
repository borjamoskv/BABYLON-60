import logging
import os
import sys

from babylon60.database.core import connect

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.extensions.timing import TimingTracker


def verify_daily_data():
    db_path = os.path.expanduser("~/.babylon60/babylon60.db")
    if not os.path.exists(db_path):
        logging.getLogger(__name__).info(f"Database not found at {db_path}")
        return

    conn = connect(db_path)
    tracker = TimingTracker(conn)

    logging.getLogger(__name__).info("--- Verifying matches for daily() ---")
    daily_stats = tracker.daily(days=7)
    logging.getLogger(__name__).info(daily_stats)

    total_seconds = sum(d["seconds"] for d in daily_stats)
    logging.getLogger(__name__).info(f"Total seconds in last 7 days: {total_seconds}")
    logging.getLogger(__name__).info(f"Total hours: {total_seconds / 3600:.2f}")

    if total_seconds > 0:
        logging.getLogger(__name__).info("✅ Data found for chart.")
    else:
        logging.getLogger(__name__).info("⚠️ No data found (Simulation might be needed if this is 0).")


if __name__ == "__main__":
    verify_daily_data()
