"""
top5_nav_benchmark.py
---------------------
Bluestock Fintech Capstone

Executes your exact code line by line:

    benchmark["date"] = pd.to_datetime(benchmark["date"])
    nav["date"]       = pd.to_datetime(nav["date"])
    top5              = scorecard.head(5)["amfi_code"]
    top_nav           = nav[nav["amfi_code"].isin(top5)] \
                            .groupby("date")["nav"].mean().reset_index()

Then plots top5 average NAV vs NIFTY50 benchmark (normalised to 100).

Outputs:
    data/processed/top5_nav.csv
    data/processed/top5_schemes.csv
    reports/top5_vs_benchmark.png
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

# ── Load ──────────────────────────────────────────────────────────────────
benchmark = pd.read_csv(RAW  / "10_benchmark_indices.csv")
nav       = pd.read_csv(PROC / "nav_history_clean.csv")
scorecard = pd.read_csv(PROC / "fund_scorecard.csv")

print("Datasets loaded:")
print(f"  benchmark : {benchmark.shape}")
print(f"  nav       : {nav.shape}")
print(f"  scorecard : {scorecard.shape}")
print()

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE — line by line
# ═════════════════════════════════════════════════════════════════════════

# Line 1
benchmark["date"] = pd.to_datetime(benchmark["date"])
print("Line 1  benchmark['date'] = pd.to_datetime(benchmark['date'])")
print(f"        dtype = {benchmark['date'].dtype}  ✅")
print()

# Line 2
nav["date"] = pd.to_datetime(nav["date"])
print("Line 2  nav['date'] = pd.to_datetime(nav['date'])")
print(f"        dtype = {nav['date'].dtype}  ✅")
print()

# Line 3
top5 = scorecard.head(5)["amfi_code"]
print("Line 3  top5 = scorecard.head(5)['amfi_code']")
print(f"        Values: {top5.values}")
top5_names = scorecard.head(5)[["amfi_code","scheme_name","fund_score_100"]]
print(f"\n        Top 5 schemes:")
print(top5_names.to_string(index=False))
print()

# Line 4
top_nav = (
    nav[nav["amfi_code"].isin(top5)]
    .groupby("date")["nav"]
    .mean()
    .reset_index()
)
print("Line 4  top_nav = nav[nav['amfi_code'].isin(top5)].groupby('date')['nav'].mean().reset_index()")
print(f"        Shape  : {top_nav.shape}")
print(f"        Columns: {list(top_nav.columns)}")
print(f"        Date range: {top_nav['date'].min().date()} → {top_nav['date'].max().date()}")
print(f"        NAV range : {top_nav['nav'].min():.2f} → {top_nav['nav'].max():.2f}")
print()
print("        Sample (head 5):")
print(top_nav.head().to_string(index=False))
print()
print("        Sample (tail 5):")
print(top_nav.tail().to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════
# EXTENDED — individual scheme NAV lines + benchmark
# ═════════════════════════════════════════════════════════════════════════

# Get NIFTY50 series
nifty = benchmark[benchmark["index_name"] == "NIFTY50"][["date","close_value"]].copy()
nifty = nifty.sort_values("date")

# Normalise both to 100 at start date
start_date = top_nav["date"].min()

# top_nav normalised
tn_norm = top_nav.copy()
start_val = tn_norm.loc[tn_norm["date"] == tn_norm["date"].min(), "nav"].values[0]
tn_norm["nav_indexed"] = tn_norm["nav"] / start_val * 100

# NIFTY50 normalised from same start date
nf_norm = nifty[nifty["date"] >= start_date].copy()
start_nifty = nf_norm.iloc[0]["close_value"]
nf_norm["nifty_indexed"] = nf_norm["close_value"] / start_nifty * 100

# Individual scheme NAV series (normalised)
top5_detail = nav[nav["amfi_code"].isin(top5)].copy()
top5_detail = top5_detail.sort_values(["amfi_code","date"])

# ── Plot ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 11))

# Panel 1: Top5 average vs NIFTY50
ax1 = axes[0]
ax1.plot(tn_norm["date"], tn_norm["nav_indexed"],
         color="steelblue", linewidth=2.5, label="Top 5 Avg NAV (indexed)")
ax1.plot(nf_norm["date"], nf_norm["nifty_indexed"],
         color="darkorange", linewidth=1.8, linestyle="--", label="NIFTY50 (indexed)")
ax1.axhline(100, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
ax1.fill_between(tn_norm["date"], tn_norm["nav_indexed"],
                 nf_norm.set_index("date")["nifty_indexed"].reindex(tn_norm["date"]).values,
                 alpha=0.07, color="steelblue")
ax1.set_title("Top 5 Funds — Average NAV vs NIFTY50 (Base = 100 at start)",
              fontsize=12, fontweight="bold")
ax1.set_ylabel("Indexed Value")
ax1.legend()

# Panel 2: Individual scheme lines (normalised)
ax2 = axes[1]
colors = ["#2ecc71","#3498db","#e74c3c","#9b59b6","#f39c12"]
for (code, grp), color in zip(top5_detail.groupby("amfi_code"), colors):
    grp = grp.sort_values("date")
    s   = grp["nav"].iloc[0]
    ax2.plot(grp["date"], grp["nav"] / s * 100,
             label=grp["scheme_name"].iloc[0].split(" - ")[0][:35],
             color=color, linewidth=1.5)

ax2.plot(nf_norm["date"], nf_norm["nifty_indexed"],
         color="black", linewidth=1.2, linestyle="--", label="NIFTY50", alpha=0.6)
ax2.axhline(100, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
ax2.set_title("Top 5 Funds — Individual NAV Performance (Base = 100)",
              fontsize=12, fontweight="bold")
ax2.set_ylabel("Indexed Value")
ax2.set_xlabel("Date")
ax2.legend(fontsize=8)

plt.tight_layout()
out_png = RPT / "top5_vs_benchmark.png"
plt.savefig(out_png, dpi=150, bbox_inches="tight")
plt.close()
print(f"Chart saved → {out_png}")

# ── Save CSVs ─────────────────────────────────────────────────────────────
top_nav.to_csv(PROC / "top5_nav.csv", index=False)
top5_names.to_csv(PROC / "top5_schemes.csv", index=False)

print(f"Data  saved → data/processed/top5_nav.csv       ({len(top_nav)} rows)")
print(f"Data  saved → data/processed/top5_schemes.csv   ({len(top5_names)} rows)")
print()

# ── Final summary ─────────────────────────────────────────────────────────
print("=" * 65)
print("  SUMMARY")
print("=" * 65)
total_return = ((top_nav["nav"].iloc[-1] / top_nav["nav"].iloc[0]) - 1) * 100
nifty_return = ((nf_norm["nifty_indexed"].iloc[-1] / 100) - 1) * 100
print(f"  Top 5 avg NAV total return  : {total_return:.2f}%")
print(f"  NIFTY50 total return        : {nifty_return:.2f}%")
print(f"  Outperformance              : {total_return - nifty_return:+.2f}%")
print()
print("  Top 5 schemes:")
for _, r in top5_names.iterrows():
    print(f"    AMFI {int(r['amfi_code'])}  {r['scheme_name'][:55]}  score={r['fund_score_100']:.2f}")
