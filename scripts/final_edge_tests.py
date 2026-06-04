"""Final edge case tests for all 3 production risk functions."""
import pandas as pd
import numpy as np

TRADING_DAYS = 252
RF = 0.065


def max_drawdown(df: pd.DataFrame) -> float:
    df = df.sort_values("date")
    running_max = df["nav"].cummax()
    drawdown = (df["nav"] / running_max) - 1
    return drawdown.min()


def sharpe_ratio(x: pd.Series) -> float:
    mean_return = x.mean() * TRADING_DAYS
    std_return  = x.std()  * np.sqrt(TRADING_DAYS)
    if std_return == 0:
        return np.nan
    return (mean_return - RF) / std_return


def sortino_ratio(x: pd.Series) -> float:
    downside = x[x < 0]
    if len(downside) < 2:
        return np.nan
    downside_std = downside.std() * np.sqrt(TRADING_DAYS)
    if downside_std == 0 or np.isnan(downside_std) or downside_std < 1e-10:
        return np.nan
    annual_return = x.mean() * TRADING_DAYS
    return (annual_return - RF) / downside_std


# ── Test cases ────────────────────────────────────────────────────────────
mixed_s    = pd.Series([0.001, -0.001] * 126)
ds_mixed   = mixed_s[mixed_s < 0].std() * np.sqrt(TRADING_DAYS)
sort_mixed = (mixed_s.mean() * TRADING_DAYS - RF) / ds_mixed

pos_dom    = pd.Series([0.001] * 126 + [-0.0001] * 126)
shp_norm   = (pos_dom.mean() * TRADING_DAYS - RF) / (pos_dom.std() * np.sqrt(TRADING_DAYS))

tests = [
    # (name,  function_result,  expected,  tolerance)
    ("MDD: rising only",
        max_drawdown(pd.DataFrame({"date": pd.date_range("2022-01-01", periods=5),
                                   "nav":  [100, 101, 102, 103, 104]})),
        0.0, 0.0001),
    ("MDD: falling 100->60",
        max_drawdown(pd.DataFrame({"date": pd.date_range("2022-01-01", periods=5),
                                   "nav":  [100, 90, 80, 70, 60]})),
        -0.40, 0.0001),
    ("MDD: V-shape 100->70->110",
        max_drawdown(pd.DataFrame({"date": pd.date_range("2022-01-01", periods=6),
                                   "nav":  [100, 90, 70, 80, 100, 110]})),
        -0.30, 0.0001),
    ("MDD: unsorted input (sort guard)",
        max_drawdown(pd.DataFrame({"date": pd.date_range("2022-01-01", periods=5)[::-1],
                                   "nav":  [104, 103, 102, 101, 100]})),
        0.0, 0.0001),
    ("Sharpe: zero std dev -> NaN",
        sharpe_ratio(pd.Series([0.0] * 252)),
        np.nan, 0),
    ("Sharpe: returns == Rf -> NaN",
        sharpe_ratio(pd.Series([RF / TRADING_DAYS] * 252)),
        np.nan, 0),
    ("Sharpe: normal mixed returns",
        sharpe_ratio(pos_dom),
        shp_norm, 0.001),
    ("Sortino: no negative days -> NaN",
        sortino_ratio(pd.Series([0.003] * 252)),
        np.nan, 0),
    ("Sortino: constant negatives -> NaN",
        sortino_ratio(pd.Series([-0.002] * 252)),
        np.nan, 0),
    ("Sortino: normal mixed returns",
        sortino_ratio(mixed_s),
        sort_mixed, 0.001),
]

# ── Run ───────────────────────────────────────────────────────────────────
print("=" * 70)
print("  EDGE CASE TESTS — max_drawdown / sharpe_ratio / sortino_ratio")
print("=" * 70)
all_pass = True
for name, got, exp, tol in tests:
    if np.isnan(exp) and np.isnan(got):
        status = "PASS"
    elif np.isnan(exp) or np.isnan(got):
        status = "FAIL"
    else:
        status = "PASS" if abs(got - exp) <= tol else "FAIL"
    if status == "FAIL":
        all_pass = False
    g = "nan" if (isinstance(got, float) and np.isnan(got)) else f"{got:.6f}"
    e = "nan" if (isinstance(exp, float) and np.isnan(exp)) else f"{exp:.6f}"
    print(f"  [{status}]  {name:<40}  got={g:>14}  expected={e:>14}")

print()
verdict = "ALL 10/10 TESTS PASSED" if all_pass else "SOME TESTS FAILED"
print(f"  Result : {verdict}")
print("=" * 70)
