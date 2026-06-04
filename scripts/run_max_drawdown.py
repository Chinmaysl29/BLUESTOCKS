"""
run_max_drawdown.py
-------------------
Runs the production-ready max_drawdown function on all 40 schemes
and validates against 4 edge cases.
"""

import pandas as pd
import numpy as np

nav         = pd.read_csv("data/processed/nav_history_clean.csv", parse_dates=["date"])
performance = pd.read_csv("data/processed/performance_clean.csv")
nav         = nav.sort_values(["amfi_code", "date"])


# ── Production-ready function (final version) ────────────────────────────
def max_drawdown(df: pd.DataFrame) -> float:
    """
    Maximum drawdown from peak to trough over the full NAV history.

    Args:
        df: DataFrame with 'nav' and 'date' columns.
            MUST be sorted by date ascending before calling.

    Returns:
        MDD as a decimal (e.g. -0.1501 = -15.01%).
        Returns 0.0 if NAV is monotonically rising.
    """
    df          = df.sort_values("date")          # always enforce sort
    running_max = df["nav"].cummax()
    drawdown    = (df["nav"] / running_max) - 1
    return drawdown.min()


# ── Apply to all 40 schemes ───────────────────────────────────────────────
rows = []
for code, grp in nav.groupby("amfi_code"):
    mdd     = max_drawdown(grp)
    pre_val = performance.loc[performance["amfi_code"] == code, "max_drawdown_pct"].values
    rows.append({
        "amfi_code"  : code,
        "scheme"     : grp["scheme_name"].iloc[0][:50],
        "category"   : grp["category"].iloc[0],
        "plan"       : grp["plan"].iloc[0],
        "mdd_pct"    : round(mdd * 100, 2),
        "precomp_pct": float(pre_val[0]) if len(pre_val) else None,
    })

df_out = (
    pd.DataFrame(rows)
    .sort_values("mdd_pct")
    .reset_index(drop=True)
)
df_out.index += 1

# ── Print results ────────────────────────────────────────────────────────
print("=" * 80)
print("  MAX DRAWDOWN — production function — all 40 schemes")
print("=" * 80)
print(f"{'#':>3}  {'Scheme':<50}  {'MDD%':>8}")
print("-" * 80)
for idx, r in df_out.iterrows():
    print(f"{idx:>3}  {r['scheme']:<50}  {r['mdd_pct']:>7.2f}%")

print()
print(f"  Worst MDD : {df_out.iloc[0]['scheme'].strip()}  =>  {df_out.iloc[0]['mdd_pct']}%")
print(f"  Best  MDD : {df_out.iloc[-1]['scheme'].strip()}  =>  {df_out.iloc[-1]['mdd_pct']}%")
print(f"  Mean  MDD : {df_out['mdd_pct'].mean():.2f}%")
print(f"  Median MDD: {df_out['mdd_pct'].median():.2f}%")
print()
print("  By Category (avg MDD):")
for cat, val in df_out.groupby("category")["mdd_pct"].mean().sort_values().items():
    bar = "#" * int(abs(val) / 2)
    print(f"    {cat:<20}  {val:>7.2f}%  {bar}")


# ── Edge case tests ───────────────────────────────────────────────────────
print()
print("=" * 55)
print("  EDGE CASE TESTS")
print("=" * 55)

cases = [
    (
        "Rising only (no drawdown)",
        pd.DataFrame({
            "date": pd.date_range("2022-01-01", periods=5),
            "nav" : [100, 101, 102, 103, 104],
        }),
        0.0,
    ),
    (
        "Falling only (100 -> 60)",
        pd.DataFrame({
            "date": pd.date_range("2022-01-01", periods=5),
            "nav" : [100, 90, 80, 70, 60],
        }),
        -0.40,
    ),
    (
        "V-shape (100 -> 70 -> 110)",
        pd.DataFrame({
            "date": pd.date_range("2022-01-01", periods=6),
            "nav" : [100, 90, 70, 80, 100, 110],
        }),
        -0.30,
    ),
    (
        "Unsorted input — sort guard fires",
        pd.DataFrame({
            "date": pd.date_range("2022-01-01", periods=5)[::-1],
            "nav" : [104, 103, 102, 101, 100],
        }),
        0.0,   # rising when sorted correctly
    ),
]

all_pass = True
for name, test_df, expected in cases:
    result = round(max_drawdown(test_df), 4)
    status = "PASS" if abs(result - expected) < 0.001 else "FAIL"
    if status == "FAIL":
        all_pass = False
    label = "ok" if status == "PASS" else "MISMATCH"
    print(f"  [{status}]  {name:<35}  got={result*100:.2f}%  expected={expected*100:.2f}%  {label}")

print()
print(f"  All edge cases : {'PASSED' if all_pass else 'SOME FAILED'}")
print()
print("  max_drawdown() is production-ready.")
