# Bluestock Mutual Fund Analytics Capstone

End-to-end mutual fund analytics platform covering ETL, SQL analytics,
EDA, risk-return metrics, fund scoring, and a recommendation engine.

## Project Structure

```
mutual_fund_analysis/
├── data/
│   ├── raw/                    # 10 original CSV datasets
│   ├── processed/              # Cleaned datasets + analytical outputs
│   └── db/                     # bluestock_mf.db (SQLite)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── etl_pipeline.py         # End-to-end ETL (extract/transform/load)
│   ├── live_nav_fetch.py       # Live NAV fetcher via mfapi.in
│   ├── compute_metrics.py      # CAGR, Sharpe, Sortino, Alpha, Beta, MDD
│   └── recommender.py          # Risk-profile fund recommendation engine
├── sql/
│   ├── schema.sql              # Star schema DDL (5 tables)
│   └── queries.sql             # 10 business analytics queries
├── dashboard/
│   └── README_dashboard.md     # Power BI setup guide
├── reports/
│   ├── Final_Report.pdf        # Full project report (10 sections)
│   ├── Presentation.pptx       # 10-slide presentation
│   └── *.png                   # 20+ EDA and analytics charts
├── requirements.txt
├── README.md
└── .gitignore
```

## Datasets (data/raw/)

| File | Rows | Description |
|------|------|-------------|
| 01_fund_master.csv | 40 | Scheme metadata — AMC, category, expense ratio |
| 02_nav_history.csv | 46,000 | Daily NAV 2022-2026 |
| 03_aum_by_fund_house.csv | 90 | Bi-annual AUM per AMC |
| 04_monthly_sip_inflows.csv | 48 | Industry SIP statistics |
| 05_category_inflows.csv | 144 | Monthly net inflows by category |
| 06_industry_folio_count.csv | 21 | Quarterly folio counts |
| 07_scheme_performance.csv | 40 | Risk-return metrics |
| 08_investor_transactions.csv | 32,778 | Investor transaction ledger |
| 09_portfolio_holdings.csv | 322 | Equity holdings per scheme |
| 10_benchmark_indices.csv | 8,050 | NIFTY50 + 6 benchmark indices |

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run ETL Pipeline

```bash
python scripts/etl_pipeline.py               # Full pipeline
python scripts/etl_pipeline.py --step extract
python scripts/etl_pipeline.py --step transform
python scripts/etl_pipeline.py --step load
```

## Run Recommendation Engine

```python
from scripts.recommender import recommend
recommend("Low")      # risk_score <= 2
recommend("Medium")   # risk_score <= 4
recommend("High")     # all funds
```

## Launch Notebooks

```bash
jupyter notebook notebooks/
```

## Key Results

| Metric | Value |
|--------|-------|
| Total schemes | 40 |
| Total AMCs | 10 |
| Total records | 87,533 |
| Best composite score | SBI Small Cap Direct (100.0) |
| Best 3Y return | SBI Small Cap Regular (23.39%) |
| Best Sharpe | Mirae Asset Large Cap (1.45) |
| Top 5 outperformance vs NIFTY50 | +106.21% |
| ETL runtime | 1.8 seconds |
| Final validation | 38/38 checks PASSED |

## Tech Stack

Python · Pandas · NumPy · Matplotlib · Seaborn · Plotly ·
SQLite · SQLAlchemy · scikit-learn · fpdf2 · python-pptx ·
Requests · SciPy · Jupyter

## License

MIT
