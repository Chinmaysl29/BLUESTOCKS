"""
fund_ranking.py
---------------
Bluestock Fintech Capstone — Fund Ranking Engine

Weighted composite score:
    30% — 3-Year Return Rank
    25% — Sharpe Ratio Rank
    20% — Alpha Rank
    15% — Expense Ratio Rank  (lower is better → inverted rank)
    10% — Max Drawdown Rank   (lower drawdown is better → inverted rank)

    score = 0.30*return_rank + 0.25*sharpe_rank + 0.20*alpha_rank
          + 0.15*expense_rank + 0.10*dd_rank

Ranking method: percentile rank (0–1), higher = better for all metrics.
    - return_3yr_pct  : higher is better  → rank ascending
    - sharpe_ratio    : higher is better  → rank ascending
    - alpha           : higher is better  → rank ascending
    - expense_ratio   : LOWER  is better  → rank DESCENDING (inverted)
    - max_drawdown    : LESS negative is better → rank DESCENDING (inverted)

Output:
    data/processed/fund_ranking.csv
    reports/fund_ranking_report.txt
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────
BASE     = Path(__file__).resolve().parent.parent
PROC_DIR = BASE / "data" / "processed"
RPT_DIR  = BASE / "reports"
RPT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Weights ───────────────────────────────────────────────────────────────
WEIGHTS = {
    "return_rank" : 0.30,
    "sharpe_rank" : 0.25,
    "alpha_rank"  : 0.20,
    "expense_rank": 0.15,
    "dd_rank"     : 0.10,
}

# ── Load data ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    perf = pd.read_csv(PROC_DIR / "performance_clean.csv")
    risk = pd.read_csv(PROC_DIR / "risk_metrics_all.csv")
    master = pd.read_csv(BASE / "data/raw/01_fund_master.csv",
                         usecols=["amfi_code", "sub_category"])

    # Merge on amfi_code
    df = perf[[
        "amfi_code", "scheme_name", "fund_house", "category",
        "plan", "return_3yr_pct", "alpha",
        "expense_ratio_pct", "morningstar_rating", "risk_grade",
        "benchmark_3yr_pct", "excess_return",
    ]].merge(
        risk[["amfi_code", "sharpe", "sortino", "max_drawdown", "ann_return", "ann_vol"]],
        on="amfi_code", how="left"
    ).merge(master, on="amfi_code", how="left")
    log.info("Loaded %d schemes for ranking", len(df))
    return df


# ── Ranking engine ────────────────────────────────────────────────────────
def compute_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute percentile ranks for each metric.
    pct_rank(ascending=True) → higher raw value = higher rank (0–1).
    Inverted metrics use ascending=False so lower raw = higher rank.
    """
    df = df.copy()

    # 1. 3-Year Return — higher is better
    df["return_rank"]  = df["return_3yr_pct"].rank(pct=True, ascending=True)

    # 2. Sharpe Ratio — higher is better
    df["sharpe_rank"]  = df["sharpe"].rank(pct=True, ascending=True)

    # 3. Alpha — higher is better
    df["alpha_rank"]   = df["alpha"].rank(pct=True, ascending=True)

    # 4. Expense Ratio — LOWER is better → invert
    df["expense_rank"] = df["expense_ratio_pct"].rank(pct=True, ascending=False)

    # 5. Max Drawdown — less negative (closer to 0) is better → invert
    df["dd_rank"]      = df["max_drawdown"].rank(pct=True, ascending=False)

    return df


def compute_score(df: pd.DataFrame) -> pd.DataFrame:
    """Apply weighted sum to produce composite score."""
    df = df.copy()
    df["composite_score"] = (
        WEIGHTS["return_rank"]  * df["return_rank"]  +
        WEIGHTS["sharpe_rank"]  * df["sharpe_rank"]  +
        WEIGHTS["alpha_rank"]   * df["alpha_rank"]   +
        WEIGHTS["expense_rank"] * df["expense_rank"] +
        WEIGHTS["dd_rank"]      * df["dd_rank"]
    ).round(4)

    # Final rank 1 = best
    df["final_rank"] = df["composite_score"].rank(ascending=False).astype(int)
    df = df.sort_values("final_rank").reset_index(drop=True)
    return df


