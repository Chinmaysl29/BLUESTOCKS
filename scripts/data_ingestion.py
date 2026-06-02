"""
data_ingestion.py
-----------------
Batch ingestion of mutual fund NAV data from AMFI India.
Downloads the latest NAV data, parses it, and stores it in:
  - data/processed/nav_data.csv
  - data/db/mutual_funds.db  (SQLite)
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "db")

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
RAW_FILE = os.path.join(RAW_DIR, "NAVAll.txt")
PROCESSED_FILE = os.path.join(PROCESSED_DIR, "nav_data.csv")
DB_PATH = os.path.join(DB_DIR, "mutual_funds.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dirs():
    """Create output directories if they don't exist."""
    for d in [RAW_DIR, PROCESSED_DIR, DB_DIR]:
        os.makedirs(d, exist_ok=True)


def download_nav_data(url: str, dest: str) -> None:
    """Download raw NAV text file from AMFI."""
    logger.info("Downloading NAV data from %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(dest, "w", encoding="utf-8") as f:
        f.write(response.text)
    logger.info("Saved raw data to %s", dest)


def parse_nav_data(filepath: str) -> pd.DataFrame:
    """
    Parse the AMFI NAV text file into a DataFrame.

    Format (pipe-separated):
    Scheme Code|ISIN Div Payout/ISIN Growth|ISIN Div Reinvestment|Scheme Name|Net Asset Value|Date
    """
    logger.info("Parsing NAV data from %s", filepath)
    records = []

    with open(filepath, "r", encoding="utf-8") as f:
        current_category = ""
        current_amc = ""

        for line in f:
            line = line.strip()
            if not line:
                continue

            # AMC header lines contain no pipes and no numeric scheme code
            parts = line.split(";")
            if len(parts) == 6:
                try:
                    scheme_code = int(parts[0].strip())
                except ValueError:
                    continue  # skip malformed lines

                records.append(
                    {
                        "scheme_code": scheme_code,
                        "isin_growth": parts[1].strip(),
                        "isin_div_reinvest": parts[2].strip(),
                        "scheme_name": parts[3].strip(),
                        "nav": parts[4].strip(),
                        "nav_date": parts[5].strip(),
                        "amc": current_amc,
                        "category": current_category,
                    }
                )
            elif ";" not in line:
                # Likely an AMC or category header
                if line.isupper() or line.endswith("Mutual Fund"):
                    current_amc = line
                else:
                    current_category = line

    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No records parsed — check file format.")
        return df

    # Clean NAV column
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["nav_date"] = pd.to_datetime(df["nav_date"], format="%d-%b-%Y", errors="coerce")
    df.dropna(subset=["nav", "nav_date"], inplace=True)
    df["ingested_at"] = datetime.utcnow()

    logger.info("Parsed %d records", len(df))
    return df


def save_to_csv(df: pd.DataFrame, dest: str) -> None:
    df.to_csv(dest, index=False)
    logger.info("Saved processed CSV to %s", dest)


def save_to_db(df: pd.DataFrame, db_path: str) -> None:
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS nav_data (
                    scheme_code   INTEGER,
                    isin_growth   TEXT,
                    isin_div_reinvest TEXT,
                    scheme_name   TEXT,
                    nav           REAL,
                    nav_date      TEXT,
                    amc           TEXT,
                    category      TEXT,
                    ingested_at   TEXT
                )
                """
            )
        )
    df.to_sql("nav_data", engine, if_exists="append", index=False)
    logger.info("Saved %d rows to SQLite DB at %s", len(df), db_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ensure_dirs()
    download_nav_data(AMFI_URL, RAW_FILE)
    df = parse_nav_data(RAW_FILE)
    if df.empty:
        logger.error("Empty DataFrame — aborting.")
        return
    save_to_csv(df, PROCESSED_FILE)
    save_to_db(df, DB_PATH)
    logger.info("Data ingestion complete.")


if __name__ == "__main__":
    main()
