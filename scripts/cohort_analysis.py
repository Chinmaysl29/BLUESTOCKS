"""
cohort_analysis.py
------------------
Executes your exact code:

    tx = pd.read_csv("data/processed/transactions_clean.csv")
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
    first_year  = tx.groupby("investor_id")["transaction_date"].min().dt.year
    tx["cohort_year"] = tx["investor_id"].map(first_year)

Then computes per cohort:
    - Average SIP Amount
    - Total Invested
    - Favorite Fund

Output: data/processed/cohort_analysis.csv
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

# ═══════════════════════════════════════════════════════════
# YOUR EXACT CODE — line by line
# ═══════════════════════════════════════════════════════════

# Line 1
tx = pd.read_csv(PROC / "transactions_clean.csv")
print("Line 1  tx = pd.read_csv('data/processed/transactions_clean.csv')")
print(f"        Shape : {tx.shape}")
print()

# Line 2
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
print("Line 2  tx['transaction_date'] = pd.to_datetime(tx['transaction_date'])")
print(f"        dtype : {tx['transaction_date'].dtype}")
print()

# Line 3
first_year = tx.groupby("investor_id")["transaction_date"].min().dt.year
print("Line 3  first_year = tx.groupby('investor_id')['transaction_date'].min().dt.year")
print(f"        Unique cohort years : {sorted(first_year.unique())}")
print(f"        Total investors     : {len(first_year):,}")
print()

# Line 4
tx["cohort_year"] = tx["investor_id"].map(first_year)
print("Line 4  tx['cohort_year'] = tx['investor_id'].map(first_year)")
print(f"        Cohort distribution :")
print(tx["cohort_year"].value_counts().sort_index().to_string())
print()

# ═══════════════════════════════════════════════════════════
# COHORT METRICS
# ═══════════════════════════════════════════════════════════

# ── Metric 1: Average SIP Amount per cohort ───────────────
sip_tx   = tx[tx["transaction_type"] == "SIP"]
avg_sip  = (sip_tx.groupby("cohort_year")["amount_inr"]
                   .mean()
                   .round(2)
                   .rename("avg_sip_amount"))

# ── Metric 2: Total Invested per cohort ───────────────────
total_inv = (tx.groupby("cohort_year")["amount_inr"]
               .sum()
               .round(2)
               .rename("total_invested"))

# ── Metric 3: Favourite Fund per cohort ──────────────────
fav_fund = (tx.groupby(["cohort_year", "scheme_name"])["amount_inr"]
              .sum()
              .reset_index()
              .sort_values("amount_inr", ascending=False)
              .groupby("cohort_year")
              .first()["scheme_name"]
              .rename("favorite_fund"))

# ── Additional metrics ────────────────────────────────────
investor_count = (tx.groupby("cohort_year")["investor_id"]
                    .nunique()
                    .rename("unique_investors"))

sip_count = (sip_tx.groupby("cohort_year").size()
                   .rename("sip_transactions"))

txn_count = (tx.groupby("cohort_year").size()
               .rename("total_transactions"))

avg_investment = (tx.groupby("cohort_year")["amount_inr"]
                    .mean()
                    .round(2)
                    .rename("avg_investment"))

# ── Combine ───────────────────────────────────────────────
cohort = pd.concat([
    investor_count,
    txn_count,
    sip_count,
    total_inv,
    avg_sip,
    avg_investment,
    fav_fund,
], axis=1).reset_index()

cohort["total_invested_cr"]  = (cohort["total_invested"] / 1e7).round(2)
cohort["avg_sip_formatted"]  = cohort["avg_sip_amount"].apply(lambda x: f"Rs {x:,.0f}")
cohort["total_inv_formatted"]= cohort["total_invested_cr"].apply(lambda x: f"Rs {x:.1f} Cr")

# ── Print full cohort table ───────────────────────────────
sep = "=" * 95
print(sep)
print("  INVESTOR COHORT ANALYSIS  (grouped by first transaction year)")
print(sep)
print(f"\n  {'Cohort':>8}  {'Investors':>10}  {'Transactions':>13}  "
      f"{'Total Invested':>15}  {'Avg SIP':>10}  {'Avg Invest':>11}")
print("  " + "-" * 75)
for _, r in cohort.iterrows():
    print(f"  {int(r['cohort_year']):>8}  "
          f"{int(r['unique_investors']):>10,}  "
          f"{int(r['total_transactions']):>13,}  "
          f"{r['total_inv_formatted']:>15}  "
          f"{r['avg_sip_formatted']:>10}  "
          f"Rs {r['avg_investment']:>8,.0f}")

print()
print(sep)
print("  FAVOURITE FUND BY COHORT  (highest total investment volume)")
print(sep)
for _, r in cohort.iterrows():
    print(f"  {int(r['cohort_year'])}  {r['favorite_fund'][:65]}")

print()
print(sep)
print("  DETAILED METRICS TABLE")
print(sep)
print(f"\n  {'Cohort':>8}  {'Avg SIP (Rs)':>14}  {'Total Invested (Rs)':>20}  {'Favourite Fund':<50}")
print("  " + "-" * 95)
for _, r in cohort.iterrows():
    print(f"  {int(r['cohort_year']):>8}  "
          f"{r['avg_sip_amount']:>14,.2f}  "
          f"{r['total_invested']:>20,.2f}  "
          f"{r['favorite_fund'][:50]:<50}")

# ── Charts ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(17, 5))

# Chart 1: Total Invested by Cohort
axes[0].bar(cohort["cohort_year"].astype(str),
            cohort["total_invested_cr"],
            color=["steelblue","darkorange","seagreen","crimson"][:len(cohort)],
            edgecolor="white")
axes[0].set_title("Total Invested by Cohort (Rs Crore)", fontweight="bold")
axes[0].set_xlabel("Cohort Year")
axes[0].set_ylabel("Rs Crore")

# Chart 2: Average SIP Amount by Cohort
axes[1].bar(cohort["cohort_year"].astype(str),
            cohort["avg_sip_amount"],
            color=["steelblue","darkorange","seagreen","crimson"][:len(cohort)],
            edgecolor="white")
axes[1].set_title("Avg SIP Amount by Cohort (Rs)", fontweight="bold")
axes[1].set_xlabel("Cohort Year")
axes[1].set_ylabel("Rs")
axes[1].yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f"Rs {x:,.0f}"))

# Chart 3: Unique Investors by Cohort
axes[2].bar(cohort["cohort_year"].astype(str),
            cohort["unique_investors"],
            color=["steelblue","darkorange","seagreen","crimson"][:len(cohort)],
            edgecolor="white")
axes[2].set_title("Unique Investors by Cohort", fontweight="bold")
axes[2].set_xlabel("Cohort Year")
axes[2].set_ylabel("Count")

plt.suptitle("Investor Cohort Analysis (by First Transaction Year)",
             fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()

chart_out = RPT / "cohort_analysis.png"
plt.savefig(chart_out, dpi=150, bbox_inches="tight")
plt.close()

# ── Save CSV ──────────────────────────────────────────────
out_csv = PROC / "cohort_analysis.csv"
cohort.to_csv(out_csv, index=False)

print()
print(f"  Chart saved -> reports/cohort_analysis.png")
print(f"  CSV   saved -> data/processed/cohort_analysis.csv")
print(f"  Shape : {cohort.shape}  |  Cols : {list(cohort.columns)}")
print(sep)
