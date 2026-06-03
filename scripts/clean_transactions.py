import pandas as pd


df = pd.read_csv(
    "data/raw/08_investor_transactions.csv"
)

df["transaction_date"] = pd.to_datetime(
    df["transaction_date"]
)

df["transaction_type"] = (
    df["transaction_type"]
    .str.strip()
    .str.title()
)

valid_types = [
    "Sip",
    "Lumpsum",
    "Redemption"
]

df = df[
    df["transaction_type"]
    .isin(valid_types)
]

df = df[
    df["amount_inr"] > 0
]

df = df.drop_duplicates()

df.to_csv(
    "data/processed/transactions_clean.csv",
    index=False
)

print(df.shape)