# ── Print results ─────────────────────────────────────────────────────────
def print_full_table(df: pd.DataFrame, out_lines: list) -> None:
    sep = "=" * 130

    header = (
        f"{'Rank':>4}  {'Scheme':<46}  {'Cat':<10}  {'Plan':<8}  "
        f"{'3YRet':>6}  {'Sharpe':>7}  {'Alpha':>6}  {'Exp%':>5}  {'MDD':>7}  "
        f"{'Score':>7}  "
        f"{'RRnk':>5}  {'SRnk':>5}  {'ARnk':>5}  {'ERnk':>5}  {'DRnk':>5}"
    )
    divider = "-" * 130

    lines = [sep,
             "  BLUESTOCK FUND RANKING — COMPOSITE WEIGHTED SCORE",
             f"  Weights: Return={WEIGHTS['return_rank']*100:.0f}%  "
             f"Sharpe={WEIGHTS['sharpe_rank']*100:.0f}%  "
             f"Alpha={WEIGHTS['alpha_rank']*100:.0f}%  "
             f"Expense={WEIGHTS['expense_rank']*100:.0f}%  "
             f"Drawdown={WEIGHTS['dd_rank']*100:.0f}%",
             sep, header, divider]

    for _, r in df.iterrows():
        name = r["scheme_name"][:46]
        line = (
            f"{r['final_rank']:>4}  {name:<46}  {r['category']:<10}  {r['plan']:<8}  "
            f"{r['return_3yr_pct']:>6.2f}  {r['sharpe']:>7.4f}  "
            f"{r['alpha']:>6.2f}  {r['expense_ratio_pct']:>5.2f}  "
            f"{r['max_drawdown']:>7.2f}  "
            f"{r['composite_score']:>7.4f}  "
            f"{r['return_rank']:>5.3f}  {r['sharpe_rank']:>5.3f}  "
            f"{r['alpha_rank']:>5.3f}  {r['expense_rank']:>5.3f}  {r['dd_rank']:>5.3f}"
        )
        lines.append(line)

    lines.append(sep)
    out_lines.extend(lines)
    for l in lines:
        print(l)


def print_summary(df: pd.DataFrame, out_lines: list) -> None:
    sep = "=" * 80
    lines = ["", sep, "  SUMMARY — TOP 10 & BOTTOM 5", sep]

    lines.append("\n  TOP 10 FUNDS (Best composite score):")
    lines.append(f"  {'Rank':<5}  {'Scheme':<50}  {'Category':<12}  {'Score':>7}")
    lines.append("  " + "-" * 80)
    for _, r in df.head(10).iterrows():
        lines.append(f"  {r['final_rank']:<5}  {r['scheme_name'][:50]:<50}  "
                     f"{r['category']:<12}  {r['composite_score']:>7.4f}")

    lines.append("\n  BOTTOM 5 FUNDS (Lowest composite score):")
    lines.append(f"  {'Rank':<5}  {'Scheme':<50}  {'Category':<12}  {'Score':>7}")
    lines.append("  " + "-" * 80)
    for _, r in df.tail(5).iterrows():
        lines.append(f"  {r['final_rank']:<5}  {r['scheme_name'][:50]:<50}  "
                     f"{r['category']:<12}  {r['composite_score']:>7.4f}")

    lines.append("")
    lines.append(sep)
    lines.append("  CATEGORY AVERAGES (composite score)")
    lines.append(sep)
    cat = df.groupby("category")["composite_score"].agg(["mean","min","max","count"])
    cat = cat.sort_values("mean", ascending=False)
    lines.append(f"  {'Category':<20}  {'Count':>5}  {'Mean':>7}  {'Min':>7}  {'Max':>7}")
    lines.append("  " + "-" * 55)
    for cat_name, row in cat.iterrows():
        bar = "#" * int(row["mean"] * 30)
        lines.append(f"  {cat_name:<20}  {int(row['count']):>5}  "
                     f"{row['mean']:>7.4f}  {row['min']:>7.4f}  {row['max']:>7.4f}  {bar}")

    lines.append("")
    lines.append(sep)
    lines.append("  PLAN COMPARISON (Regular vs Direct)")
    lines.append(sep)
    plan = df.groupby("plan")["composite_score"].agg(["mean","count"])
    for plan_name, row in plan.iterrows():
        lines.append(f"  {plan_name:<10}  avg score = {row['mean']:.4f}  "
                     f"  n = {int(row['count'])}")

    lines.append("")
    lines.append(sep)
    lines.append("  WEIGHT CONTRIBUTION ANALYSIS (top 10 schemes)")
    lines.append(sep)
    lines.append(f"  {'Scheme':<46}  {'Ret':>5}  {'Shp':>5}  {'Alp':>5}  {'Exp':>5}  {'DD':>5}  {'Total':>7}")
    lines.append("  " + "-" * 85)
    for _, r in df.head(10).iterrows():
        ret_contrib = round(WEIGHTS["return_rank"]  * r["return_rank"],  4)
        shp_contrib = round(WEIGHTS["sharpe_rank"]  * r["sharpe_rank"],  4)
        alp_contrib = round(WEIGHTS["alpha_rank"]   * r["alpha_rank"],   4)
        exp_contrib = round(WEIGHTS["expense_rank"] * r["expense_rank"], 4)
        dd_contrib  = round(WEIGHTS["dd_rank"]      * r["dd_rank"],      4)
        lines.append(
            f"  {r['scheme_name'][:46]:<46}  "
            f"{ret_contrib:>5.3f}  {shp_contrib:>5.3f}  {alp_contrib:>5.3f}  "
            f"{exp_contrib:>5.3f}  {dd_contrib:>5.3f}  {r['composite_score']:>7.4f}"
        )

    out_lines.extend(lines)
    for l in lines:
        print(l)


