# Phase 3 — Free Edition scheduling and monitoring (operator guide)

**Status: configuration instructions committed; no Databricks job has been created or run by ChatGPT.** Phase 2 notebook was validated by the project owner in Databricks Free Edition (five Bronze events, two active Silver orders, one delete tombstone, and Gold revenue of 165.00).

## Objective

Schedule the existing `phase2_bronze_silver_gold` notebook as a single **serverless Notebook task**. Databricks Jobs & Pipelines tracks run history, state, duration and failures. The notebook already includes assertions for CDC ordering, deletes, revenue, and replay safety; failed assertions should mark job runs failed.

**Important:** This is a demo replay of five static synthetic events, *not* continuous ingestion of new files. Run every week during learning to conserve quota, or keep the schedule paused after a successful manual run.

## Option A — fastest: Schedule from the imported notebook

1. Open Databricks Workspace → the imported notebook `phase2_bronze_silver_gold`.
2. Click **Schedule** (top right).
3. If the **New schedule** dialog appears, use job name `cdc-lakehouse-synthetic-validation`.
4. Set **Simple** → **Weekly**, choose a day/time and verify the displayed timezone. Prefer weekly rather than hourly/daily for the static demo.
5. Select **Serverless** compute, if prompted.
6. In optional notifications, add an email for **failure** only, if supported. No secrets in parameters or notifications.
7. Click **Create**. This creates a scheduled Databricks job, not a ChatGPT scheduled task.

## Option B — Jobs & Pipelines

1. Click **Jobs & Pipelines → Create → Job**.
2. Name it `cdc-lakehouse-synthetic-validation`.
3. Add a **Notebook** task named `bronze_silver_gold_cdc`.
4. Select **Workspace** as the source, then browse to `phase2_bronze_silver_gold` (the imported Databricks notebook).
5. Choose **Serverless**; save task.
6. Click **Run now** for a manual end-to-end check. Review run details and notebook output.
7. Once successful, add a **Weekly** schedule; use failure notifications if available.

## Validate the first job run

In Jobs & Pipelines, open the job → **Runs** → latest run. Check:
- Run state is **Succeeded**.
- The final notebook cell prints `PASS: Bronze=5 unique events; Silver=2 active + 1 tombstone; Gold=$165.00; replay safe`.
- The run details show a duration and the actual run date/time.
- Compare current persisted tables with [validation SQL](../sql/phase3_validation.sql).
- Run the job a second time (manually) and confirm counts remain unchanged. This exercises the notebook's replay logic and Delta MERGE idempotency on the same synthetic inputs.

## Failure investigation

1. Open the failed run under the job's **Runs** tab, then select the failed task/cell.
2. Read the first exception and the affected SQL command. Fix the notebook and run manually.
3. `PERMISSION_DENIED`: check your workspace catalog/schema creation privileges.
4. `TABLE_OR_VIEW_NOT_FOUND`: check active `current_catalog()`, `workspace.cdc_portfolio`, and that earlier setup cells ran.
5. Assertion failures: check whether external edits changed the demo tables, and inspect latest Silver sequence/tombstone state.
6. Compute/quota error: Free Edition only supports quota-limited serverless resources; retry after the quota reset instead of upgrading automatically.

## Boundaries

- GitHub documents and SQL queries have been committed; they have **not** been executed in your workspace from ChatGPT.
- Databricks Jobs & Pipelines will run the notebook only once you create the job in the UI.
- The demo still uses static synthetic events embedded in the notebook. To simulate advancing batches, you would need new events and ingestion checkpoints.
- Azure Data Factory / ADLS Gen2 / Azure Databricks (Azure-managed workspace) / Power BI remain **not deployed**.
- Do not publish workspace tokens, private workspace URLs, personal email addresses, or credentials.

## References

- [Schedule notebook jobs](https://docs.databricks.com/aws/en/notebooks/schedule-notebook-jobs)
- [Create Jobs](https://docs.databricks.com/aws/en/jobs/configure-job)
- [Free Edition limits](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
