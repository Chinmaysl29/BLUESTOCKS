"""
risk_metrics_all.py
-------------------
Bluestock Fintech Capstone
Runs all three production-ready risk metric functions on all 40 schemes:

    1. max_drawdown(df)     — peak-to-trough drawdown
    2. sharpe_ratio(x)      — annualised Sharpe (Rf = 6.5%)
    3. sortino_ratio(x)     — annualised Sortino (downside std only)

Outputs:
    data/processed/risk_metrics_all.csv   — full results table
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
nav         = pd.read_csv(BASE / "data/processed/nav_history_clean.csv",  parse_dates=["date"])
performance = pd.read_csv(BASE / "data/processed/performance_clean.csv")
nav         = nav.sort_values(["amfi_code", "date"])

# ── Constants ────────────────────────────────────────────────────────────
RF           = 0.065    # 6.5% annualised risk-free rate (RBI repo proxy)
TRADING_DAYS = 252

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
#  FUNCTION 1 — MAX DRAWDOWN
# ════════════════════════════════════════════════════════════════════════

def max_drawdown(df: pd.DataFrame) -> float:
    """
    Maximum drawdown from peak to trough over the full NAV history.

    Formula:
        running_max = cummax(NAV)
        drawdown    = (NAV / running_max) - 1   always <= 0
        MDD         = drawdown.min()

    Args:
        df : DataFrame with 'nav' and 'date' columns.
             Sort order is enforced inside — safe to pass unsorted.

    Returns:
        MDD as decimal (e.g. -0.1501 = -15.01%).
        Returns 0.0 if NAV is monotonically rising.
    """
    df          = df.sort_values("date")          # always enforce sort
    running_max = df["nav"].cummax()
    drawdown    = (df["nav"] / running_max) - 1
    return drawdown.min()


# ════════════════════════════════════════════════════════════════════════
#  FUNCTION 2 — SHARPE RATIO
# ════════════════════════════════════════════════════════════════════════

def sharpe_ratio(x: pd.Series) -> float:
    """
    Annualised Sharpe ratio from daily decimal returns.

    Formula:
        Sharpe = (mean_daily * 252 - Rf) / (std_daily * sqrt(252))

    Args:
        x : daily returns as DECIMALS (e.g. 0.006, NOT 0.6%)
            Pass nav['daily_return_pct'] / 100

    Returns:
        Annualised Sharpe ratio, or np.nan if std dev is zero.
    """
    mean_return = x.mean() * TRADING_DAYS
    std_return  = x.std()  * np.sqrt(TRADING_DAYS)
    if std_return == 0:
        return np.nan
    return (mean_return - RF) / std_return


# ════════════════════════════════════════════════════════════════════════
#  FUNCTION 3 — SORTINO RATIO
# ════════════════════════════════════════════════════════════════════════

def sortino_ratio(x: pd.Series) -> float:
    """
    Annualised Sortino ratio — penalises downside volatility only.

    Formula:
        Sortino = (mean_daily * 252 - Rf) / (std(x[x<0]) * sqrt(252))

    Args:
        x : daily returns as DECIMALS (e.g. 0.006, NOT 0.6%)

    Returns:
        Annualised Sortino ratio.
        Returns np.nan if no negative days or downside std is zero.

    Note:
        A series of identical negative values (e.g. all -0.002) has
        std=0 → downside_std=0 → division by zero → returns np.nan.
        This is correct: a fund with zero variance has no measurable
        downside risk spread; Sortino is undefined.
    """
    downside     = x[x < 0]
    if len(downside) < 2:           # need >= 2 points to compute std
        return np.nan
    downside_std = downside.std() * np.sqrt(TRADING_DAYS)
    if downside_std == 0 or np.isnan(downside_std) or downside_std < 1e-10:
        return np.nan
    annual_return = x.mean() * TRADING_DAYS
    return (annual_return - RF) / downside_std


# ════════════════════════════════════════════════════════════════════════
#  RUN ALL METRICS ON ALL 40 SCHEMES
# ════════════════════════════════════════════════════════════════════════

def run_all() -> pd.DataFrame:
    log.info("Running all 3 risk metric functions on %d schemes ...",
             nav["amfi_code"].nunique())

    rows = []
    for code, grp in nav.groupby("amfi_code"):
        grp  = grp.sort_values("date").reset_index(drop=True)
        rets = grp["daily_return_pct"].dropna() / 100   # decimal form

        mdd     = round(max_drawdown(grp) * 100, 4)
        sharpe  = round(sharpe_ratio(rets), 4)
        sortino = round(sortino_ratio(rets), 4)

        # Annualised stats for context
        ann_ret = round(rets.mean() * TRADING_DAYS * 100, 2)
        ann_vol = round(rets.std()  * np.sqrt(TRADING_DAYS) * 100, 2)
        neg_days = int((rets < 0).sum())

        rows.append({
            "amfi_code"   : code,
            "scheme_name" : grp["scheme_name"].iloc[0],
            "category"    : grp["category"].iloc[0],
            "plan"        : grp["plan"].iloc[0],
            "ann_return"  : ann_ret,
            "ann_vol"     : ann_vol,
            "neg_days"    : neg_days,
            "max_drawdown": mdd,
            "sharpe"      : sharpe,
            "sortino"     : sortino,
        })

    df = pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)
    df.index += 1
    return df


# ════════════════════════════════════════════════════════════════════════
#  PRINT RESULTS
# ════════════════════════════════════════════════════════════════════════

def print_results(df: pd.DataFrame) -> None:
    sep = "=" * 105

    # ── Full table ───────────────────────────────────────────────────────
    print(sep)
    print("  RISK METRICS — ALL 40 SCHEMES   (Rf=6.5%, 252 trading days)")
    print(sep)
    print(f"{'#':>3}  {'Scheme':<46}  {'Cat':<10}  {'AnnRet':>7}  "
          f"{'AnnVol':>7}  {'MDD':>8}  {'Sharpe':>7}  {'Sortino':>8}")
    print("-" * 105)
    for idx, r in df.iterrows():
        name = r["scheme_name"][:46]
        print(
            f"{idx:>3}  {name:<46}  {r['category']:<10}  "
            f"{r['ann_return']:>6.2f}%  {r['ann_vol']:>6.2f}%  "
            f"{r['max_drawdown']:>7.2f}%  {r['sharpe']:>7.4f}  {r['sortino']:>8.4f}"
        )

    # ── Summary stats ────────────────────────────────────────────────────
    print()
    print(sep)
    print("  SUMMARY STATISTICS")
    print(sep)

    metrics = {
        "Max Drawdown (%)": "max_drawdown",
        "Sharpe Ratio"    : "sharpe",
        "Sortino Ratio"   : "sortino",
    }
    for label, col in metrics.items():
        vals = df[col].dropna()
        best = df.loc[df[col].idxmax() if col != "max_drawdown" else df[col].idxmax(), "scheme_name"][:48]
        print(f"\n  {label}")
        print(f"    Best   : {best}")
        print(f"    Mean   : {vals.mean():.4f}   Median: {vals.median():.4f}   Std: {vals.std():.4f}")
        print(f"    Min    : {vals.min():.4f}   Max: {vals.max():.4f}")

    # ── Category averages ────────────────────────────────────────────────
    print()
    print(sep)
    print("  CATEGORY AVERAGES")
    print(sep)
    print(f"  {'Category':<20}  {'Avg MDD':>9}  {'Avg Sharpe':>11}  {'Avg Sortino':>12}  {'Avg AnnRet':>11}")
    print("  " + "-" * 70)
    cat_grp = df.groupby("category")[["max_drawdown", "sharpe", "sortino", "ann_return"]].mean()
    for cat, row in cat_grp.sort_values("sharpe", ascending=False).iterrows():
        print(f"  {cat:<20}  {row['max_drawdown']:>8.2f}%  "
              f"{row['sharpe']:>11.4f}  {row['sortino']:>12.4f}  {row['ann_return']:>10.2f}%")

    # ── Relationship table: Sharpe vs Sortino ────────────────────────────
    print()
    print(sep)
    print("  SHARPE vs SORTINO — KEY OBSERVATIONS")
    print(sep)
    higher = (df["sortino"] > df["sharpe"]).sum()
    print(f"  Sortino > Sharpe   : {higher}/{len(df)} schemes")
    print(f"  This is expected   : downside_std < total_std always when neg days < 50%")
    avg_diff = (df["sortino"] - df["sharpe"]).mean()
    print(f"  Avg difference     : {avg_diff:.4f}  (Sortino - Sharpe)")
    print()
    print(f"  {'Scheme':<46}  {'Sharpe':>8}  {'Sortino':>9}  {'Diff':>7}")
    print("  " + "-" * 75)
    for _, r in df.iterrows():
        diff  = r["sortino"] - r["sharpe"]
        arrow = "▲" if diff > 0 else "▼"
        print(f"  {r['scheme_name'][:46]:<46}  {r['sharpe']:>8.4f}  "
              f"{r['sortino']:>9.4f}  {arrow}{abs(diff):>6.4f}")


# ════════════════════════════════════════════════════════════════════════
#  EDGE CASE TESTS
# ════════════════════════════════════════════════════════════════════════

def run_edge_cases() -> None:
    print()
    print("=" * 60)
    print("  EDGE CASE TESTS — ALL 3 FUNCTIONS")
    print("=" * 60)
    all_pass = True

    def check(name, got, expected, tol=0.0001):
        nonlocal all_pass
        if np.isnan(got) and np.isnan(expected):
            status = "PASS"
        elif np.isnan(got) or np.isnan(expected):
            status = "FAIL"
        else:
            status = "PASS" if abs(got - expected) <= tol else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}]  {name:<45}  got={got:>9.4f}  expected={expected:>9.4f}")

    dates = pd.date_range("2022-01-01", periods=6)

    # max_drawdown
    check("MDD: rising only",
          max_drawdown(pd.DataFrame({"date": dates[:5], "nav": [100,101,102,103,104]})),
          0.0)
    check("MDD: falling 100->60",
          max_drawdown(pd.DataFrame({"date": dates[:5], "nav": [100,90,80,70,60]})),
          -0.40)
    check("MDD: V-shape 100->70->110",
          max_drawdown(pd.DataFrame({"date": dates, "nav": [100,90,70,80,100,110]})),
          -0.30)
    check("MDD: unsorted input (sort guard)",
          max_drawdown(pd.DataFrame({"date": dates[:5][::-1], "nav": [104,103,102,101,100]})),
          0.0)

    # sharpe_ratio
    flat = pd.Series([0.0] * 252)          # zero returns → std=0 → NaN
    check("Sharpe: zero std dev => NaN",    sharpe_ratio(flat), np.nan)
    rf_daily = RF / TRADING_DAYS
    flat_rf  = pd.Series([rf_daily] * 252) # exact Rf daily → Sharpe=0
    # std of constant series is 0 → our guard returns NaN (correct behaviour)
    check("Sharpe: returns equal Rf (std=0)",  sharpe_ratio(flat_rf), np.nan)
    pos  = pd.Series([0.001] * 126 + [-0.0001] * 126)  # mixed → std > 0
    check("Sharpe: positive-dominant returns",
          sharpe_ratio(pos),
          (pos.mean() * TRADING_DAYS - RF) / (pos.std() * np.sqrt(TRADING_DAYS)))

    # sortino_ratio
    pos_only = pd.Series([0.003] * 252)
    check("Sortino: no negative days => NaN",  sortino_ratio(pos_only), np.nan)
    neg_only = pd.Series([-0.002] * 252)       # all same value → std=0 → NaN
    check("Sortino: zero downside std => NaN", sortino_ratio(neg_only), np.nan)
    mixed    = pd.Series([0.001, -0.001] * 126)
    ds       = mixed[mixed < 0].std() * np.sqrt(TRADING_DAYS)
    expected_s = (mixed.mean() * TRADING_DAYS - RF) / ds
    check("Sortino: mixed returns",            sortino_ratio(mixed), expected_s)

    # Unit warning check
    rets_decimal = nav[nav["amfi_code"] == 119551]["daily_return_pct"].dropna() / 100
    rets_pct     = rets_decimal * 100
    sharpe_correct = round(sharpe_ratio(rets_decimal), 4)
    sharpe_wrong   = round(sharpe_ratio(rets_pct), 4)
    print()
    print(f"  UNIT CHECK (SBI Bluechip 119551):")
    print(f"    Correct  (decimal input /100) → Sharpe  = {sharpe_correct}")
    print(f"    Incorrect (%% input, no /100)  → Sharpe  = {sharpe_wrong}  ⚠️  inflated")
    print()
    print(f"  All edge cases: {'ALL PASSED' if all_pass else 'SOME FAILED — review above'}")


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_all()
    print_results(results)
    run_edge_cases()

    # Save to processed
    out_path = BASE / "data/processed/risk_metrics_all.csv"
    results.to_csv(out_path, index=False)
    log.info("Saved full results → %s", out_path)
