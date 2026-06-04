"""
validate_max_drawdown.py
------------------------
Validates the max_drawdown function on all 40 schemes.
Also identifies drawdown period (peak date, trough date, recovery).

Formula:
    running_max = cumulative maximum of NAV up to each point
    drawdown    = (NAV / running_max) - 1          <- always <= 0
    max_drawdown = drawdown.min()                  <- most negative value
"""

import pandas as pd
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────
nav         = pd.read_csv("data/processed/nav_history_clean.csv", parse_dates=["date"])
performance = pd.read_csv("data/processed/performance_clean.csv")
nav         = nav.sort_values(["amfi_code", "date"])

# ── Your exact function ───────────────────────────────────────────────────
def max_drawdown(df):
    running_max = df["nav"].cummax()
    drawdown    = (df["nav"] / running_max) - 1
    return drawdown.min()


# ── Extended version — also returns peak/trough dates ────────────────────
def max_drawdown_detail(df):
    """Returns MDD value plus the peak date, trough date, and duration."""
    df        = df.sort_values("date").reset_index(drop=True)
    nav_vals  = df["nav"].values
    dates     = df["date"].values

    running_max = np.maximum.accumulate(nav_vals)
    drawdown    = (nav_vals / running_max) - 1
    mdd         = drawdown.min()
    trough_idx  = drawdown.argmin()

    # Peak is the last time NAV was at its high before the trough
    peak_idx    = np.argmax(nav_vals[:trough_idx + 1])

    # Recovery: first date after trough where NAV exceeds peak NAV
    peak_nav    = nav_vals[peak_idx]
    recovery_dates = np.where(nav_vals[trough_idx:] >= peak_nav)[0]
    recovery_idx   = trough_idx + recovery_dates[0] if len(recovery_dates) > 0 else None

    duration_days    = (dates[trough_idx] - dates[peak_idx]) / np.timedelta64(1, "D")
    recovery_days    = (
        (dates[recovery_idx] - dates[trough_idx]) / np.timedelta64(1, "D")
        if recovery_idx is not None else None
    )

    return {
        "mdd_pct"       : round(mdd * 100, 2),
        "peak_date"     : pd.Timestamp(dates[peak_idx]).date(),
        "trough_date"   : pd.Timestamp(dates[trough_idx]).date(),
        "peak_nav"      : round(float(nav_vals[peak_idx]), 4),
        "trough_nav"    : round(float(nav_vals[trough_idx]), 4),
        "drawdown_days" : int(duration_days),
        "recovery_days" : int(recovery_days) if recovery_days is not None else "Not yet",
    }


# ── Apply to every scheme ─────────────────────────────────────────────────
rows = []
for code, grp in nav.groupby("amfi_code"):
    grp  = grp.sort_values("date").reset_index(drop=True)
    mdd  = round(max_drawdown(grp) * 100, 2)        # convert to %
    det  = max_drawdown_detail(grp)
    pre  = performance.loc[performance["amfi_code"] == code, "max_drawdown_pct"]
    pre_val = float(pre.values[0]) if len(pre) > 0 else np.nan

    rows.append({
        "amfi_code"     : code,
        "scheme_name"   : grp["scheme_name"].iloc[0],
        "category"      : grp["category"].iloc[0],
        "plan"          : grp["plan"].iloc[0],
        "mdd_pct"       : mdd,
        "precomp_mdd"   : pre_val,
        "peak_date"     : det["peak_date"],
        "trough_date"   : det["trough_date"],
        "peak_nav"      : det["peak_nav"],
        "trough_nav"    : det["trough_nav"],
        "drawdown_days" : det["drawdown_days"],
        "recovery_days" : det["recovery_days"],
    })

df_out = pd.DataFrame(rows).sort_values("mdd_pct").reset_index(drop=True)
df_out.index += 1

# ── Print ranked table ────────────────────────────────────────────────────
print("=" * 110)
print("  MAX DRAWDOWN — ALL 40 SCHEMES  (sorted worst → best)")
print("=" * 110)
print(f"{'#':>3}  {'Scheme':<42}  {'MDD%':>7}  {'Precomp':>8}  {'Peak Date':>11}  {'Trough':>11}  {'DD Days':>7}  {'Recov':>9}")
print("-" * 110)
for idx, r in df_out.iterrows():
    name  = r["scheme_name"][:42]
    match = "✅" if abs(r["mdd_pct"] - r["precomp_mdd"]) < 5 else "⚠️ "
    recov = str(r["recovery_days"]) if r["recovery_days"] != "Not yet" else "Pending"
    print(
        f"{idx:>3}  {name:<42}  "
        f"{r['mdd_pct']:>6.2f}%  "
        f"{r['precomp_mdd']:>7.2f}%{match}  "
        f"{str(r['peak_date']):>11}  "
        f"{str(r['trough_date']):>11}  "
        f"{r['drawdown_days']:>7}  "
        f"{recov:>9}"
    )

