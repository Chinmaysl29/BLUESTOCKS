# Dashboard — bluestock_mf.pbix

## Power BI Dashboard Specification

**File:** `bluestock_mf.pbix`

### Page 1 — Overview
| Visual | Metric |
|---|---|
| KPI Card | Total Funds (40) |
| KPI Card | Total AUM (₹ lakh crore) |
| KPI Card | Average 3-Year Return (%) |
| Table | Top 10 Funds by Score |
| Bar Chart | AUM by Fund House |
| Slicer | Category, Plan, Fund House |

### Page 2 — Performance Analytics
| Visual | Metric |
|---|---|
| Scatter Plot | Risk (Std Dev) vs Return (3Y) |
| Bar Chart | Alpha by Scheme |
| Bar Chart | Beta by Scheme |
| Histogram | Sharpe Ratio Distribution |
| Line Chart | Rolling NAV (Top 5) |
| Slicer | Category, Date Range |

### Page 3 — Investor Analytics
| Visual | Metric |
|---|---|
| Choropleth Map | Investment by State |
| Pie Chart | Gender Split |
| Bar Chart | Age Group Distribution |
| Bar Chart | T30 vs B30 City Tier |
| Line Chart | Monthly Transaction Volume |
| Slicer | Transaction Type, Age Group, State |

### Data Sources
Connect to: `data/db/bluestock_mf.db`

Tables used:
- `dim_fund`
- `fact_nav`
- `fact_performance`
- `fact_transaction`
- `fact_aum`

### Setup Instructions
1. Open Power BI Desktop
2. Get Data → SQLite → `data/db/bluestock_mf.db`
3. Import all 5 tables
4. Build relationships:
   - `dim_fund.amfi_code` → `fact_nav.amfi_code`
   - `dim_fund.amfi_code` → `fact_performance.amfi_code`
   - `dim_fund.amfi_code` → `fact_transaction.amfi_code`
5. Save as `dashboard/bluestock_mf.pbix`
