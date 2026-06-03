import pandas as pd
from sqlalchemy import create_engine


engine = create_engine(
    "sqlite:///data/db/bluestock_mf.db"
)

# Load CSVs
fund_master = pd.read_csv(
    "data/raw/01_fund_master.csv"
)

nav = pd.read_csv(
    "data/processed/nav_history_clean.csv"
)

transactions = pd.read_csv(
    "data/processed/transactions_clean.csv"
)

performance = pd.read_csv(
    "data/processed/performance_clean.csv"
)

aum = pd.read_csv(
    "data/raw/03_aum_by_fund_house.csv"
)

# Save to SQLite

fund_master.to_sql(
    "dim_fund",
    engine,
    if_exists="replace",
    index=False
)

nav.to_sql(
    "fact_nav",
    engine,
    if_exists="replace",
    index=False
)

transactions.to_sql(
    "fact_transaction",
    engine,
    if_exists="replace",
    index=False
)

performance.to_sql(
    "fact_performance",
    engine,
    if_exists="replace",
    index=False
)

aum.to_sql(
    "fact_aum",
    engine,
    if_exists="replace",
    index=False
)

print("Database Loaded Successfully")
