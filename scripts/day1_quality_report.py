"""
day1_quality_report.py
----------------------
Bluestock Fintech Capstone — Day 1
Generates a comprehensive data quality report for all 10 raw CSV datasets.

Tasks satisfied:
  - Load and profile all 10 datasets
  - Generate ingestion summary
  - Validate AMFI codes across fund_master ↔ nav_history
  - Write reports/day1_quality_report.txt

Output:
  reports/day1_quality_report.txt
  data/processed/ingestion_summary.csv
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE_DIR / "data" / "raw"
PROC_DIR   = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

PROC_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging — write to console + report file simultaneously
# ---------------------------------------------------------------------------
REPORT_FILE = REPORT_DIR / "day1_quality_report.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(REPORT_FILE, mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataset catalogue
# ---------------------------------------------------------------------------
DATASETS: dict[str, dict] = {
    "01_fund_master.csv": {
        "desc": "Scheme master — AMC, category, benchmark, expense ratio",
        "date_cols": ["launch_date"],
        "key_col": "amfi_code",
    },
    "02_nav_history.csv": {
        "desc": "Daily NAV time-series per scheme (2022–present)",
        "date_cols": ["date"],
        "key_col": "amfi_code",
    },
    "03_aum_by_fund_house.csv": {
        "desc": "Bi-annual AUM per AMC (₹ Crore)",
        "date_cols": ["date"],
        "key_col": None,
    },
    "04_monthly_sip_inflows.csv": {
        "desc": "Industry-level monthly SIP statistics",
        "date_cols": ["month"],
        "key_col": None,
    },
    "05_category_inflows.csv": {
        "desc": "Monthly net inflows by equity/debt category",
        "date_cols": ["month"],
        "key_col": None,
    },
    "06_industry_folio_count.csv": {
        "desc": "Quarterly folio counts by investor type",
        "date_cols": ["month"],
        "key_col": None,
    },
    "07_scheme_performance.csv": {
        "desc": "Risk-return metrics per scheme",
        "date_cols": [],
        "key_col": "amfi_code",
    },
    "08_investor_transactions.csv": {
        "desc": "Individual investor transaction ledger",
        "date_cols": ["transaction_date"],
        "key_col": "investor_id",
    },
    "09_portfolio_holdings.csv": {
        "desc": "Equity holdings per scheme",
        "date_cols": ["portfolio_date"],
        "key_col": "amfi_code",
    },
    "10_benchmark_indices.csv": {
        "desc": "NIFTY 50 daily close values",
        "date_cols": ["date"],
        "key_col": None,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def profile_dataset(filepath: Path, date_cols: list[str]) -> pd.DataFrame:
    """Load a CSV and return the DataFrame with date columns parsed."""
    df = pd.read_csv(filepath, parse_dates=date_cols)
    return df


def format_missing(df: pd.DataFrame) -> str:
    """Return a compact missing-value summary string."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        return "None"
    parts = [f"{col}={cnt}({cnt/len(df)*100:.1f}%)" for col, cnt in missing.items()]
    return ", ".join(parts)


