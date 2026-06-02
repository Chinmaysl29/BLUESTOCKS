"""
validate_amfi_codes.py
----------------------
Checks that every AMFI code in 01_fund_master.csv
has a corresponding NAV history in 02_nav_history.csv.
"""

import pandas as pd
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "raw"

fund_master = pd.read_csv(RAW / "01_fund_master.csv")
nav_history = pd.read_csv(RAW / "02_nav_history.csv")

master_codes = set(fund_master["amfi_code"])
nav_codes    = set(nav_history["amfi_code"])

missing_codes = master_codes - nav_codes
extra_codes   = nav_codes - master_codes   # codes in NAV but not in master

print("=" * 50)
print("AMFI VALIDATION REPORT")
print("=" * 50)
print(f"Fund Master Codes : {len(master_codes)}")
print(f"NAV History Codes : {len(nav_codes)}")
print(f"\nMissing in NAV    : {len(missing_codes)}")
print(f"Extra in NAV      : {len(extra_codes)}")

if len(missing_codes) == 0:
    print("\nValidation PASSED — all master codes have NAV history.")
else:
    print("\nMissing AMFI Codes (in master but no NAV history):")
    # Show with scheme name for context
    missing_df = fund_master[fund_master["amfi_code"].isin(missing_codes)][
        ["amfi_code", "scheme_name", "fund_house", "category"]
    ].sort_values("amfi_code")
    print(missing_df.to_string(index=False))

if len(extra_codes) > 0:
    print("\nExtra AMFI Codes (NAV history exists but not in master):")
    print(sorted(extra_codes))
