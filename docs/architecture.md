# Architecture — validated Databricks Free Edition CDC Lakehouse

## Implemented and validated (November 3, 2026)

```text
Synthetic ERP customers + e-commerce order CDC events + inventory sample
          |
          v
Databricks Free Edition / Unity Catalog
workspace.cdc_portfolio
          |
          +-- Bronze: bronze_order_events (5 ordered synthetic CDC events)
          |           bronze_inventory (sample snapshot)
          |
          +-- Silver: silver_orders
          |           Delta MERGE with sequence guard and delete tombstones
          |           (2 active + 1 deleted)
          |           dim_customers (synthetic ERP customer dimension)
          |
          +-- Gold: gold_customer_revenue (SQL view)
                     (3 customer rows, $165.00 synthetic active revenue)
          |
          v
Databricks AI/BI dashboard — published by project owner
4 KPI cards + revenue-by-region bar + CDC donut + customer table

Databricks Serverless Job: cdc-lakehouse-synthetic-validation
Manual job execution successful; weekly Sunday 09:00 America/Chicago
and failure-only email notifications configured and owner-confirmed.
```

The notebook has been executed successfully and its assertions verified by the owner. The job's first future scheduled run and actual notification delivery have not yet been observed. Dashboard PDF and PNG evidence are available for manual upload; see [dashboard guide](phase4-dashboard.md) and [demo walkthrough](demo-walkthrough.md).

## Parallel local demonstration

`src/local_cdc.py` is a standard-library-only CDC demonstration runnable in GitHub Codespaces. The user reported 3 passing tests from `python -m pytest -q`; it produces local Silver/Gold JSON outputs. This is distinct from the Databricks Delta pipeline.

## Future Azure architecture — NOT deployed

```text
ERP + E-commerce + Inventory (synthetic)
  -> Azure Data Factory orchestration
  -> ADLS Gen2 Bronze ingestion
  -> Azure Databricks/Delta Silver and Gold
  -> Power BI / Databricks dashboard
```

Azure subscription, ADF, ADLS Gen2, Power BI, streaming input, incremental watermarks, job telemetry charts, and production security/monitoring have **not** been implemented. The current scheduled job replays static synthetic inputs; the dashboard summarizes these inputs, not real revenue.
