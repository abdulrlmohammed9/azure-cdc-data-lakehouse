# Databricks notebook source
# Citi Bike real-data CDC extension (distinct from the synthetic project).
# Stage a capture.py-generated latest_snapshot.json into a UC volume before running.
# Source records are observations of public GBFS data, NOT emitted CDC events.

# COMMAND ----------
from pyspark.sql import functions as F
from delta.tables import DeltaTable

catalog = "workspace"
schema = "citibike_live"
volume = "landing"
for ident in (catalog, schema, volume):
    assert ident.replace("_", "").isalnum(), f"Unsafe identifier: {ident}"
prefix = f"`{catalog}`.`{schema}`"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {prefix}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {prefix}.`{volume}`")
snapshot_path = f"/Volumes/{catalog}/{schema}/{volume}/latest_snapshot.json"
print("Upload latest_snapshot.json to:", snapshot_path)

# COMMAND ----------
# Read the single uploaded snapshot. To process newer data, replace the file in the
# volume, then rerun this notebook (manual import is not continuous ingestion).
raw = spark.read.option("multiLine", True).json(snapshot_path)
if raw.count() != 1:
    raise ValueError("Expected exactly one snapshot JSON object")
if raw.select(F.size("stations").alias("n")).first()["n"] == 0:
    raise ValueError("Empty station list")
snapshot_ts = F.to_timestamp("captured_at")
incoming = (raw.select(F.explode("stations").alias("s"), F.col("captured_at"))
    .select(
      F.col("s.station_id").cast("string").alias("station_id"),
      F.col("s.station_name").cast("string").alias("station_name"),
      F.col("s.latitude").cast("double").alias("latitude"),
      F.col("s.longitude").cast("double").alias("longitude"),
      F.col("s.capacity").cast("long").alias("capacity"),
      F.col("s.bikes_available").cast("long").alias("bikes_available"),
      F.col("s.docks_available").cast("long").alias("docks_available"),
      F.col("s.is_renting").cast("boolean").alias("is_renting"),
      F.col("s.is_returning").cast("boolean").alias("is_returning"),
      F.to_timestamp("captured_at").alias("captured_at")
    ))
if incoming.filter(F.col("station_id").isNull() | F.col("captured_at").isNull()
   | F.col("bikes_available").isNull() | F.col("docks_available").isNull()).count() > 0:
    raise ValueError("Required station data is missing")
if incoming.filter((F.col("bikes_available") < 0) | (F.col("docks_available") < 0)).count() > 0:
    raise ValueError("Negative availability count")
if incoming.groupBy("station_id").count().filter("count > 1").count() > 0:
    raise ValueError("Duplicate station IDs in snapshot")
incoming.createOrReplaceTempView("citibike_incoming")
print("Imported", incoming.count(), "real station observations")

# COMMAND ----------
bronze = f"{prefix}.bronze_station_snapshots"
silver = f"{prefix}.silver_station_latest"
changes = f"{prefix}.silver_station_changes"
gold = f"{prefix}.gold_station_availability"
spark.sql(f"""CREATE TABLE IF NOT EXISTS {bronze} (
 station_id STRING, station_name STRING, latitude DOUBLE, longitude DOUBLE,
 capacity BIGINT, bikes_available BIGINT, docks_available BIGINT,
 is_renting BOOLEAN, is_returning BOOLEAN, captured_at TIMESTAMP
) USING DELTA""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {silver} (
 station_id STRING, station_name STRING, latitude DOUBLE, longitude DOUBLE,
 capacity BIGINT, bikes_available BIGINT, docks_available BIGINT,
 is_renting BOOLEAN, is_returning BOOLEAN, captured_at TIMESTAMP
) USING DELTA""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {changes} (
 station_id STRING, captured_at TIMESTAMP, old_bikes BIGINT, new_bikes BIGINT,
 old_docks BIGINT, new_docks BIGINT, change_type STRING
) USING DELTA""")
fields = ["station_name","latitude","longitude","capacity","bikes_available",
          "docks_available","is_renting","is_returning","captured_at"]
DeltaTable.forName(spark, bronze).alias("t").merge(
    incoming.alias("s"),
    "t.station_id = s.station_id AND t.captured_at = s.captured_at"
).whenNotMatchedInsert(values={k:f"s.{k}" for k in ["station_id", *fields]}).execute()
# Add change events before updating Silver. A rerun cannot insert duplicates.
silver_df = spark.table(silver)
prior = (incoming.alias("s").join(silver_df.alias("t"), F.col("s.station_id") == F.col("t.station_id"), "left")
  .where(F.col("t.station_id").isNull() | (F.col("s.captured_at") > F.col("t.captured_at")))
  .where(F.col("t.station_id").isNull()
     | ~F.col("s.bikes_available").eqNullSafe(F.col("t.bikes_available"))
     | ~F.col("s.docks_available").eqNullSafe(F.col("t.docks_available"))
     | ~F.col("s.is_renting").eqNullSafe(F.col("t.is_renting"))
     | ~F.col("s.is_returning").eqNullSafe(F.col("t.is_returning")))
  .select(
   F.col("station_id"),
   F.col("s.captured_at").alias("captured_at"),
   F.col("t.bikes_available").alias("old_bikes"),
   F.col("s.bikes_available").alias("new_bikes"),
   F.col("t.docks_available").alias("old_docks"),
   F.col("s.docks_available").alias("new_docks"),
   F.when(F.col("t.station_id").isNull(),F.lit("NEW")).otherwise(F.lit("UPDATED")).alias("change_type")
  ))
# Materialize pre-merge change events first, avoiding lazy evaluation after Silver changes.
prior.cache()
prior.count()
DeltaTable.forName(spark, changes).alias("t").merge(
  prior.alias("s"), "t.station_id=s.station_id AND t.captured_at=s.captured_at"
).whenNotMatchedInsertAll().execute()
prior.unpersist()
DeltaTable.forName(spark, silver).alias("t").merge(
  incoming.alias("s"), "t.station_id = s.station_id"
).whenMatchedUpdate(condition="s.captured_at > t.captured_at",
  set={k:f"s.{k}" for k in fields}
).whenNotMatchedInsert(values={k:f"s.{k}" for k in ["station_id", *fields]}).execute()

# COMMAND ----------
# Gold: a live-state view, not actual trip/usage or historically verified demand.
spark.sql(f"""CREATE OR REPLACE VIEW {gold} AS
SELECT station_id, station_name, latitude, longitude, capacity, bikes_available,
 docks_available, is_renting, is_returning, captured_at,
 CASE WHEN is_renting AND bikes_available > 0 THEN TRUE ELSE FALSE END AS can_rent,
 CASE WHEN is_returning AND docks_available > 0 THEN TRUE ELSE FALSE END AS can_return
FROM {silver}""")
print("Bronze observation count:",spark.table(bronze).count())
print("Silver latest station count:",spark.table(silver).count())
print("Recorded changes:",spark.table(changes).count())
display(spark.table(gold).orderBy(F.desc("bikes_available")).limit(20))

# COMMAND ----------
# Dataset-specific invariants. Snapshot absence is never automatically a delete.
assert spark.table(silver).groupBy("station_id").count().filter("count > 1").count() == 0
assert spark.table(bronze).groupBy("station_id", "captured_at").count().filter("count > 1").count() == 0
assert spark.table(silver).filter("bikes_available < 0 OR docks_available < 0").count() == 0
assert spark.table(gold).count() == spark.table(silver).count()
print("PASS: Citi Bike station Delta tables validated. Counts depend on the live public feed.")
