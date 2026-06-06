"""Reusable financial metric calculations for mutual fund analytics.

Return inputs must be periodic decimal returns (for example, ``0.01`` for
1%). Functions return decimal values unless the metric is unitless.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeAlias

import numpy as np
import pandas as pd


DEFAULT_RISK_FREE_RATE = 0.065
DEFAULT_PERIODS_PER_YEAR = 252
NumberSeries: TypeAlias = pd.Series | Iterable[float]

__all__ = [
    "calculate_cagr",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_alpha",
    "calculate_beta",
    "calculate_max_drawdown",
    "calculate_tracking_error",
    "calculate_information_ratio",
]


def _validate_periods_per_year(periods_per_year: int) -> None:
    if isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int):
        raise TypeError("periods_per_year must be an integer.")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero.")


def _as_numeric_series(values: NumberSeries, name: str) -> pd.Series:
    if isinstance(values, pd.Series):
        series = values.copy()
    else:
        if isinstance(values, (str, bytes)):
            raise TypeError(f"{name} must be a one-dimensional numeric iterable.")
        try:
            series = pd.Series(values, dtype="float64")
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"{name} must be a one-dimensional numeric iterable."
            ) from exc

    try:
        series = pd.to_numeric(series, errors="raise").astype("float64")
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must contain only numeric values.") from exc

    series = series.replace([np.inf, -np.inf], np.nan).dropna()
    if series.empty:
        raise ValueError(f"{name} must contain at least one finite value.")
    return series


def _align_returns(
    fund_returns: NumberSeries,
    benchmark_returns: NumberSeries,
    *,
    minimum_observations: int = 2,
) -> tuple[pd.Series, pd.Series]:
    if isinstance(fund_returns, pd.Series) and isinstance(
        benchmark_returns, pd.Series
    ):
        aligned = pd.concat(
            [
                pd.to_numeric(fund_returns, errors="coerce").rename("fund"),
                pd.to_numeric(benchmark_returns, errors="coerce").rename(
                    "benchmark"
                ),
            ],
            axis=1,
            join="inner",
        )
    else:
        if isinstance(fund_returns, (str, bytes)) or isinstance(
            benchmark_returns, (str, bytes)
        ):
            raise TypeError("Return inputs must be numeric iterables.")
        try:
            fund = pd.Series(fund_returns, dtype="float64")
            benchmark = pd.Series(benchmark_returns, dtype="float64")
        except (TypeError, ValueError) as exc:
            raise TypeError("Return inputs must be numeric iterables.") from exc
        if len(fund) != len(benchmark):
            raise ValueError(
                "fund_returns and benchmark_returns must have equal lengths."
            )
        aligned = pd.DataFrame(
            {
                "fund": fund.to_numpy(),
                "benchmark": benchmark.to_numpy(),
            }
        )

    aligned = aligned.replace([np.inf, -np.inf], np.nan).dropna()
    if len(aligned) < minimum_observations:
        raise ValueError(
            "At least "
            f"{minimum_observations} aligned observations are required."
        )
    return aligned["fund"], aligned["benchmark"]


def calculate_cagr(
    data: pd.DataFrame,
    *,
    nav_column: str = "nav",
    date_column: str = "date",
    days_per_year: float = 365.0,
) -> float:
    """Calculate compound annual growth rate from a dated NAV history.

    The result is a decimal, so ``0.12`` represents 12%. The first and last
    valid NAV observations after date sorting are used.

    Raises:
        TypeError: If ``data`` is not a pandas DataFrame.
        ValueError: If required data is missing, non-positive, or spans no time.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame.")
    missing_columns = {nav_column, date_column}.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    if not np.isfinite(days_per_year) or days_per_year <= 0:
        raise ValueError("days_per_year must be a positive finite number.")

    frame = data[[date_column, nav_column]].copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    frame[nav_column] = pd.to_numeric(frame[nav_column], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    frame = frame.sort_values(date_column)

    if len(frame) < 2:
        raise ValueError("At least two valid dated NAV observations are required.")
    if (frame[nav_column] <= 0).any():
        raise ValueError("NAV values must be greater than zero.")

    elapsed_days = (frame[date_column].iloc[-1] - frame[date_column].iloc[0]).days
    if elapsed_days <= 0:
        raise ValueError("NAV history must span more than zero days.")

    years = elapsed_days / days_per_year
    start_nav = float(frame[nav_column].iloc[0])
    end_nav = float(frame[nav_column].iloc[-1])
    return float((end_nav / start_nav) ** (1.0 / years) - 1.0)


def calculate_sharpe_ratio(
    returns: NumberSeries,
    *,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float:
    """Calculate the annualized Sharpe ratio from periodic decimal returns.

    Returns ``numpy.nan`` when annualized volatility is effectively zero.
    """
    _validate_periods_per_year(periods_per_year)
    if not np.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")
    values = _as_numeric_series(returns, "returns")
    if len(values) < 2:
        raise ValueError("At least two valid return observations are required.")

    annual_return = values.mean() * periods_per_year
    annual_volatility = values.std(ddof=1) * np.sqrt(periods_per_year)
    if np.isclose(annual_volatility, 0.0):
        return float("nan")
    return float((annual_return - risk_free_rate) / annual_volatility)


def calculate_sortino_ratio(
    returns: NumberSeries,
    *,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    minimum_acceptable_return: float = 0.0,
) -> float:
    """Calculate the annualized Sortino ratio using downside observations.

    Day 4 used returns below zero as downside. The
    ``minimum_acceptable_return`` parameter retains that default while
    allowing another periodic threshold. Returns ``numpy.nan`` when fewer
    than two downside observations exist or downside deviation is zero.
    """
    _validate_periods_per_year(periods_per_year)
    if not np.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")
    if not np.isfinite(minimum_acceptable_return):
        raise ValueError("minimum_acceptable_return must be finite.")
    values = _as_numeric_series(returns, "returns")
    if len(values) < 2:
        raise ValueError("At least two valid return observations are required.")

    downside = values[values < minimum_acceptable_return]
    if len(downside) < 2:
        return float("nan")
    downside_deviation = downside.std(ddof=1) * np.sqrt(periods_per_year)
    if np.isclose(downside_deviation, 0.0):
        return float("nan")

    annual_return = values.mean() * periods_per_year
    return float((annual_return - risk_free_rate) / downside_deviation)


def calculate_beta(
    fund_returns: NumberSeries,
    benchmark_returns: NumberSeries,
) -> float:
    """Calculate OLS beta from aligned periodic fund and benchmark returns.

    Returns ``numpy.nan`` when benchmark variance is effectively zero.
    """
    fund, benchmark = _align_returns(fund_returns, benchmark_returns)
    benchmark_variance = benchmark.var(ddof=1)
    if np.isclose(benchmark_variance, 0.0):
        return float("nan")
    covariance = fund.cov(benchmark)
    return float(covariance / benchmark_variance)


def calculate_alpha(
    fund_returns: NumberSeries,
    benchmark_returns: NumberSeries,
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float:
    """Calculate annualized OLS alpha from aligned periodic returns.

    This matches the Day 4 regression convention: daily intercept multiplied
    by 252. Returns ``numpy.nan`` when beta is undefined.
    """
    _validate_periods_per_year(periods_per_year)
    fund, benchmark = _align_returns(fund_returns, benchmark_returns)
    beta = calculate_beta(fund, benchmark)
    if np.isnan(beta):
        return float("nan")
    periodic_alpha = fund.mean() - beta * benchmark.mean()
    return float(periodic_alpha * periods_per_year)


def calculate_max_drawdown(
    data: pd.DataFrame | NumberSeries,
    *,
    nav_column: str = "nav",
    date_column: str = "date",
) -> float:
    """Calculate the deepest peak-to-trough decline in a NAV series.

    A DataFrame is sorted by ``date_column`` before calculation. A plain
    series or iterable is assumed to already be chronological. The result is
    a non-positive decimal, such as ``-0.20`` for a 20% drawdown.
    """
    if isinstance(data, pd.DataFrame):
        if nav_column not in data.columns:
            raise ValueError(f"data is missing required column: {nav_column}")
        frame = data.copy()
        if date_column in frame.columns:
            frame[date_column] = pd.to_datetime(
                frame[date_column], errors="coerce"
            )
            frame = frame.dropna(subset=[date_column]).sort_values(date_column)
        nav = _as_numeric_series(frame[nav_column], nav_column)
    else:
        nav = _as_numeric_series(data, "nav")

    if (nav <= 0).any():
        raise ValueError("NAV values must be greater than zero.")
    running_max = nav.cummax()
    drawdowns = nav.div(running_max).sub(1.0)
    return float(drawdowns.min())


def calculate_tracking_error(
    fund_returns: NumberSeries,
    benchmark_returns: NumberSeries,
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float:
    """Calculate annualized tracking error of active periodic returns."""
    _validate_periods_per_year(periods_per_year)
    fund, benchmark = _align_returns(fund_returns, benchmark_returns)
    active_returns = fund - benchmark
    return float(active_returns.std(ddof=1) * np.sqrt(periods_per_year))


def calculate_information_ratio(
    fund_returns: NumberSeries,
    benchmark_returns: NumberSeries,
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float:
    """Calculate annualized active return divided by tracking error.

    Returns ``numpy.nan`` when tracking error is effectively zero.
    """
    _validate_periods_per_year(periods_per_year)
    fund, benchmark = _align_returns(fund_returns, benchmark_returns)
    tracking_error = calculate_tracking_error(
        fund,
        benchmark,
        periods_per_year=periods_per_year,
    )
    if np.isclose(tracking_error, 0.0):
        return float("nan")
    annual_active_return = (fund - benchmark).mean() * periods_per_year
    return float(annual_active_return / tracking_error)
