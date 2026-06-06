"""Verify project structure matches required specification."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

checks = [
    ("notebooks/01_data_ingestion.ipynb",       "Notebook 1 - Data Ingestion"),
    ("notebooks/02_data_cleaning.ipynb",         "Notebook 2 - Data Cleaning"),
    ("notebooks/03_eda_analysis.ipynb",          "Notebook 3 - EDA Analysis"),
    ("notebooks/04_performance_analytics.ipynb", "Notebook 4 - Performance Analytics"),
    ("notebooks/05_advanced_analytics.ipynb",    "Notebook 5 - Advanced Analytics"),
    ("scripts/etl_pipeline.py",                  "Script - ETL Pipeline"),
    ("scripts/live_nav_fetch.py",                "Script - Live NAV Fetch"),
    ("scripts/compute_metrics.py",               "Script - Compute Metrics"),
    ("scripts/recommender.py",                   "Script - Recommender"),
    ("sql/schema.sql",                           "SQL - Schema DDL"),
    ("sql/queries.sql",                          "SQL - Business Queries"),
    ("dashboard",                                "Dashboard folder"),
    ("reports/Final_Report.pdf",                 "Report - Final PDF"),
    ("reports/Presentation.pptx",               "Report - Presentation PPTX"),
    ("data/raw",                                 "Data - raw/"),
    ("data/processed",                           "Data - processed/"),
    ("data/db",                                  "Data - db/"),
    ("data/db/bluestock_mf.db",                  "Database - bluestock_mf.db"),
    ("README.md",                                "README.md"),
    (".gitignore",                               ".gitignore"),
    ("requirements.txt",                         "requirements.txt"),
]

ok = 0
fail = 0
print("=" * 70)
print("  PROJECT STRUCTURE VERIFICATION")
print("=" * 70)
for path, desc in checks:
    p = BASE / path
    exists = p.exists()
    size = ""
    if exists and p.is_file():
        size = f"  [{p.stat().st_size // 1024} KB]"
    status = "[OK]  " if exists else "[MISS]"
    if exists:
        ok += 1
    else:
        fail += 1
    print(f"  {status}  {desc:<42}  {path}{size}")

print()
verdict = "COMPLETE" if fail == 0 else "INCOMPLETE"
print(f"  Result: {ok}/{ok+fail} items present  --  {verdict}")
print("=" * 70)
