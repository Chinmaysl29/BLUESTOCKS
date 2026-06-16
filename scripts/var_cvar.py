"""
var_cvar.py
-----------
Bluestock Fintech Capstone

Computes Value at Risk (VaR) and Conditional VaR (CVaR) for all 40 schemes.

Your exact code:
    nav = pd.read_csv("data/processed/nav_history_clean.csv")
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    var_95 = returns.quantile(0.05)   # Historical VaR at 95% confidence

Additional:
    var_99    = returns.quantile(0.01)       # VaR at 99%
    cvar_95   = returns[returns <= var_95].mean()  # CVaR / Expected Shortfall
    cvar_99   = returns[returns <= var_99].mean()

Output:
    data/processed/var_cvar_report.csv
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
nav = pd.read_csv(PROC / "nav_history_clean.csv")
print("Line 1  nav = pd.read_csv('data/processed/nav_history_clean.csv')")
print(f"        Shape: {nav.shape}")
print()

# Line 2
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
print("Line 2  nav['daily_return'] = nav.groupby('amfi_code')['nav'].pct_change()")
print(f"        Non-null returns: {nav['daily_return'].notna().sum():,}")
print(f"        NaN (first row per scheme): {nav['daily_return'].isna().sum()}")
print()

# Line 3 — Historical VaR 95% (shown per scheme below)
# var_95 = returns.quantile(0.05)
print("Line 3  var_95 = returns.quantile(0.05)  [Historical VaR @ 95%]")
print("        Applied per scheme — see table below")
print()

# ═══════════════════════════════════════════════════════════
# COMPUTE VaR + CVaR FOR ALL 40 SCHEMES
# ═══════════════════════════════════════════════════════════

CONFIDENCE_LEVELS = {
    "95%": 0.05,
    "99%": 0.01,
}

rows = []
for code, grp in nav.groupby("amfi_code"):
    returns = grp["daily_return"].dropna()
    if len(returns) < 30:
        continue

    ann_vol    = returns.std() * np.sqrt(252) * 100
    ann_return = returns.mean() * 252 * 100

    row = {
        "amfi_code"   : code,
        "scheme_name" : grp["scheme_name"].iloc[0] if "scheme_name" in grp.columns else str(code),
        "category"    : grp["category"].iloc[0]    if "category"    in grp.columns else "",
        "plan"        : grp["plan"].iloc[0]         if "plan"        in grp.columns else "",
        "total_days"  : len(returns),
        "ann_return"  : round(ann_return, 2),
        "ann_vol"     : round(ann_vol, 2),
    }

    for label, alpha in CONFIDENCE_LEVELS.items():
        var  = returns.quantile(alpha)
        cvar = returns[returns <= var].mean()
        # Annualise for reporting (daily * sqrt(252))
        var_ann  = var  * np.sqrt(252)
        cvar_ann = cvar * np.sqrt(252)

        row[f"var_{label}_daily"]   = round(var  * 100, 4)   # %
        row[f"cvar_{label}_daily"]  = round(cvar * 100, 4)   # %
        row[f"var_{label}_ann"]     = round(var_ann  * 100, 4)
        row[f"cvar_{label}_ann"]    = round(cvar_ann * 100, 4)

    rows.append(row)

df = pd.DataFrame(rows).sort_values("var_95%_daily").reset_index(drop=True)
df.index += 1

# ── Print full table ──────────────────────────────────────
sep = "=" * 110
print(sep)
print("  VaR / CVaR REPORT — ALL 40 SCHEMES  (Historical Simulation)")
print("  VaR 95%  = quantile(0.05)  |  CVaR 95% = mean of worst 5% days")
print("  VaR 99%  = quantile(0.01)  |  CVaR 99% = mean of worst 1% days")
print(sep)
print(f"  {'#':>3}  {'Scheme':<46}  {'AnnRet':>7}  {'AnnVol':>7}  "
      f"{'VaR95%':>8}  {'CVaR95%':>9}  {'VaR99%':>8}  {'CVaR99%':>9}")
print("  " + "-" * 105)
for idx, r in df.iterrows():
    name = r["scheme_name"][:46]
    print(
        f"  {idx:>3}  {name:<46}  "
        f"{r['ann_return']:>6.2f}%  "
        f"{r['ann_vol']:>6.2f}%  "
        f"{r['var_95%_daily']:>7.4f}%  "
        f"{r['cvar_95%_daily']:>8.4f}%  "
        f"{r['var_99%_daily']:>7.4f}%  "
        f"{r['cvar_99%_daily']:>8.4f}%"
    )

# ── Summary stats ─────────────────────────────────────────
print()
print(sep)
print("  SUMMARY STATISTICS (daily %)")
print(sep)
for metric, col in [
    ("VaR  95% (daily %)", "var_95%_daily"),
    ("CVaR 95% (daily %)", "cvar_95%_daily"),
    ("VaR  99% (daily %)", "var_99%_daily"),
    ("CVaR 99% (daily %)", "cvar_99%_daily"),
]:
    vals = df[col]
    print(f"  {metric:<22}  mean={vals.mean():>8.4f}%  "
          f"min={vals.min():>8.4f}%  max={vals.max():>8.4f}%")

print()
print("  Least risky scheme (smallest VaR 95%):")
best = df.iloc[-1]
print(f"    {best['scheme_name'][:60]}  VaR95={best['var_95%_daily']:.4f}%  CVaR95={best['cvar_95%_daily']:.4f}%")
print()
print("  Most risky scheme (largest VaR 95%):")
worst = df.iloc[0]
print(f"    {worst['scheme_name'][:60]}  VaR95={worst['var_95%_daily']:.4f}%  CVaR95={worst['cvar_95%_daily']:.4f}%")

# ── Category averages ─────────────────────────────────────
print()
print(sep)
print("  BY CATEGORY (avg daily VaR 95%)")
print(sep)
cat = df.groupby("category")[["var_95%_daily","cvar_95%_daily","ann_vol"]].mean()
cat = cat.sort_values("var_95%_daily")
print(f"  {'Category':<20}  {'Avg VaR95%':>11}  {'Avg CVaR95%':>12}  {'Avg AnnVol':>11}")
print("  " + "-" * 60)
for cat_name, r in cat.iterrows():
    print(f"  {cat_name:<20}  {r['var_95%_daily']:>10.4f}%  "
          f"{r['cvar_95%_daily']:>11.4f}%  {r['ann_vol']:>10.2f}%")

# ── Chart: VaR vs CVaR scatter ────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel 1: VaR 95% bar chart sorted worst to best
df_plot = df.sort_values("var_95%_daily")
colors  = ["crimson" if v < -2 else "darkorange" if v < -1.5 else "steelblue"
           for v in df_plot["var_95%_daily"]]
axes[0].barh(df_plot["scheme_name"].str.split(" - ").str[0].str[:30],
             df_plot["var_95%_daily"], color=colors, edgecolor="white")
axes[0].axvline(df["var_95%_daily"].mean(), color="black", linestyle="--",
                linewidth=1, label=f"Mean={df['var_95%_daily'].mean():.3f}%")
axes[0].set_title("Historical VaR 95% by Scheme (daily %)")
axes[0].set_xlabel("VaR 95% (% daily loss at 95% confidence)")
axes[0].legend(fontsize=8)
axes[0].tick_params(axis="y", labelsize=6)

# Panel 2: VaR vs CVaR scatter by category
for cat_name, grp in df.groupby("category"):
    axes[1].scatter(grp["var_95%_daily"], grp["cvar_95%_daily"],
                    label=cat_name, s=50, alpha=0.8)
lims = [df[["var_95%_daily","cvar_95%_daily"]].min().min() - 0.1,
        df[["var_95%_daily","cvar_95%_daily"]].max().max() + 0.1]
axes[1].plot(lims, lims, "k--", linewidth=0.8, alpha=0.4, label="VaR=CVaR line")
axes[1].set_title("VaR 95% vs CVaR 95% (daily %)")
axes[1].set_xlabel("VaR 95% (%)")
axes[1].set_ylabel("CVaR 95% (%)")
axes[1].legend(bbox_to_anchor=(1.01, 1), fontsize=7)

plt.tight_layout()
chart_path = RPT / "var_cvar_chart.png"
plt.savefig(chart_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Chart saved -> {chart_path}")

# ── Save CSV ──────────────────────────────────────────────
out = PROC / "var_cvar_report.csv"
df.to_csv(out, index=False)
print(f"  CSV   saved -> {out}  ({len(df)} rows x {df.shape[1]} cols)")
print(sep)
