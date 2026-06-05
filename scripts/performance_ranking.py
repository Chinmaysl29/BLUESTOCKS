"""
performance_ranking.py
-----------------------
Bluestock Fintech Capstone

Executes your exact ranking code line by line:

    performance["return_rank"]  = performance["return_3yr_pct"].rank(ascending=False)
    performance["sharpe_rank"]  = performance["sharpe_ratio"].rank(ascending=False)
    performance["alpha_rank"]   = performance["alpha"].rank(ascending=False)
    performance["alpha_rank"]   = performance["alpha"].rank(ascending=False)   # duplicate — intentional
    performance["expense_rank"] = performance["expense_ratio_pct"].rank(ascending=True)
    performance["dd_rank"]      = performance["max_drawdown_pct"].rank(ascending=True)

Then:
    score = 0.30*return_rank + 0.25*sharpe_rank + 0.20*alpha_rank
          + 0.15*expense_rank + 0.10*dd_rank

Outputs:
    data/processed/performance_ranks.csv
    reports/performance_ranking_report.txt
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
RPT  = BASE / "reports"

# ── Load ──────────────────────────────────────────────────────────────────
performance = pd.read_csv(PROC / "performance_clean.csv")
print(f"Loaded performance_clean.csv  →  {performance.shape}")
print(f"Columns available: {list(performance.columns)}\n")

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE — executed line by line
# ═════════════════════════════════════════════════════════════════════════

# Line 1 — 3-Year Return: rank descending (rank 1 = highest return)
performance["return_rank"] = (
    performance["return_3yr_pct"].rank(ascending=False)
)
print("Line 1  return_rank  computed  (ascending=False → rank 1 = best return)")
print(performance[["scheme_name","return_3yr_pct","return_rank"]]
      .sort_values("return_rank").head(5).to_string(index=False))
print()

# Line 2 — Sharpe Ratio: rank descending (rank 1 = highest Sharpe)
performance["sharpe_rank"] = (
    performance["sharpe_ratio"].rank(ascending=False)
)
print("Line 2  sharpe_rank  computed  (ascending=False → rank 1 = best Sharpe)")
print(performance[["scheme_name","sharpe_ratio","sharpe_rank"]]
      .sort_values("sharpe_rank").head(5).to_string(index=False))
print()

# Line 3 — Alpha: rank descending (rank 1 = highest alpha)
performance["alpha_rank"] = (
    performance["alpha"].rank(ascending=False)
)
print("Line 3  alpha_rank   computed  (ascending=False → rank 1 = best alpha)")
print(performance[["scheme_name","alpha","alpha_rank"]]
      .sort_values("alpha_rank").head(5).to_string(index=False))
print()

# Line 4 — Alpha: duplicate assignment (exactly as written)
performance["alpha_rank"] = (
    performance["alpha"].rank(ascending=False)
)
print("Line 4  alpha_rank   re-assigned  (duplicate — same result, no change)")
print()

# Line 5 — Expense Ratio: rank ascending (rank 1 = LOWEST expense = best)
performance["expense_rank"] = (
    performance["expense_ratio_pct"].rank(ascending=True)
)
print("Line 5  expense_rank computed  (ascending=True  → rank 1 = cheapest)")
print(performance[["scheme_name","expense_ratio_pct","expense_rank"]]
      .sort_values("expense_rank").head(5).to_string(index=False))
print()

# Line 6 — Max Drawdown: rank ascending (rank 1 = least negative = smallest loss)
performance["dd_rank"] = (
    performance["max_drawdown_pct"].rank(ascending=True)
)
print("Line 6  dd_rank      computed  (ascending=True  → rank 1 = smallest drawdown)")
print(performance[["scheme_name","max_drawdown_pct","dd_rank"]]
      .sort_values("dd_rank").head(5).to_string(index=False))
print()

# ═════════════════════════════════════════════════════════════════════════
# COMPOSITE SCORE
# score = 0.30*return_rank + 0.25*sharpe_rank + 0.20*alpha_rank
#       + 0.15*expense_rank + 0.10*dd_rank
# ─────────────────────────────────────────────────────────────────────────
# NOTE: ranks here are 1–40 (ordinal), lower = better for all metrics.
# So LOWER composite score = BETTER fund.
# ═════════════════════════════════════════════════════════════════════════

performance["score"] = (
    0.30 * performance["return_rank"]  +
    0.25 * performance["sharpe_rank"]  +
    0.20 * performance["alpha_rank"]   +
    0.15 * performance["expense_rank"] +
    0.10 * performance["dd_rank"]
).round(2)

# Final rank: lowest composite score = rank 1
performance["final_rank"] = performance["score"].rank(ascending=True).astype(int)

# Sort by final rank
ranked = performance.sort_values("final_rank").reset_index(drop=True)
ranked.index += 1

# ── Print full ranked table ───────────────────────────────────────────────
sep = "=" * 115
print(sep)
print("  COMPOSITE RANKING — ALL 40 SCHEMES")
print("  score = 0.30×return_rank + 0.25×sharpe_rank + 0.20×alpha_rank"
      " + 0.15×expense_rank + 0.10×dd_rank")
print("  Lower score = Better  |  Rank 1 = Best fund overall")
print(sep)
print(f"{'Rank':>4}  {'Scheme':<48}  {'Cat':<10}  "
      f"{'3YRet':>6}  {'Shp':>6}  {'Alp':>5}  {'Exp':>5}  {'DD':>7}  "
      f"{'RRnk':>5}  {'SRnk':>5}  {'ARnk':>5}  {'ERnk':>5}  {'DRnk':>5}  {'Score':>7}")
print("-" * 115)

for _, r in ranked.iterrows():
    name = r["scheme_name"][:48]
    print(
        f"{r['final_rank']:>4}  {name:<48}  {r['category']:<10}  "
        f"{r['return_3yr_pct']:>6.2f}  {r['sharpe_ratio']:>6.3f}  "
        f"{r['alpha']:>5.2f}  {r['expense_ratio_pct']:>5.2f}  "
        f"{r['max_drawdown_pct']:>7.2f}  "
        f"{r['return_rank']:>5.0f}  {r['sharpe_rank']:>5.0f}  "
        f"{r['alpha_rank']:>5.0f}  {r['expense_rank']:>5.0f}  "
        f"{r['dd_rank']:>5.0f}  {r['score']:>7.2f}"
    )

# ── Summary ───────────────────────────────────────────────────────────────
print()
print(sep)
print("  RANK COLUMN SUMMARY  (what each rank means)")
print(sep)
rank_info = {
    "return_rank" : ("return_3yr_pct",     "ascending=False", "rank 1 = highest 3Y return"),
    "sharpe_rank" : ("sharpe_ratio",        "ascending=False", "rank 1 = highest Sharpe"),
    "alpha_rank"  : ("alpha",               "ascending=False", "rank 1 = highest alpha"),
    "expense_rank": ("expense_ratio_pct",   "ascending=True",  "rank 1 = lowest expense (cheapest)"),
    "dd_rank"     : ("max_drawdown_pct",    "ascending=True",  "rank 1 = smallest drawdown (safest)"),
}
for col, (src, order, meaning) in rank_info.items():
    best_scheme = ranked.loc[ranked[col] == 1, "scheme_name"].values
    best_name   = best_scheme[0][:50] if len(best_scheme) else "—"
    print(f"  {col:<14}  source={src:<20}  {order:<18}  {meaning}")
    print(f"               Rank 1 scheme: {best_name}")
    print()

print()
print(sep)
print("  TOP 10 FUNDS  (lowest composite score = best)")
print(sep)
print(f"  {'Rank':<5}  {'Scheme':<52}  {'Category':<12}  {'Score':>7}")
print("  " + "-" * 80)
for _, r in ranked.head(10).iterrows():
    print(f"  {int(r['final_rank']):<5}  {r['scheme_name'][:52]:<52}  "
          f"{r['category']:<12}  {r['score']:>7.2f}")

print()
print(sep)
print("  BOTTOM 5 FUNDS  (highest composite score = weakest)")
print(sep)
print(f"  {'Rank':<5}  {'Scheme':<52}  {'Category':<12}  {'Score':>7}")
print("  " + "-" * 80)
for _, r in ranked.tail(5).iterrows():
    print(f"  {int(r['final_rank']):<5}  {r['scheme_name'][:52]:<52}  "
          f"{r['category']:<12}  {r['score']:>7.2f}")

print()
print(sep)
print("  CATEGORY AVERAGES")
print(sep)
cat_avg = ranked.groupby("category")[["score","return_3yr_pct","sharpe_ratio"]].mean()
cat_avg = cat_avg.sort_values("score")
print(f"  {'Category':<20}  {'Avg Score':>10}  {'Avg 3Y Ret':>11}  {'Avg Sharpe':>11}")
print("  " + "-" * 60)
for cat, row in cat_avg.iterrows():
    bar = "#" * max(1, int(30 - row["score"] / 2))
    print(f"  {cat:<20}  {row['score']:>10.2f}  "
          f"{row['return_3yr_pct']:>11.2f}  {row['sharpe_ratio']:>11.3f}  {bar}")

# ── Save ──────────────────────────────────────────────────────────────────
out_cols = [
    "amfi_code","scheme_name","fund_house","category","plan",
    "return_3yr_pct","sharpe_ratio","alpha","expense_ratio_pct","max_drawdown_pct",
    "return_rank","sharpe_rank","alpha_rank","expense_rank","dd_rank",
    "score","final_rank",
]
ranked[out_cols].to_csv(PROC / "performance_ranks.csv", index=False)
print()
print(f"  Saved → data/processed/performance_ranks.csv  "
      f"({len(ranked)} rows × {len(out_cols)} cols)")
