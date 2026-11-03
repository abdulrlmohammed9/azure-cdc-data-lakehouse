# Portfolio demonstration walkthrough — Databricks CDC Lakehouse

This is a **ready-to-record demonstration script**, not a recording of a completed screen capture. All example business records are synthetic.

## Suggested 2–3 minute walkthrough

| Segment | What to show | Narration |
| --- | --- | --- |
| 0:00–0:20 | GitHub README and architecture | "This reproducible project models e-commerce CDC with Delta Lake and a Bronze/Silver/Gold design in Databricks Free Edition." |
| 0:20–0:45 | Source notebook and synthetic events | "Five insert, update, and delete events demonstrate change tracking and deterministic ordering." |
| 0:45–1:15 | Catalog: Bronze, Silver and Gold | "Bronze retains raw events; Silver uses sequence-aware MERGE and deletion tombstones; Gold aggregates active orders by customer." |
| 1:15–1:35 | Notebook's final assertions | "Validation checks show five Bronze events, two active orders, one deleted order, and $165 in synthetic revenue, including replay protection." |
| 1:35–1:55 | Jobs & Pipelines → successful run | "The notebook runs as a serverless job. A weekly Sunday 9 AM America/Chicago trigger and failure-only alerts have been configured." |
| 1:55–2:20 | Published SQL dashboard | "Four KPI counters, regional revenue, CDC operation distribution and customer-level reporting make the results easy to inspect." |
| 2:20–2:40 | GitHub limitations/roadmap | "This is an educational Databricks Free Edition implementation, not an Azure Data Factory or ADLS Gen2 deployment; the dataset is static." |

## Before recording
1. Open the correct notebook and successful job-run record.
2. Open Catalog Explorer → `workspace.cdc_portfolio`.
3. Open the published dashboard and verify data loads.
4. Hide browser bookmarks, email addresses, workspace IDs, access tokens, personal URLs, notifications and other private details.
5. Make clear the synthetic metrics do not represent real revenue or production throughput.
6. Record using an available screen recorder and export to an MP4 or GIF under a reasonable file size.

## Publish evidence
- Dashboard PDF intended path: `docs/cdc-lakehouse-dashboard.pdf`.
- Dashboard preview intended path: `docs/images/cdc-lakehouse-dashboard.png`.
- Video can be linked from README after it is actually recorded and uploaded to a suitable hosting location.
- **At the time this guide was written, binary dashboard evidence and video had not yet been uploaded through GitHub.**
