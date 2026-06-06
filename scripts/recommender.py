"""Risk-profile-based mutual fund recommendation engine.

The engine uses the existing Day 4 fund scorecard and performance datasets.
Eligible funds are ranked by fund score, Sharpe ratio, and three-year return.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd


BASE_DIR: Final = Path(__file__).resolve().parent.parent
DEFAULT_SCORECARD_PATH: Final = BASE_DIR / "data" / "processed" / "fund_scorecard.csv"
DEFAULT_PERFORMANCE_PATH: Final = (
    BASE_DIR / "data" / "processed" / "performance_clean.csv"
)

PROFILE_RISK_LIMITS: Final[dict[str, int | None]] = {
    "Low": 2,
    "Medium": 4,
    "High": None,
}
RANKING_COLUMNS: Final[list[str]] = [
    "fund_score_100",
    "sharpe_ratio",
    "return_3yr_pct",
]
OUTPUT_COLUMNS: Final[list[str]] = [
    "recommendation_rank",
    "amfi_code",
    "scheme_name",
    "fund_house",
    "category",
    "plan",
    "risk_grade",
    "risk_score",
    "fund_score_100",
    "sharpe_ratio",
    "return_3yr_pct",
]


def _normalize_risk_profile(risk_profile: str) -> str:
    """Return the canonical risk-profile label."""
    if not isinstance(risk_profile, str):
        raise TypeError("risk_profile must be a string.")

    normalized = risk_profile.strip().casefold()
    profiles = {profile.casefold(): profile for profile in PROFILE_RISK_LIMITS}
    if normalized not in profiles:
        allowed = ", ".join(PROFILE_RISK_LIMITS)
        raise ValueError(f"risk_profile must be one of: {allowed}.")
    return profiles[normalized]


def _load_recommendation_data(
    scorecard_path: str | Path,
    performance_path: str | Path,
) -> pd.DataFrame:
    """Load and combine scorecard metrics with numeric risk scores."""
    scorecard_file = Path(scorecard_path)
    performance_file = Path(performance_path)

    for file_path in (scorecard_file, performance_file):
        if not file_path.is_file():
            raise FileNotFoundError(f"Required dataset not found: {file_path}")

    try:
        scorecard = pd.read_csv(scorecard_file)
        performance = pd.read_csv(performance_file)
    except (OSError, pd.errors.ParserError) as exc:
        raise ValueError(f"Unable to read recommendation datasets: {exc}") from exc

    scorecard_required = {
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "plan",
        *RANKING_COLUMNS,
    }
    performance_required = {"amfi_code", "risk_grade", "risk_score"}

    missing_scorecard = scorecard_required.difference(scorecard.columns)
    missing_performance = performance_required.difference(performance.columns)
    if missing_scorecard:
        raise ValueError(
            "Scorecard is missing columns: "
            + ", ".join(sorted(missing_scorecard))
        )
    if missing_performance:
        raise ValueError(
            "Performance data is missing columns: "
            + ", ".join(sorted(missing_performance))
        )
    if scorecard["amfi_code"].duplicated().any():
        raise ValueError("Scorecard contains duplicate amfi_code values.")
    if performance["amfi_code"].duplicated().any():
        raise ValueError("Performance data contains duplicate amfi_code values.")

    risk_data = performance[["amfi_code", "risk_grade", "risk_score"]]
    combined = scorecard.merge(
        risk_data,
        on="amfi_code",
        how="left",
        validate="one_to_one",
    )

    numeric_columns = [*RANKING_COLUMNS, "risk_score"]
    combined[numeric_columns] = combined[numeric_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )
    if combined[numeric_columns].isna().any().any():
        invalid = combined.loc[
            combined[numeric_columns].isna().any(axis=1),
            "amfi_code",
        ].tolist()
        raise ValueError(
            "Missing or invalid recommendation metrics for AMFI codes: "
            + ", ".join(map(str, invalid))
        )

    return combined


def recommend(
    risk_profile: str,
    *,
    top_n: int = 5,
    scorecard_path: str | Path = DEFAULT_SCORECARD_PATH,
    performance_path: str | Path = DEFAULT_PERFORMANCE_PATH,
) -> pd.DataFrame:
    """Return the top mutual funds for a Low, Medium, or High risk profile.

    Eligibility:
        Low: numeric risk score <= 2.
        Medium: numeric risk score <= 4.
        High: all funds.

    Eligible funds are sorted descending by fund score, Sharpe ratio, and
    three-year return. The returned DataFrame contains at most ``top_n`` rows.

    Raises:
        TypeError: If argument types are invalid.
        ValueError: If the profile, datasets, or ranking data are invalid.
        FileNotFoundError: If a required processed dataset is absent.
    """
    profile = _normalize_risk_profile(risk_profile)
    if isinstance(top_n, bool) or not isinstance(top_n, int):
        raise TypeError("top_n must be an integer.")
    if top_n <= 0:
        raise ValueError("top_n must be greater than zero.")

    funds = _load_recommendation_data(scorecard_path, performance_path)
    risk_limit = PROFILE_RISK_LIMITS[profile]
    if risk_limit is not None:
        funds = funds.loc[funds["risk_score"] <= risk_limit]
    if funds.empty:
        raise ValueError(f"No funds are eligible for the {profile} risk profile.")

    recommendations = (
        funds.sort_values(
            RANKING_COLUMNS,
            ascending=[False, False, False],
            kind="mergesort",
        )
        .head(top_n)
        .copy()
    )
    recommendations.insert(
        0,
        "recommendation_rank",
        range(1, len(recommendations) + 1),
    )
    recommendations["risk_score"] = recommendations["risk_score"].astype(int)
    return recommendations[OUTPUT_COLUMNS].reset_index(drop=True)


def _print_recommendations(risk_profile: str) -> None:
    """Print a concise recommendation table for command-line use."""
    recommendations = recommend(risk_profile)
    print(f"\n{risk_profile} Risk - Top {len(recommendations)} Funds")
    print(
        recommendations[
            [
                "recommendation_rank",
                "scheme_name",
                "risk_grade",
                "fund_score_100",
                "sharpe_ratio",
                "return_3yr_pct",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    for requested_profile in PROFILE_RISK_LIMITS:
        _print_recommendations(requested_profile)
