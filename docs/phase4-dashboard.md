# Phase 4 — Databricks AI/BI Dashboard

**Status:** SQL dataset templates and instructions committed. The dashboard is not yet created or validated in the Databricks workspace.

## Create a dashboard in Free Edition

1. Open Databricks **Dashboards**, or **New → Dashboard**, and create `CDC Lakehouse - Analytics Overview`.
2. Select **Serverless Starter Warehouse** if prompted.
3. On the **Data** tab, choose **Add SQL dataset** and paste the **first SELECT** from [Phase 4 SQL](../sql/phase4_dashboard_datasets.sql).
4. Run the query and name it `kpi_summary`. Expected: total_revenue=165.00, active_orders=2, deleted_orders=1, total_cdc_events=5.
5. Repeat for the remaining named datasets, using **one SELECT per dataset**: `revenue_by_region`, `cdc_event_distribution`, `customer_performance`, `silver_order_status`.
6. Open the canvas page and **Add a visualization**. Connect a **Counter** widget to `kpi_summary.total_revenue` and repeat for the other three metrics.
7. Add a **Bar** chart for `revenue_by_region`: x=region, y=revenue.
8. Add a **Pie/Donut** for `cdc_event_distribution`: category=operation_type, value=event_count.
9. Add a **Table** for `customer_performance`.
10. Preview the dashboard, verify results, and review sharing controls before publishing.

## Expected synthetic metrics

| KPI | Expected |
| --- | ---: |
| Revenue | $165.00 |
| Active orders | 2 |
| Deleted orders (Silver tombstones) | 1 |
| Bronze CDC events | 5 |
| Insert / Update / Delete events | 3 / 1 / 1 |
| West / East / Central revenue | 125 / 40 / 0 |

These metrics describe **static synthetic events**, not live sales or time-series trends. The weekly Databricks Job replays the sample and is not continuous ingestion. Native job-run telemetry is **not included** in these datasets.

## Common issues

- No SQL warehouse: check the **Serverless Starter Warehouse** selector and Free Edition quota.
- Missing table: confirm catalog `workspace` and schema `cdc_portfolio`.
- SQL dataset parser error: paste only one SELECT statement per dataset, without the other statements in the reference file.
- Unexpected totals: validate Bronze/Silver/Gold tables with [Phase 3 SQL](../sql/phase3_validation.sql).

Official guide: https://docs.databricks.com/aws/en/dashboards/tutorials/create-dashboard
