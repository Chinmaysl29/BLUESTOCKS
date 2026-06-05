"""
fund_score.py
-------------
Bluestock Fintech Capstone

Executes your exact code:

    performance["fund_score"] = (
        0.30 * performance["return_rank"]  +
        0.25 * performance["sharpe_rank"]  +
        0.20 * performance["alpha_rank"]   +
        0.15 * performance["expense_rank"] +
        0.10 * performance["dd_rank"]
    )

Weights:
    30% Return | 25% Sharpe | 20% Alpha | 15% Expense | 10% Max Drawdown

Output:
    data/processed/fund_score.csv
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

# ── Load performance with pre-computed ranks ──────────────────────────────
performance = pd.read_csv(PROC / "performance_ranks.csv")

print("Loaded performance_ranks.csv")
print(f"Shape  : {performance.shape}")
print(f"Columns: {list(performance.columns)}")
print()

# ── Verify all rank columns exist ─────────────────────────────────────────
required = ["return_rank", "sharpe_rank", "alpha_rank", "expense_rank", "dd_rank"]
missing  = [c for c in required if c not in performance.columns]
if missing:
    raise KeyError(f"Missing rank columns: {missing}. Run performance_ranking.py first.")

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE
# ═════════════════════════════════════════════════════════════════════════

performance["fund_score"] = (
    0.30 * performance["return_rank"]  +
    0.25 * performance["sharpe_rank"]  +
    0.20 * performance["alpha_rank"]   +
    0.15 * performance["expense_rank"] +
    0.10 * performance["dd_rank"]
)

# ═════════════════════════════════════════════════════════════════════════

# Final rank — lowest fund_score = Rank 1 (best)
performance["fund_rank"] = (
    performance["fund_score"].rank(ascending=True).astype(int)
)

ranked = performance.sort_values("fund_rank").reset_index(drop=True)
ranked.index += 1

# ── Print full results ────────────────────────────────────────────────────
sep = "=" * 110
print(sep)
print("  FUND SCORE  =  0.30×return_rank + 0.25×sharpe_rank + 0.20×alpha_rank")
print("               + 0.15×expense_rank + 0.10×dd_rank")
print("  Lower fund_score = Better fund  |  Rank 1 = Best")
print(sep)
print(f"  {'Rank':>4}  {'Scheme':<48}  {'Cat':<10}  "
      f"{'RRnk':>5}  {'SRnk':>5}  {'ARnk':>5}  "
      f"{'ERnk':>5}  {'DRnk':>5}  {'FundScore':>10}")
print("  " + "-" * 105)

for _, r in ranked.iterrows():
    name = r["scheme_name"][:48]
    # show weight contributions inline
    ret_c  = 0.30 * r["return_rank"]
    shp_c  = 0.25 * r["sharpe_rank"]
    alp_c  = 0.20 * r["alpha_rank"]
    exp_c  = 0.15 * r["expense_rank"]
    dd_c   = 0.10 * r["dd_rank"]
    print(f"  {r['fund_rank']:>4}  {name:<48}  {r['category']:<10}  "
          f"{r['return_rank']:>5.0f}  {r['sharpe_rank']:>5.0f}  "
          f"{r['alpha_rank']:>5.0f}  {r['expense_rank']:>5.0f}  "
          f"{r['dd_rank']:>5.0f}  {r['fund_score']:>10.2f}")

# ── Weight contribution table for top 10 ─────────────────────────────────
print()
print(sep)
print("  WEIGHT CONTRIBUTION BREAKDOWN — TOP 10")
print(sep)
print(f"  {'Rank':>4}  {'Scheme':<48}  "
      f"{'30%Ret':>7}  {'25%Shp':>7}  {'20%Alp':>7}  "
      f"{'15%Exp':>7}  {'10%DD':>7}  {'Total':>8}")
print("  " + "-" * 105)
for _, r in ranked.head(10).iterrows():
    print(f"  {r['fund_rank']:>4}  {r['scheme_name'][:48]:<48}  "
          f"{0.30*r['return_rank']:>7.2f}  "
          f"{0.25*r['sharpe_rank']:>7.2f}  "
          f"{0.20*r['alpha_rank']:>7.2f}  "
          f"{0.15*r['expense_rank']:>7.2f}  "
          f"{0.10*r['dd_rank']:>7.2f}  "
          f"{r['fund_score']:>8.2f}")

# ── Summary stats ─────────────────────────────────────────────────────────
print()
print(sep)
print("  fund_score STATISTICS")
print(sep)
desc = performance["fund_score"].describe()
print(f"  count   {desc['count']:.0f}")
print(f"  mean    {desc['mean']:.2f}")
print(f"  std     {desc['std']:.2f}")
print(f"  min     {desc['min']:.2f}   ←  {ranked.iloc[0]['scheme_name'][:55]}  (Rank 1)")
print(f"  25%     {desc['25%']:.2f}")
print(f"  50%     {desc['50%']:.2f}   (median)")
print(f"  75%     {desc['75%']:.2f}")
print(f"  max     {desc['max']:.2f}   ←  {ranked.iloc[-1]['scheme_name'][:55]}  (Rank 40)")

print()
print(sep)
print("  CATEGORY AVERAGE FUND_SCORE  (lower = better category)")
print(sep)
cat = ranked.groupby("category")["fund_score"].mean().sort_values()
for c, v in cat.items():
    bar = "█" * max(1, int(30 - v / 2))
    print(f"  {c:<22}  {v:>6.2f}  {bar}")

# ── Save ──────────────────────────────────────────────────────────────────
out_cols = [
    "amfi_code", "scheme_name", "fund_house", "category", "plan",
    "return_3yr_pct", "sharpe_ratio", "alpha", "expense_ratio_pct", "max_drawdown_pct",
    "return_rank", "sharpe_rank", "alpha_rank", "expense_rank", "dd_rank",
    "fund_score", "fund_rank",
]
ranked[out_cols].to_csv(PROC / "fund_score.csv", index=False)

print()
print(sep)
print(f"  Saved → data/processed/fund_score.csv  "
      f"({len(ranked)} rows × {len(out_cols)} cols)")
print(sep)
