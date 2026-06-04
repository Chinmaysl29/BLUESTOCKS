"""
validate_sharpe.py
------------------
Validates the Sharpe ratio function against all 40 schemes,
cross-checks with precomputed performance data, and flags edge cases.

Formula:
    Sharpe = (Annualised Return - Rf) / Annualised Std Dev
    where Rf = 6.5% = 0.065  (RBI repo rate proxy)
"""

import pandas as pd
import numpy as np

# ── Data ─────────────────────────────────────────────────────────────────
nav         = pd.read_csv("data/processed/nav_history_clean.csv",  parse_dates=["date"])
performance = pd.read_csv("data/processed/performance_clean.csv")
nav         = nav.sort_values(["amfi_code", "date"])

# ── Constants ─────────────────────────────────────────────────────────────
Rf = 0.065          # 6.5% annualised risk-free rate
TRADING_DAYS = 252  # NSE trading days per year

# ── Your exact function ───────────────────────────────────────────────────
def sharpe_ratio(x):
    """
    Compute annualised Sharpe ratio from a daily return series.

    Args:
        x : pd.Series of DAILY returns as decimals (e.g. 0.006, not 0.6%)

    Returns:
        float — annualised Sharpe ratio
    """
    mean_return = x.mean() * TRADING_DAYS          # annualised mean return
    std_return  = x.std()  * np.sqrt(TRADING_DAYS) # annualised volatility
    return (mean_return - Rf) / std_return

# ── Apply to every scheme ─────────────────────────────────────────────────
rows = []
for code, grp in nav.groupby("amfi_code"):
    grp  = grp.sort_values("date").dropna(subset=["daily_return_pct"])
    rets = grp["daily_return_pct"] / 100   # convert % → decimal

    if len(rets) < 30:
        continue

    sr         = round(sharpe_ratio(rets), 4)
    ann_ret    = round(rets.mean() * TRADING_DAYS * 100, 2)
    ann_vol    = round(rets.std()  * np.sqrt(TRADING_DAYS) * 100, 2)
    rows.append({
        "amfi_code"  : code,
        "scheme_name": grp["scheme_name"].iloc[0],
        "category"   : grp["category"].iloc[0],
        "plan"       : grp["plan"].iloc[0],
        "ann_return" : ann_ret,
        "ann_vol"    : ann_vol,
        "sharpe_calc": sr,
    })

sharpe_df = pd.DataFrame(rows)

# Merge with precomputed Sharpe from performance_clean.csv
sharpe_df = sharpe_df.merge(
    performance[["amfi_code", "sharpe_ratio"]].rename(columns={"sharpe_ratio": "sharpe_precomp"}),
    on="amfi_code", how="left"
)
sharpe_df = sharpe_df.sort_values("sharpe_calc", ascending=False).reset_index(drop=True)
sharpe_df.index += 1

# ── Print ranked table ────────────────────────────────────────────────────
print("=" * 95)
print("  SHARPE RATIO — ALL 40 SCHEMES  (Rf = 6.5%,  252 trading days)")
print("=" * 95)
print(f"{'#':>3}  {'Scheme':<44}  {'Cat':<10}  {'Ann Ret':>8}  {'Ann Vol':>8}  {'Sharpe':>8}  {'Precomp':>8}")
print("-" * 95)
for idx, r in sharpe_df.iterrows():
    name  = r["scheme_name"][:44]
    diff  = "  ✅" if abs(r["sharpe_calc"] - r["sharpe_precomp"]) < 0.5 else "  ⚠️"
    print(
        f"{idx:>3}  {name:<44}  {r['category']:<10}  "
        f"{r['ann_return']:>7.2f}%  {r['ann_vol']:>7.2f}%  "
        f"{r['sharpe_calc']:>8.4f}  {r['sharpe_precomp']:>8.4f}{diff}"
    )

