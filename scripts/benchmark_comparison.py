"""
benchmark_comparison.py
------------------------
Bluestock Fintech Capstone

Executes your exact code line by line:

    nifty50 = benchmark[benchmark["index_name"].str.replace(" ", "").str.upper() == "NIFTY50"]
    plt.figure(figsize=(12, 6))
    plt.plot(top_nav["date"],       top_nav["nav"],          label="Top 5 Funds")
    plt.plot(nifty50["date"],       nifty50["close_value"],  label="NIFTY 50")
    plt.legend()
    plt.title("Top Funds vs NIFTY 50")
    plt.show()
    plt.savefig("reports/benchmark_comparison.png")

Output:
    reports/benchmark_comparison.png
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive - safe for script execution
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
RAW  = BASE / "data" / "raw"
RPT  = BASE / "reports"

# ── Load dependencies ─────────────────────────────────────────────────────
benchmark = pd.read_csv(RAW  / "10_benchmark_indices.csv")
top_nav   = pd.read_csv(PROC / "top5_nav.csv")
scorecard = pd.read_csv(PROC / "fund_scorecard.csv")

benchmark["date"] = pd.to_datetime(benchmark["date"])
top_nav["date"]   = pd.to_datetime(top_nav["date"])

print("Loaded:")
print(f"  benchmark : {benchmark.shape}")
print(f"  top_nav   : {top_nav.shape}")
print()

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE - line by line
# ═════════════════════════════════════════════════════════════════════════

# Line 1 - filter NIFTY 50 from benchmark
nifty50 = benchmark[
    benchmark["index_name"].str.replace(" ", "", regex=False).str.upper() == "NIFTY50"
]
print("Line 1  nifty50 = benchmark[benchmark['index_name'].str.replace(' ', '').str.upper() == 'NIFTY50']")
print(f"        Unique index_name values matched : {nifty50['index_name'].unique()}")
print(f"        Shape  : {nifty50.shape}")
if nifty50.empty:
    raise ValueError("No benchmark rows matched NIFTY50 after normalizing index_name")
print(f"        Date range : {nifty50['date'].min().date()} -> {nifty50['date'].max().date()}")
print(f"        Close range: {nifty50['close_value'].min():.2f} -> {nifty50['close_value'].max():.2f}")
print()

# Line 2
plt.figure(figsize=(12, 6))
print("Line 2  plt.figure(figsize=(12, 6))  OK")

# Line 3 - plot Top 5 avg NAV
plt.plot(top_nav["date"], top_nav["nav"], label="Top 5 Funds",
         color="steelblue", linewidth=2)
print("Line 3  plt.plot(top_nav['date'], top_nav['nav'], label='Top 5 Funds')  OK")

# Line 4 - plot NIFTY 50
plt.plot(nifty50["date"], nifty50["close_value"], label="NIFTY 50",
         color="darkorange", linewidth=1.8, linestyle="--")
print("Line 4  plt.plot(nifty50['date'], nifty50['close_value'], label='NIFTY 50')  OK")

# Line 5
plt.legend()
print("Line 5  plt.legend()  OK")

# Line 6
plt.title("Top Funds vs NIFTY 50")
print("Line 6  plt.title('Top Funds vs NIFTY 50')  OK")

# Axis labels for clarity
plt.xlabel("Date")
plt.ylabel("Value")
plt.tight_layout()

# Line 7 - plt.show() - skipped in script (non-interactive), savefig handles output
print("Line 7  plt.show()  - skipped (non-interactive mode, savefig used instead)")

# Line 8 - save
out = "reports/benchmark_comparison.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Line 8  plt.savefig('{out}')  OK")
print()

# ── Verify file ───────────────────────────────────────────────────────────
out_path = BASE / out
size_kb  = out_path.stat().st_size // 1024
print(f"Saved  -> {out_path}")
print(f"Size   -> {size_kb} KB")
print()

# ── Data summary ──────────────────────────────────────────────────────────
print("=" * 60)
print("  PLOT DATA SUMMARY")
print("=" * 60)
print(f"  top_nav  rows  : {len(top_nav)}")
print(f"  nifty50  rows  : {len(nifty50)}")
print()
print(f"  Top 5 Funds - start NAV  : {top_nav['nav'].iloc[0]:.2f}")
print(f"  Top 5 Funds - end   NAV  : {top_nav['nav'].iloc[-1]:.2f}")
print(f"  Top 5 return             : {((top_nav['nav'].iloc[-1]/top_nav['nav'].iloc[0])-1)*100:.2f}%")
print()
nifty_s = nifty50[nifty50["date"] >= top_nav["date"].min()].sort_values("date")
print(f"  NIFTY 50 - start close   : {nifty_s['close_value'].iloc[0]:.2f}")
print(f"  NIFTY 50 - end   close   : {nifty_s['close_value'].iloc[-1]:.2f}")
print(f"  NIFTY 50 return          : {((nifty_s['close_value'].iloc[-1]/nifty_s['close_value'].iloc[0])-1)*100:.2f}%")
print()
print("  Top 5 schemes plotted:")
top5_names = scorecard.head(5)[["amfi_code","scheme_name","fund_score_100"]]
for _, r in top5_names.iterrows():
    print(f"    {r['scheme_name'][:55]}")
