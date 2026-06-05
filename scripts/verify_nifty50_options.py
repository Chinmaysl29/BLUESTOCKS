"""
verify_nifty50_options.py
--------------------------
Bluestock Fintech Capstone

Verifies both NIFTY50 filter options and updates
benchmark_comparison.py to use the production-safe Option 2.

Option 1: benchmark[benchmark["index_name"] == "NIFTY50"]
Option 2: benchmark[benchmark["index_name"].str.replace(" ","").str.upper() == "NIFTY50"]
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
RAW  = BASE / "data" / "raw"
RPT  = BASE / "reports"

sns.set_theme(style="whitegrid")

benchmark = pd.read_csv(RAW  / "10_benchmark_indices.csv", parse_dates=["date"])
top_nav   = pd.read_csv(PROC / "top5_nav.csv",             parse_dates=["date"])
scorecard = pd.read_csv(PROC / "fund_scorecard.csv")

# ── Print all unique index names ──────────────────────────────────────────
print("=" * 60)
print("  ALL UNIQUE index_name VALUES IN DATASET")
print("=" * 60)
for name in benchmark["index_name"].unique():
    print(f"  {repr(name)}")

print()

# ── Option 1 — exact match ────────────────────────────────────────────────
nifty50_opt1 = benchmark[benchmark["index_name"] == "NIFTY50"]
print(f"Option 1  benchmark['index_name'] == 'NIFTY50'")
print(f"  Rows      : {len(nifty50_opt1)}")
print(f"  Date range: {nifty50_opt1['date'].min().date()} -> {nifty50_opt1['date'].max().date()}")
close_min1 = nifty50_opt1['close_value'].min()
close_max1 = nifty50_opt1['close_value'].max()
print(f"  Close     : {close_min1:.2f} -> {close_max1:.2f}")
print()

# ── Option 2 — flexible ───────────────────────────────────────────────────
nifty50_opt2 = benchmark[
    benchmark["index_name"].str.replace(" ", "").str.upper() == "NIFTY50"
]
print(f"Option 2  str.replace(' ','').str.upper() == 'NIFTY50'")
print(f"  Rows      : {len(nifty50_opt2)}")
print(f"  Date range: {nifty50_opt2['date'].min().date()} -> {nifty50_opt2['date'].max().date()}")
close_min2 = nifty50_opt2['close_value'].min()
close_max2 = nifty50_opt2['close_value'].max()
print(f"  Close     : {close_min2:.2f} -> {close_max2:.2f}")
print()

# ── Verify identical results ──────────────────────────────────────────────
r1 = nifty50_opt1.reset_index(drop=True)
r2 = nifty50_opt2.reset_index(drop=True)
same = r1.equals(r2)
print(f"Both options produce identical DataFrame : {same}")
print()
if same:
    print("  Use Option 1 for this dataset — simpler and faster.")
    print("  Use Option 2 when data may have inconsistent spacing.")

# ── Use Option 2 (production-safe) for the final chart ────────────────────
nifty50 = nifty50_opt2.copy()

# ── Reproduce benchmark_comparison.py with correct filter ─────────────────
print()
print("=" * 60)
print("  REGENERATING benchmark_comparison.png with Option 2")
print("=" * 60)

plt.figure(figsize=(12, 6))
plt.plot(top_nav["date"],    top_nav["nav"],           label="Top 5 Funds",
         color="steelblue",  linewidth=2.2)
plt.plot(nifty50["date"],    nifty50["close_value"],   label="NIFTY 50",
         color="darkorange", linewidth=1.8, linestyle="--")
plt.legend(fontsize=11)
plt.title("Top Funds vs NIFTY 50", fontsize=14, fontweight="bold")
plt.xlabel("Date")
plt.ylabel("Value")
plt.tight_layout()

out = RPT / "benchmark_comparison.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved -> {out}  ({out.stat().st_size // 1024} KB)")

# ── Stats ─────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  PERFORMANCE COMPARISON")
print("=" * 60)
nifty_aligned = nifty50[nifty50["date"] >= top_nav["date"].min()].sort_values("date")
top5_ret  = (top_nav["nav"].iloc[-1]               / top_nav["nav"].iloc[0]               - 1) * 100
nifty_ret = (nifty_aligned["close_value"].iloc[-1] / nifty_aligned["close_value"].iloc[0] - 1) * 100
outperf   = top5_ret - nifty_ret

print(f"  Top 5 Funds avg return : {top5_ret:+.2f}%")
print(f"  NIFTY 50 return        : {nifty_ret:+.2f}%")
print(f"  Outperformance         : {outperf:+.2f}%")
print()
print("  Top 5 schemes in the plot:")
for _, r in scorecard.head(5).iterrows():
    print(f"    {r['scheme_name'][:58]}")
