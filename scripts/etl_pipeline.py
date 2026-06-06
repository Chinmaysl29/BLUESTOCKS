"""
etl_pipeline.py
---------------
Bluestock Mutual Fund Analytics Capstone

End-to-end ETL pipeline:
  1. EXTRACT  — validate raw CSV files exist
  2. TRANSFORM — clean NAV, performance, transactions
  3. LOAD     — write processed CSVs + load into SQLite

Usage:
    python scripts/etl_pipeline.py              # full pipeline
    python scripts/etl_pipeline.py --step extract
    python scripts/etl_pipeline.py --step transform
    python scripts/etl_pipeline.py --step load
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ── Paths ─────────────────────────────────────────────────────────────────
BASE  = Path(__file__).resolve().parent.parent
RAW   = BASE / "data" / "raw"
PROC  = BASE / "data" / "processed"
DB    = BASE / "data" / "db" / "bluestock_mf.db"

PROC.mkdir(parents=True, exist_ok=True)
(BASE / "data" / "db").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Required raw files ─────────────────────────────────────────────────────
RAW_FILES = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — EXTRACT
# ══════════════════════════════════════════════════════════════════════════

def extract() -> dict[str, pd.DataFrame]:
    """Validate and load all 10 raw CSV files."""
    log.info("=== STEP 1: EXTRACT ===")
    dfs: dict[str, pd.DataFrame] = {}
    missing = []

    for fname in RAW_FILES:
        path = RAW / fname
        if not path.exists():
            log.error("Missing: %s", path)
            missing.append(fname)
            continue
        df = pd.read_csv(path)
        dfs[fname] = df
        log.info("  %-40s  %d rows × %d cols", fname, *df.shape)

    if missing:
        raise FileNotFoundError(f"Missing raw files: {missing}")

    log.info("Extract complete — %d datasets loaded", len(dfs))
    return dfs


# ══════════════════════════════════════════════════════════════════════════
# STEP 2 — TRANSFORM
# ══════════════════════════════════════════════════════════════════════════

def transform(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Clean and enrich raw datasets."""
    log.info("=== STEP 2: TRANSFORM ===")
    out: dict[str, pd.DataFrame] = {}

    fund_master = pd.read_csv(RAW / "01_fund_master.csv", parse_dates=["launch_date"])

    # ── NAV history ──────────────────────────────────────────────────────
    log.info("  Transforming NAV history ...")
    nav = dfs["02_nav_history.csv"].copy()
    nav["date"] = pd.to_datetime(nav["date"])
    nav.dropna(subset=["nav"], inplace=True)
    nav.sort_values(["amfi_code", "date"], inplace=True)
    nav.reset_index(drop=True, inplace=True)

    nav["daily_return_pct"] = (
        nav.groupby("amfi_code")["nav"].pct_change().mul(100).round(4)
    )
    nav["rolling_vol_30d"] = (
        nav.groupby("amfi_code")["daily_return_pct"]
        .transform(lambda x: x.rolling(30, min_periods=10).std() * np.sqrt(252))
        .round(4)
    )
    master_cols = ["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "plan"]
    nav = nav.merge(fund_master[master_cols], on="amfi_code", how="left")
    out["nav_history_clean"] = nav
    log.info("  NAV history: %d rows × %d cols", *nav.shape)

    # ── Scheme performance ───────────────────────────────────────────────
    log.info("  Transforming scheme performance ...")
    perf = dfs["07_scheme_performance.csv"].copy()
    master_extra = fund_master[["amfi_code", "launch_date", "benchmark",
                                "risk_category", "min_sip_amount", "sebi_category_code"]]
    perf = perf.merge(master_extra, on="amfi_code", how="left")
    risk_map = {"Low": 1, "Moderately Low": 2, "Moderate": 3,
                "Moderately High": 4, "High": 5, "Very High": 6}
    perf["risk_score"]        = perf["risk_grade"].map(risk_map)
    perf["excess_return"]     = (perf["return_3yr_pct"] - perf["benchmark_3yr_pct"]).round(4)
    perf["information_ratio"] = (perf["alpha"] / perf["std_dev_ann_pct"]).round(4)
    out["performance_clean"] = perf
    log.info("  Performance: %d rows × %d cols", *perf.shape)

    # ── Investor transactions ────────────────────────────────────────────
    log.info("  Transforming investor transactions ...")
    txn = dfs["08_investor_transactions.csv"].copy()
    txn["amount_inr"]       = pd.to_numeric(txn["amount_inr"], errors="coerce")
    txn["transaction_date"] = pd.to_datetime(txn["transaction_date"])
    txn.dropna(subset=["amount_inr", "transaction_date"], inplace=True)
    txn["year"]         = txn["transaction_date"].dt.year
    txn["month"]        = txn["transaction_date"].dt.month
    txn["quarter"]      = txn["transaction_date"].dt.quarter
    txn["month_label"]  = txn["transaction_date"].dt.to_period("M").astype(str)
    txn["kyc_verified"] = txn["kyc_status"] == "Verified"
    txn["amount_bucket"] = pd.cut(
        txn["amount_inr"],
        bins=[0, 5_000, 50_000, 200_000, float("inf")],
        labels=["Micro (<5K)", "Small (5K-50K)", "Mid (50K-2L)", "Large (>2L)"],
    )
    master_txn = fund_master[["amfi_code", "scheme_name", "fund_house",
                               "category", "sub_category"]]
    txn = txn.merge(master_txn, on="amfi_code", how="left")
    out["transactions_clean"] = txn
    log.info("  Transactions: %d rows × %d cols", *txn.shape)

    log.info("Transform complete — %d datasets ready", len(out))
    return out


# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — LOAD
# ══════════════════════════════════════════════════════════════════════════

def load(transformed: dict[str, pd.DataFrame]) -> None:
    """Write processed CSVs and load into SQLite."""
    log.info("=== STEP 3: LOAD ===")

    # CSV output
    for name, df in transformed.items():
        out_path = PROC / f"{name}.csv"
        df.to_csv(out_path, index=False)
        log.info("  Saved CSV: %-40s  %d rows", out_path.name, len(df))

    # SQLite
    engine = create_engine(f"sqlite:///{DB}")
    log.info("  Loading into SQLite: %s", DB)

    nav_db = transformed["nav_history_clean"][
        ["amfi_code", "date", "nav", "daily_return_pct"]
    ]
    nav_db.to_sql("fact_nav", engine, if_exists="replace", index=False)
    log.info("  fact_nav: %d rows", len(nav_db))

    perf_db = transformed["performance_clean"][
        ["amfi_code", "scheme_name", "return_1yr_pct", "return_3yr_pct",
         "return_5yr_pct", "alpha", "beta", "sharpe_ratio",
         "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
         "expense_ratio_pct", "risk_grade", "risk_score"]
    ]
    perf_db.to_sql("fact_performance", engine, if_exists="replace", index=False)
    log.info("  fact_performance: %d rows", len(perf_db))

    txn_db = transformed["transactions_clean"][
        ["investor_id", "transaction_date", "amfi_code",
         "transaction_type", "amount_inr", "state", "city",
         "age_group", "gender", "kyc_status", "month_label"]
    ]
    txn_db.to_sql("fact_transaction", engine, if_exists="replace", index=False)
    log.info("  fact_transaction: %d rows", len(txn_db))

    # Fund master
    fund_master = pd.read_csv(RAW / "01_fund_master.csv")
    fund_master.to_sql("dim_fund", engine, if_exists="replace", index=False)
    log.info("  dim_fund: %d rows", len(fund_master))

    # AUM
    aum = pd.read_csv(RAW / "03_aum_by_fund_house.csv")
    aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
    log.info("  fact_aum: %d rows", len(aum))

    log.info("Load complete — database: %s", DB)


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main(step: str = "all") -> None:
    """Run the full ETL pipeline or a single step."""
    started = datetime.now(timezone.utc)
    log.info("ETL Pipeline started — step=%s", step)

    if step in ("all", "extract"):
        raw_data = extract()
    else:
        raw_data = {f: pd.read_csv(RAW / f) for f in RAW_FILES if (RAW / f).exists()}

    if step in ("all", "transform"):
        processed = transform(raw_data)
    else:
        processed = {
            p.stem: pd.read_csv(p)
            for p in PROC.glob("*.csv")
        }

    if step in ("all", "load"):
        load(processed)

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    log.info("ETL Pipeline complete in %.1f seconds", elapsed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluestock MF ETL Pipeline")
    parser.add_argument("--step", choices=["all", "extract", "transform", "load"],
                        default="all", help="Pipeline step to run")
    args = parser.parse_args()
    main(args.step)
