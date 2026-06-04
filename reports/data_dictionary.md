# Data Dictionary

| Column Name | Data Type | Meaning | Source File |
|---|---:|---|---|
| `fund_key` | INTEGER | Surrogate primary key for a mutual fund scheme. | `dim_fund` |
| `amfi_code` | TEXT | AMFI or scheme code used to identify a mutual fund. | `data/clean/02_nav_history.csv`, `data/clean/07_scheme_performance.csv`, `data/clean/08_investor_transactions.csv`, `data/clean/06_aum.csv` |
| `scheme_name` | TEXT | Name of the mutual fund scheme. | Source files with `scheme_name` or `fund_name` |
| `category` | TEXT | Broad fund category. | Source files with `category` |
| `sub_category` | TEXT | More specific fund category. | Source files with `sub_category` or `subcategory` |
| `date_key` | INTEGER | Date surrogate key in `YYYYMMDD` format. | `dim_date` |
| `date_value` | TEXT | Calendar date in `YYYY-MM-DD` format. | All cleaned source files with date columns |
| `year` | INTEGER | Calendar year extracted from date. | Derived from source date columns |
| `quarter` | INTEGER | Calendar quarter extracted from date. | Derived from source date columns |
| `month` | INTEGER | Calendar month extracted from date. | Derived from source date columns |
| `day` | INTEGER | Calendar day extracted from date. | Derived from source date columns |
| `nav_key` | INTEGER | Surrogate primary key for NAV fact records. | `fact_nav` |
| `nav` | REAL | Net Asset Value of the scheme on a given date. Must be greater than 0. | `data/clean/02_nav_history.csv` |
| `transaction_key` | INTEGER | Surrogate primary key for investor transaction records. | `fact_transaction` |
| `investor_id` | TEXT | Investor identifier, PAN, or folio number when available. | `data/clean/08_investor_transactions.csv` |
| `transaction_type` | TEXT | Type of transaction, such as SIP, purchase, redemption, or switch. | `data/clean/08_investor_transactions.csv` |
| `amount` | REAL | Transaction amount. Must be greater than 0. | `data/clean/08_investor_transactions.csv` |
| `units` | REAL | Number of fund units involved in the transaction. | `data/clean/08_investor_transactions.csv` |
| `kyc_status` | TEXT | Investor KYC status enum, such as verified, pending, rejected, or not available. | `data/clean/08_investor_transactions.csv` |
| `performance_key` | INTEGER | Surrogate primary key for scheme performance records. | `fact_performance` |
| `period` | TEXT | Performance period label when provided. | `data/clean/07_scheme_performance.csv` |
| `return_1m` | REAL | One-month scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_3m` | REAL | Three-month scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_6m` | REAL | Six-month scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_1y` | REAL | One-year scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_3y` | REAL | Three-year scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_5y` | REAL | Five-year scheme return percentage. | `data/clean/07_scheme_performance.csv` |
| `return_since_inception` | REAL | Return percentage since scheme inception. | `data/clean/07_scheme_performance.csv` |
| `benchmark_return` | REAL | Benchmark return percentage for comparison. | `data/clean/07_scheme_performance.csv` |
| `aum_key` | INTEGER | Surrogate primary key for AUM fact records. | `fact_aum` |
| `aum` | REAL | Assets under management for a fund on a given date. Must be greater than or equal to 0. | `data/clean/06_aum.csv` |

## Tables

| Table Name | Meaning |
|---|---|
| `dim_fund` | Fund dimension containing scheme-level descriptive attributes. |
| `dim_date` | Date dimension used by all fact tables. |
| `fact_nav` | Daily or periodic NAV values by fund. |
| `fact_transaction` | Investor transaction activity by date and fund when fund mapping is available. |
| `fact_performance` | Fund performance return metrics by period and date. |
| `fact_aum` | Assets under management by fund and date. |
