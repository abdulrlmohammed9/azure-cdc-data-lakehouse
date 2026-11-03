# Architecture — illustrative target and implemented local demo

## Implemented (local only)
```text
Synthetic CSV sources (ERP customers, e-commerce order CDC, inventory sample)
     | 
     +--> Local Python CDC parser (e-commerce events) = Bronze source ingestion
                  |
                  +--> in-memory CDC apply (Silver order state)
                  |
                  +--> customer join and revenue aggregation (Gold)
                  |
                  +--> output/*.json (ignored by git)
```
Inventory is supplied as an example of a third domain; **it is not processed** by the local starter.

## Target Azure architecture (NOT deployed)
```text
ERP + E-commerce + Inventory (synthetic)
        -> Azure Data Factory ingestion/orchestration
        -> ADLS Gen2 Bronze
        -> Azure Databricks PySpark / Delta Lake Silver MERGE
        -> Gold curated Delta tables / Power BI
```

## Quality and security next steps
- Incremental file ingestion, schema drift detection, idempotent checkpoints.
- Data quality validation, null/duplicate keys, CDC sequencing/replay testing.
- Azure managed identities, Key Vault, least privilege, monitoring, and cost controls.
- Power BI semantic model and measures based on tested Gold tables.
