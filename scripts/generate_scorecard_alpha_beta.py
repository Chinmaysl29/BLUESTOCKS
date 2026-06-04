"""
generate_scorecard_alpha_beta.py
---------------------------------
Task 2:
    scorecard.to_csv("data/processed/fund_scorecard.csv", index=False)
    alpha_beta.to_csv("data/processed/alpha_beta.csv",    index=False)

fund_scorecard — combines all metrics into one master scorecard per scheme
alpha_beta     — OLS regression of each scheme vs its category benchmark
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import linregress

BASE  = Path(__file__).resolve().parent.parent
PROC  = BASE / "data" / "processed"
RAW   = BASE / "data" / "raw"

# ── Load ──────────────────────────────────────────────────────────────────
nav         = pd.read_csv(PROC / "nav_history_clean.csv",  parse_dates=["date"])
performance = pd.read_csv(PROC / "performance_clean.csv",  parse_dates=["launch_date"])
risk        = pd.read_csv(PROC / "risk_metrics_all.csv")
ranking     = pd.read_csv(PROC / "fund_ranking.csv")
benchmark   = pd.read_csv(RAW  / "10_benchmark_indices.csv", parse_dates=["date"])
nav         = nav.sort_values(["amfi_code", "date"])

# Wide benchmark returns
bench_wide = benchmark.pivot_table(index="date", columns="index_name", values="close_value")
bench_wide.columns.name = None
bench_ret  = bench_wide.pct_change().mul(100)   # % form

# Category -> benchmark mapping
CAT_BENCH = {
    "Large Cap"      : "NIFTY100",
    "Mid Cap"        : "NIFTY_MIDCAP150",
    "Small Cap"      : "BSE_SMALLCAP",
    "Flexi Cap"      : "NIFTY500",
    "Large & Mid Cap": "NIFTY500",
    "Value"          : "NIFTY500",
    "ELSS"           : "NIFTY500",
    "Index/ETF"      : "NIFTY50",
    "Index"          : "NIFTY50",
    "Gilt"           : "CRISIL_GILT",
    "Liquid"         : "CRISIL_LIQUID",
    "Short Duration" : "CRISIL_GILT",
}

# ══════════════════════════════════════════════════════════════════════════
# TASK A — ALPHA / BETA  via OLS regression
# ══════════════════════════════════════════════════════════════════════════
print("Computing Alpha/Beta via OLS regression ...")
ab_rows = []

for code, grp in nav.groupby("amfi_code"):
    grp      = grp.sort_values("date").dropna(subset=["daily_return_pct"])
    category = grp["category"].iloc[0]
    bench_col = CAT_BENCH.get(category, "NIFTY50")

    # Align fund returns with correct benchmark returns
    fund_ret  = grp.set_index("date")["daily_return_pct"]
    bmark_ret = bench_ret[bench_col].dropna()

    merged = pd.concat([fund_ret, bmark_ret], axis=1, join="inner")
    merged.columns = ["fund", "bench"]
    merged = merged.dropna()

    if len(merged) < 30:
        continue

    # OLS:  fund_ret = alpha + beta * bench_ret
    slope, intercept, r_value, p_value, std_err = linregress(
        merged["bench"], merged["fund"]
    )

    # Annualised alpha (daily intercept * 252)
    ann_alpha = round(intercept * 252, 4)
    beta      = round(slope, 4)
    r_sq      = round(r_value ** 2, 4)
    t_stat    = round(slope / std_err, 4) if std_err > 0 else np.nan

    # Tracking error = std of (fund - bench)
    tracking_err = round((merged["fund"] - merged["bench"]).std() * np.sqrt(252), 4)

    # Information ratio = ann_excess_return / tracking_error
    ann_excess = round((merged["fund"] - merged["bench"]).mean() * 252, 4)
    info_ratio = round(ann_excess / tracking_err, 4) if tracking_err > 0 else np.nan

    ab_rows.append({
        "amfi_code"      : code,
        "scheme_name"    : grp["scheme_name"].iloc[0],
        "category"       : category,
        "plan"           : grp["plan"].iloc[0],
        "benchmark_used" : bench_col,
        "ols_beta"       : beta,
        "ols_daily_alpha": round(intercept, 6),
        "ols_ann_alpha"  : ann_alpha,
        "r_squared"      : r_sq,
        "t_stat_beta"    : t_stat,
        "tracking_error" : tracking_err,
        "ann_excess_ret" : ann_excess,
        "info_ratio"     : info_ratio,
        "n_obs"          : len(merged),
    })

alpha_beta = pd.DataFrame(ab_rows).sort_values("ols_ann_alpha", ascending=False).reset_index(drop=True)
alpha_beta.to_csv(PROC / "alpha_beta.csv", index=False)
print(f"  alpha_beta.csv  saved  ({len(alpha_beta)} rows x {alpha_beta.shape[1]} cols)")

# Print alpha_beta results
print()
print("=" * 95)
print("  ALPHA / BETA — OLS REGRESSION (each scheme vs category benchmark)")
print("=" * 95)
print(f"{'#':>3}  {'Scheme':<44}  {'Benchmark':<16}  {'Beta':>6}  {'AnnAlpha':>9}  {'R²':>6}  {'InfoR':>7}")
print("-" * 95)
for i, r in alpha_beta.iterrows():
    name = r["scheme_name"][:44]
    print(f"{i+1:>3}  {name:<44}  {r['benchmark_used']:<16}  "
          f"{r['ols_beta']:>6.4f}  {r['ols_ann_alpha']:>9.4f}  "
          f"{r['r_squared']:>6.4f}  {r['info_ratio']:>7.4f}")


# ══════════════════════════════════════════════════════════════════════════
# TASK B — FUND SCORECARD  (master table combining all datasets)
# ══════════════════════════════════════════════════════════════════════════
print("\nBuilding fund scorecard ...")

scorecard = (
    performance[[
        "amfi_code","scheme_name","fund_house","category","plan",
        "return_1yr_pct","return_3yr_pct","return_5yr_pct",
        "alpha","beta","sharpe_ratio","sortino_ratio",
        "std_dev_ann_pct","max_drawdown_pct","aum_crore",
        "expense_ratio_pct","morningstar_rating","risk_grade",
        "benchmark","excess_return","information_ratio",
        "risk_score","launch_date",
    ]]
    .merge(
        risk[["amfi_code","ann_return","ann_vol","sharpe","sortino",
              "max_drawdown","neg_days"]],
        on="amfi_code", how="left"
    )
    .merge(
        alpha_beta[["amfi_code","benchmark_used","ols_beta","ols_ann_alpha",
                    "r_squared","tracking_error","info_ratio"]],
        on="amfi_code", how="left"
    )
    .merge(
        ranking[["amfi_code","composite_score","final_rank",
                 "return_rank","sharpe_rank","alpha_rank",
                 "expense_rank","dd_rank"]],
        on="amfi_code", how="left"
    )
)

scorecard = scorecard.sort_values("final_rank").reset_index(drop=True)
scorecard.to_csv(PROC / "fund_scorecard.csv", index=False)
print(f"  fund_scorecard.csv  saved  ({len(scorecard)} rows x {scorecard.shape[1]} cols)")
print(f"  Columns: {list(scorecard.columns)}")

# Print top 10
print()
print("=" * 85)
print("  FUND SCORECARD — TOP 10  (by composite rank)")
print("=" * 85)
display_cols = ["final_rank","scheme_name","category","return_3yr_pct",
                "sharpe","ols_ann_alpha","ols_beta","max_drawdown",
                "expense_ratio_pct","composite_score"]
print(scorecard[display_cols].head(10).to_string(index=False))
print()
print("Saved:")
print(f"  data/processed/fund_scorecard.csv  — {len(scorecard)} rows, {scorecard.shape[1]} cols")
print(f"  data/processed/alpha_beta.csv      — {len(alpha_beta)} rows, {alpha_beta.shape[1]} cols")
