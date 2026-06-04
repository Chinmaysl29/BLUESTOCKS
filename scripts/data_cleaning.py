"""
data_cleaning.py
----------------
Bluestock Fintech Capstone — Day 2 Pre-requisite
Cleans raw datasets and writes three processed CSVs required by
notebooks/03_EDA_Analysis.ipynb:

  data/processed/nav_history_clean.csv
  data/processed/performance_clean.csv
  data/processed/transactions_clean.csv

Why required:
  Raw files may contain type mismatches, date strings, missing YoY values,
  and redundant whitespace. EDA notebooks must operate on validated, typed data.

Output files:
  nav_history_clean.csv     — parsed dates, sorted, returns computed
  performance_clean.csv     — merged with fund_master, risk_grade encoded
  transactions_clean.csv    — parsed dates, amount_inr cast, derived columns
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE   = Path(__file__).resolve().parent.parent
RAW    = BASE / "data" / "raw"
PROC   = BASE / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. NAV History  →  nav_history_clean.csv
# ---------------------------------------------------------------------------

def clean_nav_history() -> pd.DataFrame:
    """
    Clean 02_nav_history.csv.

    Steps:
      - Parse date column
      - Sort by amfi_code + date
      - Compute daily_return_pct per scheme
      - Compute 30-day rolling volatility
      - Drop any rows with null NAV
    """
    log.info("Cleaning NAV history …")
    df = pd.read_csv(RAW / "02_nav_history.csv", parse_dates=["date"])

    # Drop nulls, sort
    before = len(df)
    df.dropna(subset=["nav"], inplace=True)
    df.sort_values(["amfi_code", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    log.info("  Rows: %d → %d (dropped %d null NAV rows)", before, len(df), before - len(df))

    # Daily return per scheme
    df["daily_return_pct"] = (
        df.groupby("amfi_code")["nav"]
        .pct_change()
        .mul(100)
        .round(4)
    )

    # 30-day rolling volatility (annualised)
    df["rolling_vol_30d"] = (
        df.groupby("amfi_code")["daily_return_pct"]
        .transform(lambda x: x.rolling(30, min_periods=10).std() * np.sqrt(252))
        .round(4)
    )

    # Merge scheme name from fund_master for readability
    master = pd.read_csv(RAW / "01_fund_master.csv",
                         usecols=["amfi_code", "scheme_name", "fund_house",
                                  "category", "sub_category", "plan"])
    df = df.merge(master, on="amfi_code", how="left")

    out = PROC / "nav_history_clean.csv"
    df.to_csv(out, index=False)
    log.info("  ✅ Saved → %s  (%d rows, %d cols)", out.name, *df.shape)
    return df


# ---------------------------------------------------------------------------
# 2. Scheme Performance  →  performance_clean.csv
# ---------------------------------------------------------------------------

def clean_performance() -> pd.DataFrame:
    """
    Clean 07_scheme_performance.csv.

    Steps:
      - Merge with fund_master to add launch_date, benchmark, risk_category
      - Encode risk_grade as ordered integer (Low=1 … Very High=5)
      - Compute excess_return = return_3yr_pct - benchmark_3yr_pct
      - Compute information_ratio = alpha / std_dev_ann_pct
      - Fill any missing morningstar_rating with median per category
    """
    log.info("Cleaning scheme performance …")
    perf = pd.read_csv(RAW / "07_scheme_performance.csv")
    master = pd.read_csv(RAW / "01_fund_master.csv",
                         usecols=["amfi_code", "launch_date", "benchmark",
                                  "risk_category", "min_sip_amount",
                                  "sebi_category_code"])

    df = perf.merge(master, on="amfi_code", how="left")
    df["launch_date"] = pd.to_datetime(df["launch_date"])

    # Ordered risk encoding
    risk_map = {"Low": 1, "Moderately Low": 2, "Moderate": 3,
                "Moderately High": 4, "High": 5, "Very High": 6}
    df["risk_score"] = df["risk_grade"].map(risk_map)

    # Derived metrics
    df["excess_return"]     = (df["return_3yr_pct"] - df["benchmark_3yr_pct"]).round(4)
    df["information_ratio"] = (df["alpha"] / df["std_dev_ann_pct"]).round(4)

    # Fill missing morningstar_rating with category median
    if df["morningstar_rating"].isnull().any():
        df["morningstar_rating"] = df.groupby("category")["morningstar_rating"]\
            .transform(lambda x: x.fillna(x.median()))

    out = PROC / "performance_clean.csv"
    df.to_csv(out, index=False)
    log.info("  ✅ Saved → %s  (%d rows, %d cols)", out.name, *df.shape)
    return df


# ---------------------------------------------------------------------------
# 3. Investor Transactions  →  transactions_clean.csv
# ---------------------------------------------------------------------------

def clean_transactions() -> pd.DataFrame:
    """
    Clean 08_investor_transactions.csv.

    Steps:
      - Parse transaction_date
      - Cast amount_inr to float
      - Derive year, month, quarter columns
      - Derive amount_bucket (SIP-sized / Mid / Large)
      - Merge scheme name from fund_master
      - Flag KYC non-verified records
    """
    log.info("Cleaning investor transactions …")
    df = pd.read_csv(RAW / "08_investor_transactions.csv",
                     parse_dates=["transaction_date"])

    # Type safety
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    before = len(df)
    df.dropna(subset=["amount_inr", "transaction_date"], inplace=True)
    log.info("  Rows: %d → %d (dropped %d unparseable rows)",
             before, len(df), before - len(df))

    # Date parts
    df["year"]    = df["transaction_date"].dt.year
    df["month"]   = df["transaction_date"].dt.month
    df["quarter"] = df["transaction_date"].dt.quarter
    df["month_label"] = df["transaction_date"].dt.to_period("M").astype(str)

    # Amount buckets  (₹)
    df["amount_bucket"] = pd.cut(
        df["amount_inr"],
        bins=[0, 5_000, 50_000, 200_000, float("inf")],
        labels=["Micro (<5K)", "Small (5K-50K)",
                "Mid (50K-2L)", "Large (>2L)"],
        right=True,
    )

    # KYC flag
    df["kyc_verified"] = df["kyc_status"] == "Verified"

    # Merge scheme metadata
    master = pd.read_csv(RAW / "01_fund_master.csv",
                         usecols=["amfi_code", "scheme_name",
                                  "fund_house", "category", "sub_category"])
    df = df.merge(master, on="amfi_code", how="left")

    out = PROC / "transactions_clean.csv"
    df.to_csv(out, index=False)
    log.info("  ✅ Saved → %s  (%d rows, %d cols)", out.name, *df.shape)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=" * 60)
    log.info("  DATA CLEANING PIPELINE")
    log.info("=" * 60)
    clean_nav_history()
    clean_performance()
    clean_transactions()
    log.info("=" * 60)
    log.info("  All three cleaned files written to data/processed/")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
