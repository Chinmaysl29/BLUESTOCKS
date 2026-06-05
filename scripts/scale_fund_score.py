"""
scale_fund_score.py
--------------------
Bluestock Fintech Capstone

Executes your exact code:

    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 100))
    performance["fund_score"] = scaler.fit_transform(performance[["fund_score"]])

IMPORTANT — direction note:
    Raw fund_score was LOWER = BETTER (ordinal rank sum).
    After MinMaxScaler:  0  = worst raw score (best fund)
                        100 = best  raw score (worst fund)

    To make intuitive (100 = best), we invert:
        performance["fund_score_scaled"] = 100 - scaled_value

Both the raw-scaled and inverted columns are saved.

Output:
    data/processed/fund_score_scaled.csv
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

# ── Load ──────────────────────────────────────────────────────────────────
performance = pd.read_csv(PROC / "fund_score.csv")
print(f"Loaded fund_score.csv  →  {performance.shape}")
print(f"fund_score range BEFORE scaling:  "
      f"min={performance['fund_score'].min():.2f}  "
      f"max={performance['fund_score'].max():.2f}")
print()

# Store original for comparison
performance["fund_score_raw"] = performance["fund_score"].copy()

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE
# ═════════════════════════════════════════════════════════════════════════

from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(0, 100))
performance["fund_score"] = (
    scaler.fit_transform(performance[["fund_score"]])
)

# ═════════════════════════════════════════════════════════════════════════

print(f"fund_score range AFTER  scaling:  "
      f"min={performance['fund_score'].min():.2f}  "
      f"max={performance['fund_score'].max():.2f}")
print()

# Inverted score: 100 = best fund, 0 = worst fund (intuitive direction)
performance["fund_score_100"] = (100 - performance["fund_score"]).round(4)
performance["fund_score"]     = performance["fund_score"].round(4)

# Re-rank on inverted score (rank 1 = highest fund_score_100 = best)
performance["fund_rank"] = (
    performance["fund_score_100"].rank(ascending=False).astype(int)
)
ranked = performance.sort_values("fund_rank").reset_index(drop=True)
ranked.index += 1

# ── Print full table ──────────────────────────────────────────────────────
sep = "=" * 105
print(sep)
print("  FUND SCORE — MinMaxScaler(0, 100) APPLIED")
print("  fund_score      : 0 = raw min (best rank sum)  →  100 = raw max (worst rank sum)")
print("  fund_score_100  : INVERTED — 100 = best fund   →    0 = worst fund  ← use this")
print(sep)
print(f"  {'Rank':>4}  {'Scheme':<48}  {'Cat':<10}  "
      f"{'RawScore':>9}  {'Scaled(0-100)':>13}  {'Score100':>9}")
print("  " + "-" * 100)

for _, r in ranked.iterrows():
    print(
        f"  {r['fund_rank']:>4}  {r['scheme_name'][:48]:<48}  "
        f"{r['category']:<10}  "
        f"{r['fund_score_raw']:>9.2f}  "
        f"{r['fund_score']:>13.4f}  "
        f"{r['fund_score_100']:>9.4f}"
    )

# ── Verify scaler behaviour ───────────────────────────────────────────────
print()
print(sep)
print("  SCALER VERIFICATION")
print(sep)
print(f"  Original min  : {performance['fund_score_raw'].min():.4f}  →  scaled = {performance['fund_score'].min():.4f}")
print(f"  Original max  : {performance['fund_score_raw'].max():.4f}  →  scaled = {performance['fund_score'].max():.4f}")
print(f"  Formula check : (raw - min) / (max - min) × 100")
raw_min = performance["fund_score_raw"].min()
raw_max = performance["fund_score_raw"].max()
sample  = performance.loc[0, "fund_score_raw"]
manual  = (sample - raw_min) / (raw_max - raw_min) * 100
print(f"  Sample row[0] : ({sample:.4f} - {raw_min:.4f}) / ({raw_max:.4f} - {raw_min:.4f}) × 100 = {manual:.4f}")
print(f"  Scaler output : {performance.loc[0,'fund_score']:.4f}  ✅" if abs(manual - performance.loc[0,'fund_score']) < 0.001 else "  MISMATCH ⚠️")

# ── Stats ─────────────────────────────────────────────────────────────────
print()
print(sep)
print("  fund_score_100 STATISTICS  (100 = best, 0 = worst)")
print(sep)
desc = ranked["fund_score_100"].describe()
print(f"  count   {desc['count']:.0f}")
print(f"  mean    {desc['mean']:.2f}")
print(f"  std     {desc['std']:.2f}")
print(f"  min     {desc['min']:.2f}   ←  {ranked.iloc[-1]['scheme_name'][:50]}  (worst)")
print(f"  max     {desc['max']:.2f}   ←  {ranked.iloc[0]['scheme_name'][:50]}   (best)")
print()
print("  Category averages (fund_score_100, higher = better):")
cat_avg = ranked.groupby("category")["fund_score_100"].mean().sort_values(ascending=False)
for cat, val in cat_avg.items():
    bar = "█" * int(val / 5)
    print(f"    {cat:<22}  {val:>6.2f}  {bar}")

# ── Save ──────────────────────────────────────────────────────────────────
out_cols = [
    "amfi_code", "scheme_name", "fund_house", "category", "plan",
    "return_3yr_pct", "sharpe_ratio", "alpha", "expense_ratio_pct", "max_drawdown_pct",
    "return_rank", "sharpe_rank", "alpha_rank", "expense_rank", "dd_rank",
    "fund_score_raw", "fund_score", "fund_score_100", "fund_rank",
]
ranked[out_cols].to_csv(PROC / "fund_score_scaled.csv", index=False)
print()
print(f"  Saved → data/processed/fund_score_scaled.csv  "
      f"({len(ranked)} rows × {len(out_cols)} cols)")
print(sep)
