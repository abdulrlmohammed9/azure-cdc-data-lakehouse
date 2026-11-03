# Azure Data Factory orchestration — planned

No deployable ADF pipeline is included yet. ADF is **not configured or tested** in this starter.

Suggested next implementation:
1. Provision a development Azure Data Factory, a storage account, and Databricks workspace.
2. Configure managed identity/service principal access and keep secrets in Key Vault.
3. Define linked services and datasets for synthetic ERP, orders CDC, and inventory.
4. Add a pipeline to ingest to Bronze, trigger the Databricks Silver merge, then build Gold.
5. Enable retry policies, alerts, incremental watermarks, run logging, and integration tests.
6. Export validated pipeline ARM/JSON definitions here when tested.

The local Python demo in `src/` runs independently of Azure.