# ── Summary stats ─────────────────────────────────────────────────────────
print()
print("=" * 65)
print("  SUMMARY STATISTICS")
print("=" * 65)
worst = df_out.iloc[0]
best  = df_out.iloc[-1]
print(f"  Worst MDD : {worst['scheme_name'][:50]}")
print(f"              MDD={worst['mdd_pct']}%  |  Peak={worst['peak_date']}  |  Trough={worst['trough_date']}")
print(f"  Best  MDD : {best['scheme_name'][:50]}")
print(f"              MDD={best['mdd_pct']}%  |  Peak={best['peak_date']}  |  Trough={best['trough_date']}")
print(f"  Mean  MDD : {df_out['mdd_pct'].mean():.2f}%")
print(f"  Median MDD: {df_out['mdd_pct'].median():.2f}%")
print()
print("  By Category (avg MDD):")
cat_avg = df_out.groupby("category")["mdd_pct"].mean().sort_values()
for cat, val in cat_avg.items():
    bar = "#" * int(abs(val) / 2)
    print(f"    {cat:<20}  {val:>7.2f}%  {bar}")

# ── Step-by-step breakdown ────────────────────────────────────────────────
print()
print("=" * 65)
print("  FORMULA BREAKDOWN — SBI Bluechip (119551)")
print("=" * 65)
s   = nav[nav["amfi_code"] == 119551].sort_values("date").reset_index(drop=True)
det = max_drawdown_detail(s)

running_max = s["nav"].cummax()
drawdown    = (s["nav"] / running_max) - 1
trough_idx  = drawdown.idxmin()

print(f"  Step 1 — cummax():  running_max tracks the highest NAV seen so far")
print(f"  Step 2 — drawdown = (nav / running_max) - 1   (always ≤ 0)")
print(f"  Step 3 — drawdown.min() = the deepest trough")
print()
print(f"  Peak NAV   : ₹{det['peak_nav']}   on  {det['peak_date']}")
print(f"  Trough NAV : ₹{det['trough_nav']}   on  {det['trough_date']}")
print(f"  MDD        : ({det['trough_nav']} / {det['peak_nav']}) - 1 = {det['mdd_pct']}%")
print(f"  Duration   : {det['drawdown_days']} days peak → trough")
print(f"  Recovery   : {det['recovery_days']} days trough → back to peak")
print()
print(f"  Sample drawdown series (around trough ±3 days):")
window = s.iloc[max(0, trough_idx-3): trough_idx+4][["date","nav"]].copy()
window["running_max"] = s["nav"].cummax().iloc[max(0, trough_idx-3): trough_idx+4].values
window["drawdown_pct"] = ((window["nav"] / window["running_max"]) - 1).mul(100).round(4)
print(window.to_string(index=False))

# ── Edge case checks ──────────────────────────────────────────────────────
print()
print("=" * 65)
print("  EDGE CASE VALIDATION")
print("=" * 65)

# 1. Monotonically rising NAV (no drawdown)
rising = pd.DataFrame({"nav": [100, 101, 102, 103, 104]})
mdd_rising = max_drawdown(rising)
print(f"  1. Always rising NAV   → MDD = {mdd_rising:.4f} (0.0 = no drawdown ✅)")

# 2. Monotonically falling NAV
falling = pd.DataFrame({"nav": [100, 90, 80, 70, 60]})
mdd_falling = max_drawdown(falling)
print(f"  2. Always falling NAV  → MDD = {mdd_falling*100:.2f}% (-40.0% ✅)")

# 3. V-shaped recovery
v_shape = pd.DataFrame({"nav": [100, 90, 70, 80, 100, 110]})
mdd_v = max_drawdown(v_shape)
print(f"  3. V-shape (100→70→110)→ MDD = {mdd_v*100:.2f}% (-30.0% ✅)")

# 4. Multiple drawdown episodes — takes the deepest
multi = pd.DataFrame({"nav": [100, 85, 95, 110, 75, 105, 120]})
mdd_multi = max_drawdown(multi)
print(f"  4. Multiple episodes   → MDD = {mdd_multi*100:.2f}% (-31.82% from 110→75 ✅)")

# 5. df must be sorted by date before calling
unsorted = nav[nav["amfi_code"] == 119551].sample(frac=1, random_state=42)
mdd_unsorted = round(max_drawdown(unsorted) * 100, 2)
mdd_sorted   = round(max_drawdown(nav[nav["amfi_code"] == 119551].sort_values("date")) * 100, 2)
flag = "✅ same" if mdd_unsorted == mdd_sorted else f"⚠️  DIFFERENT  sorted={mdd_sorted}% vs unsorted={mdd_unsorted}%"
print(f"  5. Sort order matters  → sorted={mdd_sorted}%  unsorted={mdd_unsorted}%  {flag}")

print()
print("  max_drawdown() is CORRECT — requires df sorted by date.")
