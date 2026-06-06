-- ============================================================
-- queries.sql
-- Bluestock Mutual Fund Analytics Capstone
-- Business analytics queries against bluestock_mf.db
-- ============================================================

-- ── 1. TOP 5 FUNDS BY AUM ─────────────────────────────────
-- Retrieves the five fund houses with the highest total AUM
-- ordered by most recent reporting date.
SELECT
    fund_house,
    MAX(report_date)       AS latest_date,
    SUM(aum_cr)            AS total_aum_crore,
    SUM(aum_lakh_crore)    AS total_aum_lakh_crore,
    SUM(num_schemes)       AS total_schemes
FROM fact_aum
WHERE report_date = (SELECT MAX(report_date) FROM fact_aum)
GROUP BY fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;


-- ── 2. AVERAGE NAV PER SCHEME (LAST 30 DAYS) ─────────────
-- Computes the average, minimum, and maximum NAV for each
-- scheme over the most recent 30 trading days.
SELECT
    fn.amfi_code,
    df.scheme_name,
    df.category,
    ROUND(AVG(fn.nav), 4)  AS avg_nav_30d,
    ROUND(MIN(fn.nav), 4)  AS min_nav_30d,
    ROUND(MAX(fn.nav), 4)  AS max_nav_30d,
    COUNT(*)               AS trading_days
FROM fact_nav fn
JOIN dim_fund df ON fn.amfi_code = df.amfi_code
WHERE fn.date >= DATE('now', '-30 days')
GROUP BY fn.amfi_code, df.scheme_name, df.category
ORDER BY avg_nav_30d DESC;


-- ── 3. MONTHLY SIP INFLOW TRENDS ─────────────────────────
-- Monthly transaction volume for SIP transactions showing
-- growth trend. Uses fact_transaction.
SELECT
    SUBSTR(transaction_date, 1, 7)  AS month,
    COUNT(*)                         AS sip_count,
    ROUND(SUM(amount_inr), 0)        AS total_sip_amount,
    ROUND(AVG(amount_inr), 2)        AS avg_sip_amount
FROM fact_transaction
WHERE transaction_type = 'SIP'
GROUP BY SUBSTR(transaction_date, 1, 7)
ORDER BY month;


-- ── 4. EXPENSE RATIO ANALYSIS ────────────────────────────
-- Compares average expense ratio across categories and
-- fund houses. Identifies the cheapest and most expensive.
SELECT
    df.category,
    df.fund_house,
    COUNT(*)                              AS num_schemes,
    ROUND(AVG(fp.expense_ratio_pct), 4)   AS avg_expense_ratio,
    ROUND(MIN(fp.expense_ratio_pct), 4)   AS min_expense_ratio,
    ROUND(MAX(fp.expense_ratio_pct), 4)   AS max_expense_ratio
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
GROUP BY df.category, df.fund_house
ORDER BY avg_expense_ratio ASC;


-- ── 5. TRANSACTION ANALYSIS BY STATE & CITY TIER ─────────
-- Ranks states by total investment volume and shows
-- T30 vs B30 split.
SELECT
    state,
    city_tier,
    COUNT(*)                              AS transaction_count,
    ROUND(SUM(amount_inr), 0)             AS total_amount,
    ROUND(AVG(amount_inr), 2)             AS avg_amount,
    ROUND(SUM(amount_inr) * 100.0 /
          (SELECT SUM(amount_inr) FROM fact_transaction), 2)
                                          AS pct_of_total
FROM fact_transaction
GROUP BY state, city_tier
ORDER BY total_amount DESC
LIMIT 20;


-- ── 6. TOP 10 FUNDS BY SHARPE RATIO ──────────────────────
SELECT
    fp.amfi_code,
    df.scheme_name,
    df.category,
    df.fund_house,
    ROUND(fp.sharpe_ratio, 4)       AS sharpe_ratio,
    ROUND(fp.return_3yr_pct, 2)     AS return_3yr_pct,
    ROUND(fp.alpha, 4)              AS alpha,
    ROUND(fp.expense_ratio_pct, 2)  AS expense_ratio_pct
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
ORDER BY fp.sharpe_ratio DESC
LIMIT 10;


-- ── 7. RISK vs RETURN BY CATEGORY ────────────────────────
SELECT
    df.category,
    COUNT(*)                              AS num_funds,
    ROUND(AVG(fp.return_3yr_pct), 2)      AS avg_return_3yr,
    ROUND(AVG(fp.std_dev_ann_pct), 2)     AS avg_volatility,
    ROUND(AVG(fp.sharpe_ratio), 4)        AS avg_sharpe,
    ROUND(AVG(fp.max_drawdown_pct), 2)    AS avg_max_drawdown,
    ROUND(AVG(fp.alpha), 4)               AS avg_alpha
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
GROUP BY df.category
ORDER BY avg_sharpe DESC;


-- ── 8. REGULAR vs DIRECT PLAN COMPARISON ────────────────
SELECT
    df.category,
    df.risk_category,
    SUM(CASE WHEN df.sub_category LIKE '%Regular%'
             OR fp.amfi_code IN (
                 SELECT amfi_code FROM dim_fund WHERE sub_category = 'Regular'
             ) THEN 1 ELSE 0 END) AS regular_count,
    ROUND(AVG(CASE WHEN df.sub_category = 'Regular'
                   THEN fp.expense_ratio_pct END), 4) AS avg_expense_regular,
    ROUND(AVG(CASE WHEN df.sub_category = 'Direct'
                   THEN fp.expense_ratio_pct END), 4) AS avg_expense_direct,
    ROUND(AVG(CASE WHEN df.sub_category = 'Regular'
                   THEN fp.return_3yr_pct END), 2)    AS avg_return_regular,
    ROUND(AVG(CASE WHEN df.sub_category = 'Direct'
                   THEN fp.return_3yr_pct END), 2)    AS avg_return_direct
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
GROUP BY df.category, df.risk_category
ORDER BY df.category;


-- ── 9. INVESTOR DEMOGRAPHICS ANALYSIS ───────────────────
SELECT
    age_group,
    gender,
    COUNT(*)                              AS transaction_count,
    ROUND(SUM(amount_inr), 0)             AS total_invested,
    ROUND(AVG(amount_inr), 2)             AS avg_investment,
    ROUND(SUM(CASE WHEN transaction_type = 'SIP'
                   THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                          AS sip_pct
FROM fact_transaction
GROUP BY age_group, gender
ORDER BY total_invested DESC;


-- ── 10. NAV PERFORMANCE VS BENCHMARK (NIFTY 50) ──────────
-- Computes cumulative NAV return for each scheme from
-- the first available date to the most recent date.
SELECT
    fn.amfi_code,
    df.scheme_name,
    df.category,
    MIN(fn.date)                          AS start_date,
    MAX(fn.date)                          AS end_date,
    ROUND(
        (MAX(CASE WHEN fn.date = (
            SELECT MAX(date) FROM fact_nav WHERE amfi_code = fn.amfi_code)
        THEN fn.nav END) /
        MAX(CASE WHEN fn.date = (
            SELECT MIN(date) FROM fact_nav WHERE amfi_code = fn.amfi_code)
        THEN fn.nav END) - 1) * 100, 2
    )                                     AS total_return_pct,
    COUNT(DISTINCT fn.date)               AS trading_days
FROM fact_nav fn
JOIN dim_fund df ON fn.amfi_code = df.amfi_code
GROUP BY fn.amfi_code, df.scheme_name, df.category
ORDER BY total_return_pct DESC;
