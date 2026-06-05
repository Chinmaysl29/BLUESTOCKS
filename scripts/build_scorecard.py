"""
build_scorecard.py
------------------
Bluestock Fintech Capstone

Executes your exact code:

    scorecard = performance.sort_values("fund_score", ascending=False)

fund_score here is the MinMaxScaler(0,100) output where:
    100 = best raw rank sum (worst fund)  ← raw scaled direction
    BUT we use fund_score_100 (inverted) so:
    ascending=False → highest fund_score_100 first = BEST FUND FIRST

Saves:
    data/processed/scorecard.csv
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

# ── Load fund_score_scaled (has fund_score_100 = inverted, 100=best) ──────
performance = pd.read_csv(PROC / "fund_score_scaled.csv")
print(f"Loaded fund_score_scaled.csv  →  {performance.shape}")
print(f"Columns: {list(performance.columns)}\n")

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE
# ═════════════════════════════════════════════════════════════════════════

scorecard = (
    performance.sort_values("fund_score_100", ascending=False)
)

# ═════════════════════════════════════════════════════════════════════════

scorecard = scorecard.reset_index(drop=True)
scorecard.index += 1

# ── Print full scorecard ──────────────────────────────────────────────────
sep = "=" * 115
print(sep)
print("  FUND SCORECARD  —  sorted by fund_score  (ascending=False → Best fund first)")
print("  fund_score_100 : 100 = Best  |  0 = Worst")
print(sep)
print(f"  {'Rank':>4}  {'Scheme':<50}  {'Category':<12}  {'Plan':<8}  "
      f"{'3YRet%':>7}  {'Sharpe':>7}  {'Alpha':>6}  "
      f"{'Exp%':>5}  {'MDD%':>7}  {'Score':>8}")
print("  " + "-" * 115)

for idx, r in scorecard.iterrows():
    name = r["scheme_name"][:50]
    print(
        f"  {idx:>4}  {name:<50}  {r['category']:<12}  {r['plan']:<8}  "
        f"{r['return_3yr_pct']:>7.2f}  {r['sharpe_ratio']:>7.3f}  "
        f"{r['alpha']:>6.2f}  {r['expense_ratio_pct']:>5.2f}  "
        f"{r['max_drawdown_pct']:>7.2f}  {r['fund_score_100']:>8.4f}"
    )

# ── Summary ───────────────────────────────────────────────────────────────
print()
print(sep)
print("  TOP 5  (Best funds)")
print(sep)
for _, r in scorecard.head(5).iterrows():
    print(f"  #{int(_):>2}  {r['scheme_name'][:55]:<55}  "
          f"Score={r['fund_score_100']:>7.2f}  "
          f"3Y={r['return_3yr_pct']:.2f}%  "
          f"Sharpe={r['sharpe_ratio']:.3f}  "
          f"Alpha={r['alpha']:.2f}")

print()
print(sep)
print("  BOTTOM 5  (Weakest funds)")
print(sep)
for _, r in scorecard.tail(5).iterrows():
    print(f"  #{int(_):>2}  {r['scheme_name'][:55]:<55}  "
          f"Score={r['fund_score_100']:>7.2f}  "
          f"3Y={r['return_3yr_pct']:.2f}%  "
          f"Sharpe={r['sharpe_ratio']:.3f}  "
          f"Alpha={r['alpha']:.2f}")

# ── Category summary ──────────────────────────────────────────────────────
print()
print(sep)
print("  CATEGORY SCORECARD SUMMARY")
print(sep)
print(f"  {'Category':<22}  {'Count':>5}  {'AvgScore':>9}  "
      f"{'Best':>7}  {'Worst':>7}  {'Avg3Y%':>7}  {'AvgSharpe':>10}")
print("  " + "-" * 80)
cat = scorecard.groupby("category").agg(
    count      = ("fund_score_100", "count"),
    avg_score  = ("fund_score_100", "mean"),
    best_score = ("fund_score_100", "max"),
    worst_score= ("fund_score_100", "min"),
    avg_return = ("return_3yr_pct",  "mean"),
    avg_sharpe = ("sharpe_ratio",    "mean"),
).sort_values("avg_score", ascending=False)

for cat_name, row in cat.iterrows():
    bar = "█" * int(row["avg_score"] / 7)
    print(f"  {cat_name:<22}  {int(row['count']):>5}  "
          f"{row['avg_score']:>9.2f}  "
          f"{row['best_score']:>7.2f}  "
          f"{row['worst_score']:>7.2f}  "
          f"{row['avg_return']:>7.2f}  "
          f"{row['avg_sharpe']:>10.3f}  {bar}")

# ── Save ──────────────────────────────────────────────────────────────────
scorecard.to_csv(PROC / "scorecard.csv", index=False)
print()
print(f"  Saved → data/processed/scorecard.csv  "
      f"({len(scorecard)} rows × {scorecard.shape[1]} cols)")
print(sep)
