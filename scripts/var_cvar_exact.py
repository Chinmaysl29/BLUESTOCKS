"""
var_cvar_exact.py
-----------------
Executes your exact code:

    cvar_95 = returns[returns <= var_95].mean()

    results = []
    for fund, df in nav.groupby("amfi_code"):
        returns = df["daily_return"].dropna()
        var95   = returns.quantile(0.05)
        cvar95  = returns[returns <= var95].mean()
        results.append([fund, var95, cvar95])

    var_cvar.to_csv("data/processed/var_cvar_report.csv", index=False)

Output: data/processed/var_cvar_report.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

# ── Load ──────────────────────────────────────────────────────────────────
nav = pd.read_csv(PROC / "nav_history_clean.csv")
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

print("nav loaded:", nav.shape)
print()

# ═════════════════════════════════════════════════════════════════════════
# YOUR EXACT CODE
# ═════════════════════════════════════════════════════════════════════════

results = []

for fund, df in nav.groupby("amfi_code"):
    returns = df["daily_return"].dropna()
    var95   = returns.quantile(0.05)
    cvar95  = (returns[returns <= var95].mean())
    results.append([fund, var95, cvar95])

# ═════════════════════════════════════════════════════════════════════════

var_cvar = pd.DataFrame(results, columns=["amfi_code", "var_95", "cvar_95"])

# Merge scheme name and category for context
meta = nav[["amfi_code","scheme_name","category","plan"]].drop_duplicates("amfi_code")
var_cvar = var_cvar.merge(meta, on="amfi_code", how="left")

# Convert to % for readability
var_cvar["var_95_pct"]  = (var_cvar["var_95"]  * 100).round(4)
var_cvar["cvar_95_pct"] = (var_cvar["cvar_95"] * 100).round(4)

# ── Print full results ────────────────────────────────────────────────────
print("=" * 85)
print("  VaR/CVaR @ 95% CONFIDENCE — ALL 40 SCHEMES")
print("  var95  = returns.quantile(0.05)")
print("  cvar95 = returns[returns <= var95].mean()  (Expected Shortfall)")
print("=" * 85)
print(f"  {'#':>3}  {'Scheme':<48}  {'VaR 95% (%)':>12}  {'CVaR 95% (%)':>13}")
print("  " + "-" * 80)

df_sorted = var_cvar.sort_values("var_95").reset_index(drop=True)
df_sorted.index += 1
for idx, r in df_sorted.iterrows():
    name = r["scheme_name"][:48]
    print(f"  {idx:>3}  {name:<48}  {r['var_95_pct']:>11.4f}%  {r['cvar_95_pct']:>12.4f}%")

# ── Stats ─────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  SUMMARY")
print("=" * 55)
print(f"  Total schemes  : {len(var_cvar)}")
print(f"  Mean VaR 95%   : {var_cvar['var_95_pct'].mean():.4f}%")
print(f"  Mean CVaR 95%  : {var_cvar['cvar_95_pct'].mean():.4f}%")
print(f"  Worst VaR 95%  : {var_cvar['var_95_pct'].min():.4f}%  <- {var_cvar.loc[var_cvar['var_95_pct'].idxmin(),'scheme_name'][:45]}")
print(f"  Best  VaR 95%  : {var_cvar['var_95_pct'].max():.4f}%  <- {var_cvar.loc[var_cvar['var_95_pct'].idxmax(),'scheme_name'][:45]}")
print()
print("  CVaR > VaR always (CVaR captures tail severity):")
print(f"  All CVaR < VaR : {(var_cvar['cvar_95'] < var_cvar['var_95']).all()}")

# ── Save — your exact line ─────────────────────────────────────────────────
out = PROC / "var_cvar_report.csv"
var_cvar.to_csv(out, index=False)

print()
print(f"  Saved -> data/processed/var_cvar_report.csv")
print(f"  Shape : {var_cvar.shape}")
print(f"  Cols  : {list(var_cvar.columns)}")
print()
print(var_cvar[["amfi_code","scheme_name","var_95_pct","cvar_95_pct"]].head(5).to_string(index=False))
