"""
live_nav_fetch.py
-----------------
Fetches live / latest NAV for a watchlist of scheme codes on a schedule
and appends results to data/processed/live_nav.csv and the SQLite DB.

Usage:
    python scripts/live_nav_fetch.py              # runs scheduler indefinitely
    python scripts/live_nav_fetch.py --once       # single fetch and exit
"""

import os
import sys
import logging
import argparse
import requests
import pandas as pd
import schedule
import time
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "db")

LIVE_NAV_CSV = os.path.join(PROCESSED_DIR, "live_nav.csv")
DB_PATH = os.path.join(DB_DIR, "mutual_funds.db")

# AMFI open API endpoint for a single scheme NAV
AMFI_API = "https://api.mfapi.in/mf/{scheme_code}"

# Edit this list with the scheme codes you want to track
WATCHLIST: list[int] = [
    125497,  # HDFC Top 100 Direct
    119551,  # SBI Bluechip
    120503,  # ICICI Bluechip
    118632,  # Nippon Large Cap
    119092,  # Axis Bluechip
    120841   # Kotak Bluechip

]

FETCH_INTERVAL_MINUTES = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def ensure_dirs():
    for d in [PROCESSED_DIR, DB_DIR]:
        os.makedirs(d, exist_ok=True)


def fetch_nav(scheme_code: int) -> dict | None:
    """Fetch latest NAV for a single scheme from mfapi.in."""
    url = AMFI_API.format(scheme_code=scheme_code)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        latest = data.get("data", [{}])[0]
        return {
            "scheme_code": scheme_code,
            "scheme_name": data.get("meta", {}).get("scheme_name", ""),
            "nav": float(latest.get("nav", 0)),
            "nav_date": latest.get("date", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.warning("Failed to fetch NAV for scheme %s: %s", scheme_code, exc)
        return None


def fetch_all(watchlist: list[int]) -> pd.DataFrame:
    records = []
    for code in watchlist:
        result = fetch_nav(code)
        if result:
            records.append(result)
            logger.info("  %-10s  NAV: %-10s  Date: %s", code, result["nav"], result["nav_date"])
    return pd.DataFrame(records)


def append_to_csv(df: pd.DataFrame, path: str) -> None:
    header = not os.path.exists(path)
    df.to_csv(path, mode="a", index=False, header=header)
    logger.info("Appended %d rows to %s", len(df), path)


def append_to_db(df: pd.DataFrame, db_path: str) -> None:
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS live_nav (
                    scheme_code  INTEGER,
                    scheme_name  TEXT,
                    nav          REAL,
                    nav_date     TEXT,
                    fetched_at   TEXT
                )
                """
            )
        )
    df.to_sql("live_nav", engine, if_exists="append", index=False)
    logger.info("Appended %d rows to SQLite live_nav table", len(df))


def run_fetch():
    logger.info("=== Starting live NAV fetch for %d schemes ===", len(WATCHLIST))
    df = fetch_all(WATCHLIST)
    if df.empty:
        logger.warning("No data fetched this run.")
        return
    append_to_csv(df, LIVE_NAV_CSV)
    append_to_db(df, DB_PATH)
    logger.info("=== Fetch complete ===")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Live NAV fetcher for mutual funds")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch once and exit (no scheduler)",
    )
    args = parser.parse_args()

    ensure_dirs()

    if args.once:
        run_fetch()
        return

    logger.info("Scheduler started — fetching every %d minutes.", FETCH_INTERVAL_MINUTES)
    run_fetch()  # immediate first run
    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(run_fetch)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
