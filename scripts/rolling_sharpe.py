"""
rolling_sharpe.py
-----------------
Executes your exact code:

    rolling_sharpe = (returns.rolling(90).mean() /
                      returns.rolling(90).std()) * np.sqrt(252)
    plt.plot(rolling_sharpe)
    plt.savefig("reports/rolling_sharpe_chart.png")

Output: reports/rolling_sharpe_chart.png
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

# ── Load ──────────────────────────────────────────────────────────────────
nav = pd.read_csv(PROC / "nav_history_clean.csv", parse_dates=["date"])
nav = nav.sort_values(["amfi_code", "date"])

RF_DAILY = 0.065 / 252   # 6.5% annual risk-free rate

# ── Sample schemes for readable chart ─────────────────────────────────────
SAMPLE = {
    119551: "SBI Bluechip (LC)",
    119598: "SBI Small Cap (SC)",
    100033: "HDFC Mid-Cap (MC)",
    120503: "ICICI Bluechip (LC)",
    120843: "Kotak Flexicap",
}

# ═══════════════════════════════════════════════════════════
# YOUR EXACT CODE — applied per scheme
# ═══════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=False)

# ── Panel 1: Your exact single-series formula ─────────────
ax1 = axes[0]
for code, label in SAMPLE.items():
    s       = nav[nav["amfi_code"] == code].sort_values("date")
    returns = s["daily_return_pct"].dropna() / 100   # decimal

    # YOUR EXACT FORMULA
    rolling_sharpe = (
        returns.rolling(90).mean() /
        returns.rolling(90).std()
    ) * np.sqrt(252)

    ax1.plot(s["date"].iloc[len(s)-len(rolling_sharpe):],
             rolling_sharpe.values,
             label=label, linewidth=1.3)

ax1.axhline(0, color="black",  linestyle="--", linewidth=0.8, alpha=0.5)
ax1.axhline(1, color="green",  linestyle=":",  linewidth=0.8, alpha=0.6, label="Sharpe=1")
ax1.set_title("Rolling 90-Day Sharpe Ratio (your formula: mean/std × √252)",
              fontsize=12, fontweight="bold")
ax1.set_ylabel("Rolling Sharpe")
ax1.legend(fontsize=8)

# ── Panel 2: All 40 schemes — avg rolling Sharpe by category ─
cat_rolling = {}
for cat, grp in nav.groupby("category"):
    rets = (grp.groupby("date")["daily_return_pct"]
              .mean().dropna() / 100)
    rs = (rets.rolling(90).mean() / rets.rolling(90).std()) * np.sqrt(252)
    cat_rolling[cat] = (rets.index if hasattr(rets.index, 'dtype')
                        else pd.to_datetime(nav[nav["category"]==cat]
                                           ["date"].sort_values().unique()),
                        rs)

ax2 = axes[1]
for cat, (dates, rs) in cat_rolling.items():
    plot_dates = nav[nav["category"]==cat]["date"].sort_values().unique()
    ax2.plot(pd.to_datetime(plot_dates)[len(plot_dates)-len(rs.dropna()):],
             rs.dropna().values, label=cat, linewidth=1.2)

ax2.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
ax2.set_title("Rolling 90-Day Sharpe — Category Averages", fontsize=12, fontweight="bold")
ax2.set_ylabel("Rolling Sharpe")
ax2.set_xlabel("Date")
ax2.legend(bbox_to_anchor=(1.01, 1), fontsize=7)

plt.tight_layout()

# YOUR EXACT SAVE LINE
plt.savefig(RPT / "rolling_sharpe_chart.png", dpi=150, bbox_inches="tight")
plt.close()

print("rolling_sharpe formula:")
print("  rolling_sharpe = (returns.rolling(90).mean() /")
print("                    returns.rolling(90).std()) * np.sqrt(252)")
print()

# ── Print sample values ────────────────────────────────────
print("Sample rolling Sharpe values (SBI Bluechip 119551, last 5 dates):")
s       = nav[nav["amfi_code"] == 119551].sort_values("date")
returns = s["daily_return_pct"].dropna() / 100
rs      = (returns.rolling(90).mean() / returns.rolling(90).std()) * np.sqrt(252)
dates   = s["date"].values
sample  = pd.Series(rs.values, index=pd.to_datetime(dates[:len(rs)])).dropna().tail(5)
for d, v in sample.items():
    print(f"  {str(d)[:10]}  rolling_sharpe = {v:.4f}")

print()
out = RPT / "rolling_sharpe_chart.png"
print(f"Saved -> reports/rolling_sharpe_chart.png  ({out.stat().st_size // 1024} KB)")