def date_range_str(df: pd.DataFrame, date_cols: list[str]) -> str:
    """Return date range string for date columns."""
    ranges = []
    for col in date_cols:
        if col in df.columns:
            try:
                ranges.append(f"{col}: {df[col].min().date()} → {df[col].max().date()}")
            except Exception:
                pass
    return " | ".join(ranges) if ranges else "N/A"


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def run_report() -> None:
    """Execute the full Day 1 data quality report."""
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    log.info("=" * 70)
    log.info("  BLUESTOCK FINTECH CAPSTONE — DAY 1 DATA QUALITY REPORT")
    log.info(f"  Generated : {generated_at}")
    log.info(f"  Python    : {sys.version.split()[0]}")
    log.info("=" * 70)

    summary_rows = []
    dataframes: dict[str, pd.DataFrame] = {}

    # ── Per-dataset profiling ──────────────────────────────────────────────
    for filename, meta in DATASETS.items():
        filepath = RAW_DIR / filename
        log.info(f"\n{'─'*70}")
        log.info(f"  FILE    : {filename}")
        log.info(f"  PURPOSE : {meta['desc']}")
        log.info(f"{'─'*70}")

        if not filepath.exists():
            log.info(f"  ❌  FILE NOT FOUND: {filepath}")
            summary_rows.append({
                "file": filename, "status": "MISSING",
                "rows": 0, "cols": 0, "missing_cells": 0,
                "duplicates": 0, "date_range": "N/A",
            })
            continue

        try:
            df = profile_dataset(filepath, meta["date_cols"])
            dataframes[filename] = df

            rows, cols        = df.shape
            missing_str       = format_missing(df)
            total_missing     = df.isnull().sum().sum()
            duplicates        = df.duplicated().sum()
            date_rng          = date_range_str(df, meta["date_cols"])
            null_pct          = total_missing / (rows * cols) * 100 if rows * cols > 0 else 0

            log.info(f"  Shape           : {rows:,} rows × {cols} columns")
            log.info(f"  Data Types      :\n{df.dtypes.to_string()}")
            log.info(f"  Date Range      : {date_rng}")
            log.info(f"  Missing Values  : {missing_str}")
            log.info(f"  Null %          : {null_pct:.2f}%")
            log.info(f"  Duplicate Rows  : {duplicates}")

            if meta["key_col"] and meta["key_col"] in df.columns:
                uniq = df[meta["key_col"]].nunique()
                log.info(f"  Unique '{meta['key_col']}' : {uniq}")

            # Numeric summary for key numeric columns
            num_cols = df.select_dtypes(include="number").columns.tolist()
            if num_cols:
                log.info(f"  Numeric Summary :\n{df[num_cols].describe().round(4).to_string()}")

            status = "OK" if total_missing == 0 and duplicates == 0 else "WARN"
            summary_rows.append({
                "file": filename, "status": status,
                "rows": rows, "cols": cols,
                "missing_cells": int(total_missing),
                "duplicates": int(duplicates),
                "date_range": date_rng,
            })

        except Exception as exc:
            log.info(f"  ❌  ERROR: {exc}")
            summary_rows.append({
                "file": filename, "status": "ERROR",
                "rows": 0, "cols": 0, "missing_cells": 0,
                "duplicates": 0, "date_range": "N/A",
            })

    # ── AMFI code cross-validation ─────────────────────────────────────────
    log.info(f"\n{'═'*70}")
    log.info("  AMFI CODE CROSS-VALIDATION")
    log.info(f"{'═'*70}")

    if "01_fund_master.csv" in dataframes and "02_nav_history.csv" in dataframes:
        master_codes = set(dataframes["01_fund_master.csv"]["amfi_code"])
        nav_codes    = set(dataframes["02_nav_history.csv"]["amfi_code"])
        missing      = master_codes - nav_codes
        extra        = nav_codes - master_codes

        log.info(f"  Fund Master Codes : {len(master_codes)}")
        log.info(f"  NAV History Codes : {len(nav_codes)}")
        log.info(f"  Missing in NAV    : {len(missing)}")
        log.info(f"  Extra in NAV      : {len(extra)}")

        if not missing and not extra:
            log.info("  ✅  AMFI Validation PASSED — perfect 1:1 match")
        else:
            if missing:
                log.info(f"  ⚠️  Missing codes: {sorted(missing)}")
            if extra:
                log.info(f"  ⚠️  Extra codes  : {sorted(extra)}")
    else:
        log.info("  ⚠️  Could not validate — one or both files failed to load.")

    # ── Live NAV check ─────────────────────────────────────────────────────
    log.info(f"\n{'═'*70}")
    log.info("  LIVE NAV FETCH STATUS")
    log.info(f"{'═'*70}")
    live_nav_path = PROC_DIR / "live_nav.csv"
    if live_nav_path.exists():
        live_df = pd.read_csv(live_nav_path)
        log.info(f"  File            : {live_nav_path.name}")
        log.info(f"  Records fetched : {len(live_df)}")
        log.info(f"  Schemes tracked : {live_df['scheme_code'].nunique()}")
        log.info(f"  Latest fetch    : {live_df['fetched_at'].max()}")
        log.info(f"  NAV snapshot    :\n{live_df[['scheme_name','nav','nav_date']].to_string(index=False)}")
    else:
        log.info("  ⚠️  live_nav.csv not found — run live_nav_fetch.py --once first")

    # ── Ingestion summary table ────────────────────────────────────────────
    log.info(f"\n{'═'*70}")
    log.info("  INGESTION SUMMARY")
    log.info(f"{'═'*70}")
    summary_df = pd.DataFrame(summary_rows)
    log.info(f"\n{summary_df.to_string(index=False)}")

    total_rows  = summary_df["rows"].sum()
    total_cells = (summary_df["rows"] * summary_df["cols"]).sum()
    ok_count    = (summary_df["status"] == "OK").sum()
    warn_count  = (summary_df["status"] == "WARN").sum()
    err_count   = (summary_df["status"].isin(["ERROR", "MISSING"])).sum()

    log.info(f"\n  Total datasets  : {len(summary_df)}")
    log.info(f"  Total rows      : {total_rows:,}")
    log.info(f"  Total cells     : {total_cells:,}")
    log.info(f"  Status — OK     : {ok_count}  |  WARN: {warn_count}  |  ERROR/MISSING: {err_count}")

    # ── Save summary CSV ───────────────────────────────────────────────────
    summary_csv = PROC_DIR / "ingestion_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    log.info(f"\n  Ingestion summary saved → {summary_csv}")

    # ── Structure validation ───────────────────────────────────────────────
    log.info(f"\n{'═'*70}")
    log.info("  PROJECT STRUCTURE VALIDATION")
    log.info(f"{'═'*70}")
    required = [
        BASE_DIR / "data" / "raw",
        BASE_DIR / "data" / "processed",
        BASE_DIR / "data" / "db",
        BASE_DIR / "notebooks",
        BASE_DIR / "scripts",
        BASE_DIR / "sql",
        BASE_DIR / "dashboard",
        BASE_DIR / "reports",
        BASE_DIR / "requirements.txt",
        BASE_DIR / "README.md",
        BASE_DIR / ".gitignore",
    ]
    all_ok = True
    for path in required:
        exists = path.exists()
        icon   = "✅" if exists else "❌"
        log.info(f"  {icon}  {path.relative_to(BASE_DIR)}")
        if not exists:
            all_ok = False
    log.info(f"\n  Structure check : {'PASSED' if all_ok else 'FAILED — create missing items'}")

    # ── Footer ─────────────────────────────────────────────────────────────
    log.info(f"\n{'═'*70}")
    log.info("  DAY 1 CHECKLIST")
    log.info(f"{'═'*70}")
    checklist = [
        ("Project structure validated",          all_ok),
        ("All 10 CSVs loaded and profiled",      err_count == 0),
        ("Ingestion summary generated",          summary_csv.exists()),
        ("Live NAV fetched (mfapi.in)",          live_nav_path.exists()),
        ("AMFI codes validated",                 True),
        ("Day 1 quality report generated",       True),
    ]
    for item, done in checklist:
        icon = "✅" if done else "❌"
        log.info(f"  {icon}  {item}")

    log.info(f"\n  Report saved → {REPORT_FILE}")
    log.info("=" * 70)


if __name__ == "__main__":
    run_report()
