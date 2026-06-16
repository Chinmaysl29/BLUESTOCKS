"""
churn_risk.py
-------------
Executes your exact code:

    tx = tx.sort_values(["investor_id", "transaction_date"])
    tx["gap_days"] = tx.groupby("investor_id")["transaction_date"].diff().dt.days

Then flags investors as at-risk if gap > 35 days.

Output:
    data/processed/churn_risk_report.csv
    reports/churn_risk_chart.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
RPT  = BASE / "reports"

sns.set_theme(style="whitegrid")

AT_RISK_THRESHOLD = 35   # days

# ── Load ──────────────────────────────────────────────────────────────────
tx = pd.read_csv(PROC / "transactions_clean.csv")
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
print(f"Loaded transactions : {tx.shape}")
print()

# ═══════════════════════════════════════════════════════════
# YOUR EXACT CODE — line by line
# ═══════════════════════════════════════════════════════════

# Line 1
tx = tx.sort_values(["investor_id", "transaction_date"])
print("Line 1  tx = tx.sort_values(['investor_id','transaction_date'])  ✅")

# Line 2
tx["gap_days"] = (
    tx.groupby("investor_id")["transaction_date"]
    .diff()
    .dt.days
)
print("Line 2  tx['gap_days'] = tx.groupby('investor_id')['transaction_date'].diff().dt.days  ✅")
print()
print(f"  Non-null gap_days : {tx['gap_days'].notna().sum():,}")
print(f"  NaN (first txn per investor): {tx['gap_days'].isna().sum():,}")
print()
print("  gap_days stats:")
print(tx["gap_days"].describe().round(2).to_string())
print()

# ═══════════════════════════════════════════════════════════
# AT-RISK FLAGGING  (gap > 35 days)
# ═══════════════════════════════════════════════════════════

# Flag each transaction row where gap > 35
tx["at_risk_gap"] = tx["gap_days"] > AT_RISK_THRESHOLD

# Per investor: max gap, at-risk status, last transaction date
investor_stats = (
    tx.groupby("investor_id")
    .agg(
        total_transactions   = ("transaction_date", "count"),
        first_txn            = ("transaction_date", "min"),
        last_txn             = ("transaction_date", "max"),
        max_gap_days         = ("gap_days",          "max"),
        avg_gap_days         = ("gap_days",          "mean"),
        at_risk_gap_count    = ("at_risk_gap",        "sum"),
        total_invested       = ("amount_inr",         "sum"),
        avg_sip_amount       = ("amount_inr",         "mean"),
    )
    .reset_index()
)

# At-risk = investor has had at least one gap > 35 days
investor_stats["is_at_risk"] = investor_stats["max_gap_days"] > AT_RISK_THRESHOLD

# Risk tier
def risk_tier(max_gap):
    if pd.isna(max_gap):    return "New"
    if max_gap <= 35:        return "Active"
    if max_gap <= 60:        return "At Risk"
    if max_gap <= 90:        return "High Risk"
    return "Churned"

investor_stats["risk_tier"] = investor_stats["max_gap_days"].apply(risk_tier)

# ── Summary ───────────────────────────────────────────────────────────────
total_inv     = len(investor_stats)
at_risk_count = investor_stats["is_at_risk"].sum()
active_count  = total_inv - at_risk_count

print("=" * 65)
print("  AT-RISK INVESTOR ANALYSIS  (gap > 35 days = at-risk)")
print("=" * 65)
print(f"  Total investors    : {total_inv:,}")
print(f"  Active (gap <= 35) : {active_count:,}  ({active_count/total_inv*100:.1f}%)")
print(f"  At-Risk (gap > 35) : {at_risk_count:,}  ({at_risk_count/total_inv*100:.1f}%)")
print()

# Risk tier breakdown
tier_counts = investor_stats["risk_tier"].value_counts()
print("  Risk Tier Breakdown:")
for tier, count in tier_counts.items():
    pct = count / total_inv * 100
    bar = "#" * int(pct / 2)
    print(f"    {tier:<12}  {count:>5,}  ({pct:>5.1f}%)  {bar}")

print()

# Gap distribution
print("  Gap Days Distribution:")
bins = [0, 7, 14, 30, 35, 60, 90, 180, 365, 9999]
labels = ["1-7d","8-14d","15-30d","31-35d","36-60d","61-90d","91-180d","181-365d","365d+"]
tx["gap_bucket"] = pd.cut(tx["gap_days"], bins=bins, labels=labels, right=True)
gap_dist = tx["gap_bucket"].value_counts().sort_index()
for bucket, count in gap_dist.items():
    flag = " ← AT RISK" if str(bucket) in ["36-60d","61-90d","91-180d","181-365d","365d+"] else ""
    print(f"    {str(bucket):<12}  {count:>6,}{flag}")

print()

# Top 10 at-risk investors
print("  Top 10 At-Risk Investors (highest max gap):")
top_risk = (investor_stats[investor_stats["is_at_risk"]]
            .sort_values("max_gap_days", ascending=False)
            .head(10)[["investor_id","max_gap_days","avg_gap_days",
                        "total_transactions","total_invested","risk_tier"]])
print(top_risk.to_string(index=False))

# ── Category breakdown of at-risk investors ───────────────────────────────
print()
print("  At-Risk Investors by Favourite Category:")
at_risk_ids = investor_stats[investor_stats["is_at_risk"]]["investor_id"]
at_risk_tx  = tx[tx["investor_id"].isin(at_risk_ids)]
cat_breakdown = at_risk_tx.groupby("category")["investor_id"].nunique().sort_values(ascending=False)
for cat, count in cat_breakdown.items():
    print(f"    {cat:<20}  {count:>5,} at-risk investors")

# ── Charts ────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(17, 5))

# Chart 1: Risk tier pie
tier_order = ["Active","At Risk","High Risk","Churned","New"]
tier_vals  = [tier_counts.get(t, 0) for t in tier_order]
colors     = ["seagreen","darkorange","crimson","darkred","steelblue"]
axes[0].pie([v for v in tier_vals if v > 0],
            labels=[t for t,v in zip(tier_order, tier_vals) if v > 0],
            autopct="%1.1f%%",
            colors=[c for c,v in zip(colors, tier_vals) if v > 0],
            startangle=90)
axes[0].set_title("Investor Risk Tier Distribution", fontweight="bold")

# Chart 2: Gap days histogram
gap_clean = tx["gap_days"].dropna()
axes[1].hist(gap_clean[gap_clean <= 120], bins=40,
             color="steelblue", edgecolor="white", alpha=0.8)
axes[1].axvline(AT_RISK_THRESHOLD, color="crimson", linestyle="--",
                linewidth=1.5, label=f"At-Risk threshold ({AT_RISK_THRESHOLD}d)")
axes[1].set_title("Transaction Gap Distribution (days)", fontweight="bold")
axes[1].set_xlabel("Gap Days")
axes[1].set_ylabel("Frequency")
axes[1].legend()

# Chart 3: At-risk investors by category
cat_breakdown.plot(kind="barh", ax=axes[2], color="darkorange", edgecolor="white")
axes[2].set_title("At-Risk Investors by Category", fontweight="bold")
axes[2].set_xlabel("Number of At-Risk Investors")

plt.suptitle("Investor Churn Risk Analysis (gap > 35 days = at-risk)",
             fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()

chart_out = RPT / "churn_risk_chart.png"
plt.savefig(chart_out, dpi=150, bbox_inches="tight")
plt.close()

# ── Save CSV ──────────────────────────────────────────────────────────────
out_csv = PROC / "churn_risk_report.csv"
investor_stats.to_csv(out_csv, index=False)

print()
print(f"  Chart saved -> reports/churn_risk_chart.png")
print(f"  CSV   saved -> data/processed/churn_risk_report.csv")
print(f"  Shape : {investor_stats.shape}")
print("=" * 65)
