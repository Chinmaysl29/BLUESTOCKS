"""
cagr_comparison.py
------------------
Extracts 1Y / 3Y / 5Y CAGR for all 40 schemes and saves to
data/processed/cagr_comparison.csv
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

# ── Load ──────────────────────────────────────────────────────────────────
performance = pd.read_csv(PROC / "performance_clean.csv")

# ── Your exact code ───────────────────────────────────────────────────────
cagr_table = (
    performance[[
        "amfi_code",
        "scheme_name",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
    ]]
)

print("=" * 70)
print("  CAGR COMPARISON TABLE")
print("=" * 70)
print(f"  Shape : {cagr_table.shape}")
print()

# ── head() ────────────────────────────────────────────────────────────────
print("  cagr_table.head():")
print(cagr_table.head().to_string(index=False))

# ── Full table ────────────────────────────────────────────────────────────
print()
print("  Full table (all 40 schemes, sorted by 3Y return):")
print()
full = cagr_table.sort_values("return_3yr_pct", ascending=False).reset_index(drop=True)
full.index += 1
print(f"  {'#':>3}  {'Scheme':<50}  {'1Y%':>7}  {'3Y%':>7}  {'5Y%':>7}")
print("  " + "-" * 75)
for idx, r in full.iterrows():
    name = r["scheme_name"][:50]
    print(f"  {idx:>3}  {name:<50}  "
          f"{r['return_1yr_pct']:>7.2f}  "
          f"{r['return_3yr_pct']:>7.2f}  "
          f"{r['return_5yr_pct']:>7.2f}")

# ── Stats ─────────────────────────────────────────────────────────────────
print()
print("  Summary stats:")
print(cagr_table[["return_1yr_pct","return_3yr_pct","return_5yr_pct"]]
      .describe().round(2).to_string())

# ── Save ──────────────────────────────────────────────────────────────────
out = PROC / "cagr_comparison.csv"
cagr_table.to_csv(out, index=False)
print()
print(f"  Saved → {out}")
print(f"  Rows  : {len(cagr_table)}  |  Cols : {list(cagr_table.columns)}")