def print_formula_proof(df: pd.DataFrame, out_lines: list) -> None:
    """Step-by-step proof of score calculation for top-ranked fund."""
    r = df.iloc[0]
    sep = "=" * 70
    lines = [
        "", sep,
        f"  FORMULA PROOF — #{int(r['final_rank'])}  {r['scheme_name'][:55]}",
        sep,
        f"  Metric           Raw Value    Rank       Weight   Contribution",
        "  " + "-" * 65,
        f"  3-Year Return    {r['return_3yr_pct']:>8.2f}%   {r['return_rank']:>6.4f}    × 0.30  = "
            f"{WEIGHTS['return_rank']*r['return_rank']:>7.4f}",
        f"  Sharpe Ratio     {r['sharpe']:>8.4f}    {r['sharpe_rank']:>6.4f}    × 0.25  = "
            f"{WEIGHTS['sharpe_rank']*r['sharpe_rank']:>7.4f}",
        f"  Alpha            {r['alpha']:>8.4f}    {r['alpha_rank']:>6.4f}    × 0.20  = "
            f"{WEIGHTS['alpha_rank']*r['alpha_rank']:>7.4f}",
        f"  Expense Ratio    {r['expense_ratio_pct']:>8.2f}%   {r['expense_rank']:>6.4f}    × 0.15  = "
            f"{WEIGHTS['expense_rank']*r['expense_rank']:>7.4f}  (inverted — lower=better)",
        f"  Max Drawdown     {r['max_drawdown']:>8.2f}%   {r['dd_rank']:>6.4f}    × 0.10  = "
            f"{WEIGHTS['dd_rank']*r['dd_rank']:>7.4f}  (inverted — less negative=better)",
        "  " + "-" * 65,
        f"  Composite Score  {'':>8}    {'':>6}             = {r['composite_score']:>7.4f}",
        sep,
    ]
    out_lines.extend(lines)
    for l in lines:
        print(l)


# ── Main ──────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("Starting fund ranking engine ...")
    df      = load_data()
    df      = compute_ranks(df)
    df      = compute_score(df)

    out_lines = []
    print_full_table(df, out_lines)
    print_summary(df, out_lines)
    print_formula_proof(df, out_lines)

    # Save CSV
    out_csv = PROC_DIR / "fund_ranking.csv"
    df.to_csv(out_csv, index=False)
    log.info("Ranking CSV saved → %s", out_csv)

    # Save report
    out_rpt = RPT_DIR / "fund_ranking_report.txt"
    with open(out_rpt, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    log.info("Ranking report saved → %s", out_rpt)

    log.info("Done. Top fund: #1 = %s (score=%.4f)",
             df.iloc[0]["scheme_name"], df.iloc[0]["composite_score"])


if __name__ == "__main__":
    main()