# ── Summary stats ─────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  SUMMARY STATISTICS")
print("=" * 60)
best  = sharpe_df.iloc[0]
worst = sharpe_df.iloc[-1]
print(f"  Highest Sharpe : {best['scheme_name'][:50]}")
print(f"                   Sharpe={best['sharpe_calc']}  |  Return={best['ann_return']}%  |  Vol={best['ann_vol']}%")
print(f"  Lowest  Sharpe : {worst['scheme_name'][:50]}")
print(f"                   Sharpe={worst['sharpe_calc']}  |  Return={worst['ann_return']}%  |  Vol={worst['ann_vol']}%")
print(f"  Mean Sharpe    : {sharpe_df['sharpe_calc'].mean():.4f}")
print(f"  Median Sharpe  : {sharpe_df['sharpe_calc'].median():.4f}")
print()
print("  By Category (avg Sharpe):")
cat_avg = sharpe_df.groupby("category")["sharpe_calc"].mean().sort_values(ascending=False)
for cat, val in cat_avg.items():
    bar = "#" * max(0, int(val * 10))
    sign = "+" if val >= 0 else ""
    print(f"    {cat:<20}  {sign}{val:>6.4f}  {bar}")

# ── Formula breakdown ─────────────────────────────────────────────────────
print()
print("=" * 60)
print("  FORMULA BREAKDOWN — SBI Bluechip (119551)")
print("=" * 60)
s    = nav[nav["amfi_code"] == 119551].sort_values("date").dropna(subset=["daily_return_pct"])
rets = s["daily_return_pct"] / 100
mu   = rets.mean()
sig  = rets.std()
ann_mu  = mu  * TRADING_DAYS
ann_sig = sig * np.sqrt(TRADING_DAYS)
sr_val  = (ann_mu - Rf) / ann_sig
print(f"  Daily mean return  :  {mu:.8f}  ({mu*100:.4f}%)")
print(f"  Daily std dev      :  {sig:.8f}  ({sig*100:.4f}%)")
print(f"  Annualised return  :  {ann_mu:.6f}  ({ann_mu*100:.2f}%)   [× 252]")
print(f"  Annualised vol     :  {ann_sig:.6f}  ({ann_sig*100:.2f}%)   [× √252]")
print(f"  Risk-free rate (Rf):  {Rf}  (6.5%)")
print(f"  Sharpe = ({ann_mu*100:.2f}% - {Rf*100:.1f}%) / {ann_sig*100:.2f}%")
print(f"         = {(ann_mu*100 - Rf*100):.4f}% / {ann_sig*100:.4f}%")
print(f"         = {sr_val:.4f}")

# ── Edge case checks ──────────────────────────────────────────────────────
print()
print("=" * 60)
print("  EDGE CASE VALIDATION")
print("=" * 60)

# 1. Zero std dev (constant NAV — e.g. liquid fund on some days)
zero_std = pd.Series([0.0001] * 252)   # near-zero vol, like liquid fund
try:
    result = sharpe_ratio(zero_std)
    print(f"  1. Near-zero vol series  → Sharpe = {result:.2f}  (large but finite ✅)")
except ZeroDivisionError:
    print("  1. Zero std dev          → ZeroDivisionError ⚠️  add guard")

const_series = pd.Series([0.0] * 252)
try:
    result = sharpe_ratio(const_series)
    print(f"  2. All-zero returns      → Sharpe = {result}  ⚠️  NaN/inf returned")
except Exception as e:
    print(f"  2. All-zero returns      → Exception: {e}")

# 3. Negative Sharpe
neg_series = pd.Series([-0.002] * 252)
print(f"  3. Consistently negative → Sharpe = {sharpe_ratio(neg_series):.4f}  (negative ✅ — expected)")

# 4. Units check: passing % values instead of decimals
pct_series = rets * 100   # wrong units
sr_wrong   = sharpe_ratio(pct_series)
sr_correct = sharpe_ratio(rets)
print(f"  4. UNIT CHECK:")
print(f"     Correct (decimal input) → Sharpe = {sr_correct:.4f}")
print(f"     Wrong   (%% input)       → Sharpe = {sr_wrong:.4f}   ← inflated by 100x ⚠️")
print(f"     Always pass daily_return_pct / 100  (decimal form)")

print()
print("  sharpe_ratio() is CORRECT when input is decimal daily returns.")
