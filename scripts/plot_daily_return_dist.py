"""
plot_daily_return_dist.py
--------------------------
Task:
    nav["daily_return_pct"].describe()
    sns.histplot(nav["daily_return_pct"], bins=50, kde=True)
    plt.title("Daily Return Distribution")
    plt.savefig("reports/daily_return_distribution.png")
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend — safe for script execution
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
nav  = pd.read_csv(BASE / "data/processed/nav_history_clean.csv", parse_dates=["date"])
nav  = nav.sort_values(["amfi_code", "date"])

sns.set_theme(style="whitegrid")

# ── 1. Describe ───────────────────────────────────────────────────────────
print("=" * 50)
print("  nav['daily_return_pct'].describe()")
print("=" * 50)
desc = nav["daily_return_pct"].describe()
print(desc.round(6))
print(f"\n  Skewness  : {nav['daily_return_pct'].skew():.4f}")
print(f"  Kurtosis  : {nav['daily_return_pct'].kurt():.4f}")
print(f"  Non-null  : {nav['daily_return_pct'].notna().sum():,}")
print(f"  Null (1st row per scheme): {nav['daily_return_pct'].isna().sum()}")

# ── 2. Plot ───────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel 1 — all schemes combined
sns.histplot(
    nav["daily_return_pct"].dropna(),
    bins=50,
    kde=True,
    ax=axes[0],
    color="steelblue",
    edgecolor="white",
    linewidth=0.3,
)
axes[0].axvline(0, color="black",   linestyle="--", linewidth=0.9, alpha=0.7, label="Zero")
axes[0].axvline(nav["daily_return_pct"].mean(), color="red",
                linestyle="--", linewidth=0.9, label=f"Mean={nav['daily_return_pct'].mean():.3f}%")
axes[0].set_title("Daily Return Distribution — All Schemes")
axes[0].set_xlabel("Daily Return (%)")
axes[0].set_ylabel("Count")
axes[0].legend(fontsize=8)

# Panel 2 — by category (KDE overlay)
eq_cats = ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap"]
palette = ["steelblue", "darkorange", "seagreen", "crimson"]
for cat, col in zip(eq_cats, palette):
    subset = nav[nav["sub_category"] == cat]["daily_return_pct"].dropna()
    if len(subset) > 0:
        sns.kdeplot(subset, ax=axes[1], label=cat, color=col, linewidth=1.5)

axes[1].axvline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.6)
axes[1].set_title("Daily Return KDE — Equity Categories")
axes[1].set_xlabel("Daily Return (%)")
axes[1].set_ylabel("Density")
axes[1].set_xlim(-5, 5)
axes[1].legend(fontsize=8)

plt.suptitle("Daily Return Distribution", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()

out = BASE / "reports/daily_return_distribution.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved → {out}")
