# Phase 2 — Azure Databricks Delta Lake (synthetic CDC)

**Implementation:** [`databricks/phase2_bronze_silver_gold.py`](../databricks/phase2_bronze_silver_gold.py) is a Databricks source notebook with `# COMMAND ----------` cell delimiters, designed to be imported as a notebook. **Committed, but not yet executed in any Databricks workspace.**

## 1. Choose a workspace

- **No-cost prototype:** Databricks Free Edition (quota-limited, serverless). It is distinct from a paid Azure subscription. Sign up via the official Databricks Free Edition site.
- **Azure integration:** Create Azure Databricks in the [Azure portal](https://portal.azure.com), resource group `rg-cdc-portfolio-dev`, workspace `dbw-cdc-portfolio-dev`, preferred region available to your subscription. Choose serverless where eligible and review pricing/trial terms before creating anything billable. For real ADF + ADLS work later, use an Azure workspace.

Use a personal development workspace, not your employer's. Shut down classic compute when finished; serverless and cloud storage may incur charges depending on account and plan.

## 2. Import the notebook

1. In Databricks, open **Workspace** and use **Import**, or create a notebook and import the file from GitHub.
2. Supply the GitHub raw file URL:
   `https://raw.githubusercontent.com/abdulrlmohammed9/azure-cdc-data-lakehouse/main/databricks/phase2_bronze_silver_gold.py`
3. Use a Python notebook attached to eligible serverless or all-purpose compute with Unity Catalog access and Delta support.
4. Execute **all cells sequentially**, top to bottom.

The example uses `SELECT current_catalog()` and tries to create `cdc_portfolio` schema inside it. If you receive a permission error, switch to a catalog where you have `CREATE SCHEMA` permission, or ask an administrator to create the schema and grant access. No external files, volumes, secrets or storage accounts are needed for this phase.

## 3. Expected results

| Layer | Expected result |
| --- | --- |
| Bronze | 5 distinct synthetic CDC events (I/U/D) |
| Silver | 3 keyed rows including 2 active orders and 1 deleted tombstone |
| Gold | C001=125.00, C002=0.00, C003=40.00; active revenue total=165.00 |
| Replay | Reprocessing first batch leaves tombstones and updated records unchanged |

The notebook ends with Python `assert` checks and a PASS line. **These are expected results, not verified cloud test results.**

## 4. Validate manually

In a Databricks SQL editor or notebook, after choosing your catalog, run:

```sql
SELECT * FROM cdc_portfolio.bronze_order_events ORDER BY event_id;
SELECT order_id, amount, is_deleted, last_sequence
FROM cdc_portfolio.silver_orders ORDER BY order_id;
SELECT * FROM cdc_portfolio.gold_customer_revenue ORDER BY customer_id;
```

If your workspace doesn't resolve the same default catalog, use fully qualified `catalog.schema.table` names printed by the notebook.

Run the notebook a **second time** to test replay and idempotency. It should keep Bronze at 5 and Silver at 3 keyed records. The sample inventory is loaded into `bronze_inventory` but is not yet incorporated into a Gold supply-chain mart.

## 5. Common problems

- `PERMISSION_DENIED` / `CREATE SCHEMA`: choose a writable catalog; ask workspace admin for permissions.
- `NO_ACTIVE_WAREHOUSE` / no compute: attach serverless/all-purpose compute supported by your workspace.
- `TABLE_OR_VIEW_NOT_FOUND`: execute cells in order, check `current_catalog()`, and use the printed catalog/schema.
- `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`: the example deduplicates each batch by order ID and sequence; avoid directly MERGing all history at once.
- Stale result after replay: verify `last_sequence` ordering and retain delete tombstones.
- Reusing this demo schema with unrelated tables may fail assertions; use an isolated personal catalog/schema.

## 6. Scope & roadmap

**Implemented in GitHub:** notebook code, synthetic inputs, table DDL, MERGE operations, Gold view, assertions.

**Not yet verified:** executing in a Databricks workspace, cloud permissions, table persistence, runtime compatibility in your account.

**Not built:** Azure Data Factory orchestration, ADLS Gen2 external Bronze ingestion, continuous ingestion/checkpoints, Power BI dashboard, and production monitoring.

Official references:
- [Azure workspace setup](https://learn.microsoft.com/en-us/azure/databricks/admin/workspace/create-workspace)
- [Databricks Free Edition](https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-edition)
- [MERGE semantics](https://learn.microsoft.com/en-us/azure/databricks/delta/merge)
- [Unity Catalog default catalog](https://learn.microsoft.com/en-us/azure/databricks/catalogs/default)
