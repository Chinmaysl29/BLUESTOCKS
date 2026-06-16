"""
run_recommender.py
------------------
Runs the recommendation engine for all 3 risk profiles:

    recommend("Low")      -- risk_grade <= 2
    recommend("Moderate") -- risk_grade <= 4
    recommend("High")     -- all funds

Note: The recommender uses "Medium" internally for <= 4.
      "Moderate" is mapped as an alias.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recommender import recommend, PROFILE_RISK_LIMITS

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

SEP = "=" * 75

PROFILES = [
    ("Low",      "risk_score <= 2  (Low risk funds only)"),
    ("Medium",   "risk_score <= 4  (Low + Moderate risk)"),
    ("High",     "all funds        (no risk filter)"),
]

results = {}

for profile, rule in PROFILES:
    print(SEP)
    print(f'  recommend("{profile}")  |  Filter: {rule}')
    print(SEP)
    try:
        df = recommend(profile)
        results[profile] = df
        print(df[[
            "recommendation_rank",
            "scheme_name",
            "category",
            "risk_grade",
            "fund_score_100",
            "sharpe_ratio",
            "return_3yr_pct",
        ]].to_string(index=False))
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

# ── Comparison summary ────────────────────────────────────────────────────
print(SEP)
print("  RECOMMENDATION SUMMARY — TOP FUND PER PROFILE")
print(SEP)
print(f"  {'Profile':<10}  {'Top Fund':<55}  {'Score':>8}  {'3Y Ret':>7}")
print("  " + "-" * 85)
for profile, _ in PROFILES:
    if profile in results and len(results[profile]) > 0:
        top = results[profile].iloc[0]
        print(f"  {profile:<10}  {top['scheme_name'][:55]:<55}  "
              f"{top['fund_score_100']:>8.2f}  {top['return_3yr_pct']:>6.2f}%")
print()
print(SEP)
print("  RISK FILTER LOGIC")
print(SEP)
print("  Low      -- risk_score <= 2  (Low risk funds only)")
print("             Includes: Low, Moderately Low")
print("  Medium   -- risk_score <= 4  (Low + Moderate risk)")
print("             Includes: Low, Moderately Low, Moderate, Moderately High")
print("  High     -- All 40 funds, no filter applied")
print(SEP)
