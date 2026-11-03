# Azure CDC Data Lakehouse — Synthetic Starter

[![Status: validated learning project](https://img.shields.io/badge/status-validated%20learning%20project-brightgreen)](#implementation-status)

An educational, portfolio-friendly example of **change data capture (CDC)** and a **Bronze → Silver → Gold** data flow, inspired by common Azure Data Engineering patterns. All included records are **synthetic**. This repository is independently recreated and contains **no employer/customer source code, credentials, or production data**.

## Business problem

Order systems send inserts, updates, and deletes. Downstream analytics need the *latest active order state* rather than a naïve sum of all events. This starter demonstrates how to consume a small ordered event log, apply upserts/deletes, enrich with a customer dimension, and calculate revenue.

## Implementation status

| Component | Status | Evidence |
| --- | --- | --- |
| Synthetic ERP customer CSV + e-commerce CDC CSV | **Included** | `sample-data/` |
| Synthetic inventory CSV | **Sample only** | Not ingested into Gold yet |
| Local ordered CDC I/U/D processing | **Implemented** | `src/local_cdc.py` |
| Local Silver/Gold JSON outputs | **Implemented** | Run instructions below |
| Local Python unit tests | **3 passed in GitHub Codespaces (Nov 3, 2026)** | `tests/test_local_cdc.py` |
| Databricks Bronze/Silver/Gold Delta MERGE | **Executed and validated in Databricks Free Edition (Nov 3, 2026)** | `databricks/phase2_bronze_silver_gold.py` |
| Databricks Gold customer revenue view | **Created; result assertions passed** | `databricks/phase2_bronze_silver_gold.py` (separate `sql/gold_customer_revenue.sql` is an unverified template) |
| Databricks serverless Job | **Created and successful run shown (Nov 3, 2026)** | `docs/phase3-jobs-monitoring.md` |
| Weekly trigger / failure emails | **Configured in UI screenshots; saved/active status not independently verified** | `docs/phase3-jobs-monitoring.md` |
| ADF pipeline, ADLS Bronze ingestion | **Planned, not built** | `adf/README.md` |
| Power BI dashboard | **Planned, not built** | No dashboard included |

**This is a validated educational Databricks Free Edition project, not an Azure production deployment.** The local Python starter and Databricks Delta notebook have been executed successfully; Azure Data Factory, ADLS Gen2, and Azure-hosted Databricks remain unconfigured.

## Architecture

```text
Synthetic CSV (Bronze inputs)
       |
       v
Ordered CDC event processing (Silver active orders)
       |
       v
Customer dimension join + revenue aggregation (Gold)
       |
       v
JSON outputs for inspection
```

See [architecture notes](docs/architecture.md) for the proposed Azure architecture.

## Quickstart (Python 3.10+)

No Azure account or third-party packages are required for the local demo:

```bash
python -m src.local_cdc
```

Expected summary: one active order for C001 with revenue **125.00**, and one for C003 with revenue **40.00**. Order O101 is removed by a later delete event. Results are saved in `output/silver_orders.json` and `output/gold_customer_revenue.json`.

To run tests:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Outputs, environment files, and credentials are excluded by `.gitignore`.

## Project layout

```text
adf/             Planned Azure Data Factory orchestration
databricks/      Delta MERGE starter example (needs Databricks workspace)
docs/            Architecture and next steps
sample-data/     Synthetic ERP, e-commerce CDC, inventory CSVs
sql/             Gold view SQL template
src/             Executable local Python CDC demo
tests/           Pytest tests for local CDC
requirements.txt Optional test dependency
.gitignore       Ignore secrets, generated outputs, local environments
```

## Data contracts & limitations

- Order keys use `order_id`; CDC ordering uses integer `sequence`, then `event_id`.
- Event types: `I` (insert), `U` (update), `D` (delete).
- The local program recomputes active state from the complete event file. It does **not** implement durable streaming checkpoints, cross-run sequence persistence, distributed Delta MERGE, or cloud orchestration.
- Financial arithmetic uses Python floats for demo simplicity; a production pipeline should use precise decimal types.
- The provided inventory domain is illustrative and isn't included in the aggregate.

## Phase 2: Databricks Bronze / Silver / Gold (validated in Free Edition)

The [Databricks Phase 2 notebook](databricks/phase2_bronze_silver_gold.py) uses synthetic records to create managed Delta Bronze event, Silver order state, customer dimension, inventory sample, and Gold customer revenue tables/view. It includes sequence-aware CDC MERGE, delete tombstones, replay checks, and assertions. See the [step-by-step Databricks setup and validation guide](docs/phase2-databricks.md).

**Status (Nov 3, 2026):** Owner-executed notebook finished with the reported validation message: `PASS: Bronze=5 unique events; Silver=2 active + 1 tombstone; Gold=$165.00; replay safe`. Catalog Explorer screenshots show the five objects in `workspace.cdc_portfolio`. Azure Data Factory, ADLS Gen2, and Power BI remain future phases.

## Phase 3 — Databricks Jobs and monitoring (manual job run verified)

On **November 3, 2026**, the owner created the Databricks Free Edition job `cdc-lakehouse-synthetic-validation` with a serverless notebook task running `phase2_bronze_silver_gold`. The Jobs **Runs** page showed a green successful run and a **View latest successful run** link. The job-run output itself was not separately captured; the notebook's interactive execution had already passed CDC/revenue/replay assertions.

UI screenshots showed a proposed **active weekly trigger** for **Sunday at 09:00 America/Chicago** and **failure-only email notifications**, with skipped/cancelled notifications muted. Those screens did not establish that **Save** was clicked for either configuration; verify both in Databricks before calling them active. First planned Sunday is **November 8, 2026** if the trigger was saved and enabled.

See the [Phase 3 job operations guide](docs/phase3-jobs-monitoring.md) and [read-only validation SQL](sql/phase3_validation.sql). The scheduled job replays **static synthetic events**; it does not fetch new events or run ADF/ADLS.

## Roadmap

1. Add inventory domain with its own CDC/snapshot semantics and joined analytics.
2. Extend the validated Databricks notebook with additional CDC edge cases, incremental event ingestion and monitoring.
3. Build ADLS Bronze landing and deploy ADF linked services, pipelines, and monitoring.
4. Add data-quality checks, CI, secured configuration, deployment guidance, and a Power BI model.

## Portfolio and data provenance

All data here is synthetic and fictional. Reproduce experiments only in environments you own or are authorized to use. This repository is a **starter implementation**, not a copy of the professional Infinite Electronics engagement.
