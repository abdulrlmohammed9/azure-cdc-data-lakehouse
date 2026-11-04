# CDC Lakehouse | Data Engineering & Analytics

**Validated Databricks Free Edition portfolio project · Synthetic data · November 2026**

A reproducible change data capture (CDC) demonstration with **Python, PySpark, Databricks Delta Lake, SQL, Databricks Jobs, and an AI/BI dashboard**. The project illustrates inserts, updates, deletes, deterministic event ordering, replay safety, and customer analytics using a Bronze → Silver → Gold medallion architecture.

> **Scope:** Independent, educational implementation using fictional records. This is **not** an Azure Data Factory / ADLS Gen2 deployment and does not contain employer or client production data.

## What works

| Component | Status |
| --- | --- |
| Local Python CDC processor | Executed in Codespaces; **3 automated tests passed** |
| Synthetic ERP customer, e-commerce CDC and inventory inputs | Included; inventory is sample-only for analytics |
| Databricks Bronze raw events | Validated: **5 distinct events** |
| Databricks Silver Delta MERGE | Validated: **2 active orders, 1 deleted tombstone**, sequence-aware replay protection |
| Databricks Gold SQL analytics view | Validated: **$165.00** synthetic active-order revenue |
| Databricks Serverless Job | Owner created and ran it successfully |
| Weekly job schedule | Owner confirmed active: **Sunday, 9 AM America/Chicago** |
| Job notifications | Owner confirmed failure-only email notifications enabled |
| Databricks AI/BI dashboard | Built and published by project owner; visually verified |
| Azure Data Factory, ADLS Gen2, Power BI | **Not implemented** |

## Architecture

```text
Synthetic e-commerce CDC + ERP customer dimension + inventory sample
           |
           v
Databricks Bronze Delta tables (raw order events; inventory sample)
           |
           v
Silver Delta MERGE (upserts, deletion tombstones, sequence guard)
           |
           v
Gold customer revenue SQL view
           |
           v
Published Databricks AI/BI Dashboard
    4 KPI counters | revenue by region | CDC operation donut | customer table

Databricks Serverless Job: scheduled execution and failure alerts
```

See the [architecture details](docs/architecture.md).

## Dashboard evidence

The published dashboard was reviewed from the project owner's PDF export, displaying:

| KPI | Verified synthetic value |
| --- | ---: |
| Total revenue | **$165.00** |
| Active orders | **2** |
| Deleted orders | **1** |
| Total CDC events | **5** |
| Revenue by region | West $125; East $40; Central $0 |
| CDC operations | Inserts 3; Updates 1; Deletes 1 |

The evidence files are prepared for upload but **not yet present in this GitHub repository**. After uploading, the following links will open:
- [Dashboard PDF export](docs/cdc-lakehouse-dashboard.pdf)
- [Dashboard PNG preview](docs/images/cdc-lakehouse-dashboard.png)

See the [dashboard setup and verification guide](docs/phase4-dashboard.md).

## Reproduce the local CDC demonstration

Requires Python 3.10+:

```bash
git clone https://github.com/abdulrlmohammed9/azure-cdc-data-lakehouse.git
cd azure-cdc-data-lakehouse
python -m src.local_cdc
python -m pip install -r requirements.txt
python -m pytest -q
```

Expected: 3 passing tests; local outputs under `output/` (ignored by Git).

## Reproduce the Databricks Delta pipeline

1. Create a **Databricks Free Edition** workspace with sufficient permissions to create a schema.
2. Import [the Phase 2 notebook](databricks/phase2_bronze_silver_gold.py) to your Databricks workspace.
3. Run all notebook cells with Serverless compute. The notebook generates synthetic input records without requiring cloud storage.
4. Inspect the five objects in `workspace.cdc_portfolio` (or your available catalog).
5. Confirm the terminal assertion `PASS: Bronze=5 unique events; Silver=2 active + 1 tombstone; Gold=$165.00; replay safe`.
6. See the [job setup](docs/phase3-jobs-monitoring.md) and [dashboard SQL datasets](sql/phase4_dashboard_datasets.sql).

## Repository structure

```text
src/              Runnable local Python CDC example
tests/            Local automated tests
sample-data/      Fictional source records
databricks/       Phase 2 Delta Lake notebook + earlier starter
sql/              Gold view template, CDC validation, dashboard queries
docs/             Architecture, dashboard, jobs, demo walkthrough
adf/              Future orchestration plan; not deployed
requirements.txt  Python test dependency
.gitignore        Development outputs and secrets exclusions
```

## Demonstration and portfolio materials

- [2–3 minute demo walkthrough / recording script](docs/demo-walkthrough.md) — **a recording is not yet available**.
- [Phase 2 implementation guide](docs/phase2-databricks.md).
- [Phase 3 scheduling and monitoring](docs/phase3-jobs-monitoring.md).
- [Phase 4 dashboard](docs/phase4-dashboard.md).

## Limitations and roadmap

- Current event inputs are **static synthetic samples**, not production CDC streaming or continuously arriving data.
- Inventory is available in a Bronze sample but not joined to the Gold revenue report.
- Scheduled executions replay the sample data; the actual first future scheduled run and alert delivery have not yet been observed.
- The local Python prototype and the Databricks implementation are separate demonstrations.
- ADF orchestration, ADLS Gen2, Azure-hosted Databricks, production checkpoints, secure cloud deployment and Power BI remain future extensions.
