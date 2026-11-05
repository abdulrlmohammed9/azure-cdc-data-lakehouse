# Citi Bike GBFS live-data extension (Phase 5)

**Status:** GitHub code committed; live API fetch, workflow execution, and Databricks notebook have **not** yet been executed or validated by the assistant. The original synthetic pipeline and dashboard are unchanged.

This separate project ingests *real, publicly reported* station snapshots from [Citi Bike system data](https://citibikenyc.com/system-data). Public GBFS station status/info feeds describe station availability; they **do not supply insert/update/delete CDC records**. Changes are inferred by comparing timestamped observations.

## Pipeline architecture (free learning path)

```text
Citi Bike GBFS station_status + station_information
  -> GitHub Actions manual workflow, or local capture script
  -> citibike/data/latest_snapshot.json (rolling latest copy in GitHub)
  -> MANUAL upload to Databricks UC Volume
  -> Databricks Serverless notebook
  -> Bronze: historical station snapshots (append-by-unique ID + timestamp)
  -> Silver: latest station states + detected station changes
  -> Gold: station availability view
  -> optional separate Databricks AI/BI dashboard
```

**Important:** GitHub Actions captures data independently; it does *not* automatically sync snapshots into Databricks Free Edition. The current Databricks import step is manual. Running the existing Sunday synthetic job will not fetch or ingest Citi Bike data. Never advertise this as an end-to-end live autonomous pipeline until a supported sync method has been verified.

## Step 1 — Capture a current public snapshot

**Method A: GitHub Actions (recommended)**

1. In your GitHub repository, open **Actions** and select **Citi Bike GBFS capture (manual)**.
2. Select **Run workflow → main → Run workflow**.
3. Review the run logs. It first runs the offline tests, then fetches both public feeds and commits `citibike/data/latest_snapshot.json`.
4. If the push fails with `403` or resource-not-accessible error, review repository **Settings → Actions → General → Workflow permissions** and grant **Read and write permissions** only if acceptable, or instead capture via Method B.
5. The workflow is deliberately **manual**, not hourly or unattended. This avoids unnecessary Git history growth and quota use during initial validation.

**Method B: GitHub Codespaces (no workflow write permissions required)**

```bash
python -m unittest discover -s citibike/tests -v
python -m citibike.capture
```

The second command requests the GBFS JSON over HTTPS and writes the normalized latest snapshot. Review the output and commit it if desired. It requires public internet connectivity. All source data is public but can be rate-limited or temporarily unavailable.

**To create useful CDC changes:** capture again after a meaningful time interval; process each capture in Databricks before replacing the uploaded snapshot. The GitHub path contains only the most recent version; Git history retains old revisions but there is no automatic history loader. The notebook's historical Bronze and changes tables are preserved across notebook runs.

## Step 2 — Import snapshot into Databricks Free Edition

1. In your Databricks workspace, open **Catalog → workspace → Create schema** named `citibike_live` (or let the notebook create it).
2. Under that schema, create a managed **Volume** named `landing`, if not already present. The notebook can also create it where permissions allow.
3. From GitHub, download `citibike/data/latest_snapshot.json`.
4. In **Catalog → workspace → citibike_live → Volumes → landing**, use **Upload to volume** to upload that JSON with the exact filename `latest_snapshot.json`.
5. Use the notebook path:
   `/Volumes/workspace/citibike_live/landing/latest_snapshot.json`

The notebook reads from the Volume, not directly from an external API. Databricks Free Edition generally restricts outbound internet access; this approach follows the manual-upload pattern supported by Databricks.

## Step 3 — Import and run the Databricks notebook

Import `citibike/databricks/phase5_citibike_bronze_silver_gold.py` as a separate Python notebook and use **Serverless** compute. Run all cells. Do not replace the existing `phase2_bronze_silver_gold` notebook.

The new notebook creates:
- `workspace.citibike_live.bronze_station_snapshots`: station-level observations keyed by `station_id` and `captured_at`.
- `workspace.citibike_live.silver_station_latest`: latest known row per station; strictly newer timestamps update existing rows.
- `workspace.citibike_live.silver_station_changes`: first observations (`NEW`) and observed availability/operating-status changes (`UPDATED`).
- `workspace.citibike_live.gold_station_availability`: an analytics-ready SQL view including `can_rent` and `can_return`.

**Station absent from a snapshot is *not* deleted.** Without a reliable source deletion signal, disappearing stations remain in Silver with their last-seen timestamp. Use freshness checks before treating them as currently operating. `captured_at` is ingestion observation time, not the source's event time.

## Step 4 — Validate CDC behavior

1. Run the notebook with a captured snapshot and inspect Gold.
2. Run it **again with the same file**. Bronze, Silver and changes counts should not increase (idempotency).
3. Capture a **newer snapshot** through GitHub Actions or Codespaces, upload it to the same volume path, and rerun.
4. Bronze should increase by one row per station observed in the new timestamp, Silver keeps one row per station, and Changes should record only stations with changed availability/operating status or first sightings.
5. Use [dashboard SQL](sql/dashboard_queries.sql) to examine counts, availability and observation history. This is a separate dashboard from your existing synthetic e-commerce dashboard.

The notebook includes invariant assertions but its successful execution is **not yet verified**. Source feed layouts and workspace privileges can vary, so troubleshoot the first run before scheduling anything.

## No-subscription constraints & caveats

- The GitHub Actions workflow is manually triggered and stores **one rolling latest** JSON in the public repository. Captures can be sizeable; do not run it frequently.
- There is **no automated GitHub→Databricks transfer** yet. Scheduled Databricks notebook runs against an unchanged file would not reflect new real data.
- Free Edition has serverless quotas; stop or pause runs if quota errors appear.
- GBFS availability does not measure actual trip demand or bike turnover; snapshots can be incomplete, stale or intermittently inaccessible.
- There is no guaranteed delete event, and no real transaction data, customer information, or financial revenue.
- Do not claim the original Azure Data Factory / ADLS Gen2 architecture has been deployed.

## Sources
- [Citi Bike data](https://citibikenyc.com/system-data)
- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Import data into Unity Catalog volume](https://docs.databricks.com/aws/en/getting-started/import-visualize-data)
