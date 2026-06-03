import pandas as pd


df = pd.read_csv(
    "data/raw/07_scheme_performance.csv"
)

numeric_cols = [
    "return_1yr_pct",
    "return_3yr_pct",
    "benchmark_3yr_pct",
    "alpha",
    "std_dev_ann_pct"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df[
    df["expense_ratio_pct"]
    .between(0.1, 2.5)
]

df = df.drop_duplicates()

df.to_csv(
    "data/processed/performance_clean.csv",
    index=False
)

print(df.shape)
