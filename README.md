# Bluestock Mutual Fund Capstone

An end-to-end mutual fund data analysis platform covering data ingestion, live NAV tracking, SQL-based analytics, and an interactive dashboard.

## Project Structure

```
mutual_fund_analysis/
├── data/
│   ├── raw/          # Raw downloaded data (CSV, JSON, etc.)
│   ├── processed/    # Cleaned and transformed data
│   └── db/           # SQLite database files
├── notebooks/
│   └── 01_data_ingestion.ipynb   # Exploratory data ingestion notebook
├── scripts/
│   ├── data_ingestion.py         # Batch data ingestion pipeline
│   └── live_nav_fetch.py         # Live NAV fetcher (scheduled)
├── sql/              # SQL queries and schema definitions
├── dashboard/        # Dash/Plotly dashboard app
├── reports/          # Generated reports and charts
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Data Ingestion
```bash
python scripts/data_ingestion.py
```

### Live NAV Fetch
```bash
python scripts/live_nav_fetch.py
```

### Jupyter Notebooks
```bash
jupyter notebook notebooks/
```

## Data Sources
- AMFI India NAV data: https://www.amfiindia.com/spages/NAVAll.txt
- Additional fund metadata via public APIs

## License
MIT
