"""Print all benchmark columns, formats, and category mapping."""
import pandas as pd

bench = pd.read_csv("data/raw/10_benchmark_indices.csv", parse_dates=["date"])
bench_wide = bench.pivot_table(index="date", columns="index_name", values="close_value")
bench_wide.columns.name = None
bench_ret = bench_wide.pct_change().mul(100)

print("=" * 60)
print("  BENCHMARK DATASET — COMPLETE COLUMN REFERENCE")
print("=" * 60)

print("\n1. RAW FILE columns (long format):")
for c in bench.columns:
    print(f"     {c}")

print("\n2. UNIQUE index_name values:")
for i in bench["index_name"].unique():
    count = (bench["index_name"] == i).sum()
    print(f"     {i:<20}  ({count} rows)")

print("\n3. WIDE FORMAT columns — bench_wide (after pivot):")
for c in bench_wide.columns:
    print(f'     bench_wide["{c}"]')

print("\n4. DAILY RETURN columns — bench_ret (after pct_change * 100):")
for c in bench_ret.columns:
    print(f'     bench_ret["{c}"]')

print(f"\n5. SHAPE:  raw={bench.shape}  wide={bench_wide.shape}  ret={bench_ret.shape}")
print(f"   Date range: {bench['date'].min().date()} -> {bench['date'].max().date()}")

print("\n6. CATEGORY -> BENCHMARK MAPPING (for Alpha/Beta):")
mapping = {
    "Large Cap"      : "NIFTY100",
    "Mid Cap"        : "NIFTY_MIDCAP150",
    "Small Cap"      : "BSE_SMALLCAP",
    "Flexi Cap"      : "NIFTY500",
    "Large & Mid Cap": "NIFTY500",
    "Value"          : "NIFTY500",
    "ELSS"           : "NIFTY500",
    "Index/ETF"      : "NIFTY50",
    "Index"          : "NIFTY50",
    "Gilt"           : "CRISIL_GILT",
    "Liquid"         : "CRISIL_LIQUID",
    "Short Duration" : "CRISIL_GILT",
}
for cat, idx in mapping.items():
    print(f"     {cat:<20}  ->  {idx}")

print("\n7. bench_wide sample (head 3):")
print(bench_wide.head(3).round(2).to_string())

print("\n8. bench_ret (daily % returns) sample (head 3):")
print(bench_ret.head(3).round(4).to_string())

print("\n9. Daily return stats per index:")
print(bench_ret.describe().round(4).to_string())
