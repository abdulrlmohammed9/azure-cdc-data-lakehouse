# Azure CDC Data Lakehouse — Synthetic Starter

[![Status: local starter](https://img.shields.io/badge/status-local%20starter-blue)](#implementation-status)

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
| Local Python unit tests | **Included** | `tests/test_local_cdc.py` |
| Databricks Delta MERGE examples | **Phase 2 notebook committed, unverified in Databricks** | `databricks/phase2_bronze_silver_gold.py` |
| Databricks SQL Gold view | **Template, unverified** | `sql/gold_customer_revenue.sql` |
| ADF pipeline, ADLS Bronze ingestion, monitoring | **Planned, not built** | `adf/README.md` |
| Power BI dashboard | **Planned, not built** | No dashboard included |

**Do not interpret this repository as proof that an Azure production pipeline has been deployed.** The working core is a small local Python demonstration. The cloud implementation is the next phase.

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

## Phase 2: Databricks Bronze / Silver / Gold (code committed; cloud validation pending)

The [Databricks Phase 2 notebook](databricks/phase2_bronze_silver_gold.py) uses synthetic records to create managed Delta Bronze event, Silver order state, customer dimension, inventory sample, and Gold customer revenue tables/view. It includes sequence-aware CDC MERGE, delete tombstones, replay checks, and assertions. See the [step-by-step Databricks setup and validation guide](docs/phase2-databricks.md).

**Status:** Code published, not yet executed in your Databricks workspace. Azure Data Factory, ADLS Gen2, and Power BI remain future phases.

## Phase 3 — Databricks Jobs (setup guide, not deployed)

The Phase 2 Delta Lake notebook was **user-validated in Databricks Free Edition** (five Bronze CDC events, two active orders, one Silver delete tombstone, and Gold total revenue 165.00). For repeatable execution, see [Phase 3 Databricks Jobs and monitoring](docs/phase3-jobs-monitoring.md) and [read-only SQL checks](sql/phase3_validation.sql).

**Status:** Scheduling guidance and SQL committed; **no Databricks job has yet been created or executed by this repository automation**. A scheduled job will reprocess static synthetic events; it is not live ingestion. Azure Data Factory, ADLS Gen2, Azure Databricks deployment, and Power BI remain future work.

## Roadmap

1. Add inventory domain with its own CDC/snapshot semantics and joined analytics.
2. Validate Delta MERGE in a personal Databricks workspace; add repeat/replay tests.
3. Build ADLS Bronze landing and deploy ADF linked services, pipelines, and monitoring.
4. Add data-quality checks, CI, secured configuration, deployment guidance, and a Power BI model.

## Portfolio and data provenance

All data here is synthetic and fictional. Reproduce experiments only in environments you own or are authorized to use. This repository is a **starter implementation**, not a copy of the professional Infinite Electronics engagement.
