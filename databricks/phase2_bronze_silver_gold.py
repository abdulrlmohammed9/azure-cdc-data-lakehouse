# Databricks notebook source
# Phase 2: reproducible synthetic Bronze / Silver / Gold Delta Lake CDC demo.
# REQUIRES Databricks with Unity Catalog permissions and Delta support.
# This is NOT executed or validated in the connected Databricks environment yet.
# No Azure Data Factory or ADLS dependency. Rerunning is idempotent.
# Create a schema in your currently selected catalog (needs CREATE SCHEMA privileges).

# COMMAND ----------
import re
from pyspark.sql import functions as F
from pyspark.sql.window import Window

catalog = spark.sql("SELECT current_catalog() AS catalog").first()["catalog"]
schema = "cdc_portfolio"
for identifier in (catalog, schema):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Unexpected catalog/schema identifier: {identifier!r}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
prefix = f"`{catalog}`.`{schema}`"
bronze = f"{prefix}.bronze_order_events"
silver = f"{prefix}.silver_orders"
customers = f"{prefix}.dim_customers"
inventory = f"{prefix}.bronze_inventory"
gold = f"{prefix}.gold_customer_revenue"
print("Working catalog/schema:", catalog, schema)

# COMMAND ----------
# DDL: Bronze raw events; Silver state with tombstones and last applied sequence.
# Retaining deleted rows as tombstones ensures old replayed inserts cannot resurrect orders.
spark.sql(f"""CREATE TABLE IF NOT EXISTS {bronze} (
  event_id BIGINT, order_id STRING, customer_id STRING,
  order_date DATE, amount DECIMAL(12,2), operation STRING, sequence BIGINT
) USING DELTA""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {silver} (
  order_id STRING, customer_id STRING, order_date DATE,
  amount DECIMAL(12,2), is_deleted BOOLEAN, last_sequence BIGINT
) USING DELTA""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {customers} (
  customer_id STRING, customer_name STRING, region STRING
) USING DELTA""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {inventory} (
  sku STRING, category STRING, on_hand BIGINT
) USING DELTA""")
# Upsert synthetic dimensions, not employer/customer data.
spark.sql("""SELECT * FROM VALUES
  ('C001','Acme Retail','West'),
  ('C002','Bluebird Stores','Central'),
  ('C003','Cedar Markets','East')
AS d(customer_id, customer_name, region)""").createOrReplaceTempView("seed_customers")
spark.sql(f"""MERGE INTO {customers} t USING seed_customers s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET t.customer_name=s.customer_name, t.region=s.region
WHEN NOT MATCHED THEN INSERT (customer_id,customer_name,region)
VALUES (s.customer_id,s.customer_name,s.region)""")
spark.sql("""SELECT * FROM VALUES
 ('SKU-01','Electronics',12L), ('SKU-02','Accessories',25L), ('SKU-03','Electronics',8L)
 AS v(sku,category,on_hand)""").createOrReplaceTempView("seed_inventory")
spark.sql(f"""MERGE INTO {inventory} t USING seed_inventory s ON t.sku=s.sku
 WHEN MATCHED THEN UPDATE SET t.category=s.category,t.on_hand=s.on_hand
 WHEN NOT MATCHED THEN INSERT (sku,category,on_hand) VALUES (s.sku,s.category,s.on_hand)""")

# COMMAND ----------
# Two micro-batches demonstrate a real update and delete, not only a final-state snapshot.
events = [
 (1,"O100","C001","2026-01-01","120.00","I",1,1),
 (2,"O101","C002","2026-01-02","70.50","I",2,1),
 (3,"O100","C001","2026-01-01","125.00","U",3,2),
 (4,"O102","C003","2026-01-03","40.00","I",4,1),
 (5,"O101","C002","2026-01-02","70.50","D",5,2)
]
source = spark.createDataFrame(events,
  "event_id long, order_id string, customer_id string, order_date string, amount string, operation string, sequence long, batch long"
).selectExpr("event_id","order_id","customer_id",
  "CAST(order_date AS DATE) AS order_date",
  "CAST(amount AS DECIMAL(12,2)) AS amount",
  "operation","sequence","batch")
# Save raw events without duplicates across reruns.
source.createOrReplaceTempView("all_synthetic_events")
spark.sql(f"""MERGE INTO {bronze} t USING all_synthetic_events s
ON t.event_id=s.event_id
WHEN NOT MATCHED THEN INSERT
(event_id,order_id,customer_id,order_date,amount,operation,sequence)
VALUES (s.event_id,s.order_id,s.customer_id,s.order_date,s.amount,s.operation,s.sequence)""")

# COMMAND ----------
def apply_batch(batch_number: int) -> None:
    # Deduplicate each batch to one event/key before MERGE (Delta requirement).
    incoming = source.filter(F.col("batch") == batch_number)
    w = Window.partitionBy("order_id").orderBy(F.desc("sequence"),F.desc("event_id"))
    latest = incoming.withColumn("rn", F.row_number().over(w)).filter("rn=1").drop("rn","batch")
    latest.createOrReplaceTempView("batch_latest")
    spark.sql(f"""MERGE INTO {silver} t USING batch_latest s
      ON t.order_id=s.order_id
      WHEN MATCHED AND s.sequence > t.last_sequence THEN UPDATE SET
        t.customer_id=s.customer_id,
        t.order_date=s.order_date,
        t.amount=s.amount,
        t.is_deleted=(s.operation='D'),
        t.last_sequence=s.sequence
      WHEN NOT MATCHED THEN INSERT
        (order_id,customer_id,order_date,amount,is_deleted,last_sequence)
        VALUES (s.order_id,s.customer_id,s.order_date,s.amount,
                (s.operation='D'),s.sequence)""")

apply_batch(1)
apply_batch(2)

# COMMAND ----------
# Gold is a view on active Silver rows, joined to synthetic ERP customer dimension.
spark.sql(f"""CREATE OR REPLACE VIEW {gold} AS
 SELECT c.customer_id,c.customer_name,c.region,
        COUNT(s.order_id) AS order_count,
        CAST(COALESCE(SUM(s.amount),0) AS DECIMAL(14,2)) AS revenue
 FROM {customers} c
 LEFT JOIN {silver} s ON c.customer_id=s.customer_id AND s.is_deleted=false
 GROUP BY c.customer_id,c.customer_name,c.region""")

print("Bronze events:")
display(spark.table(bronze).orderBy("event_id"))
print("Silver state (including delete tombstone):")
display(spark.table(silver).orderBy("order_id"))
print("Gold customer revenue:")
display(spark.table(gold).orderBy("customer_id"))

# COMMAND ----------
# Assertions validate CDC changes, delete, replay protection, aggregates.
from decimal import Decimal
active = {r["order_id"]: r for r in spark.table(silver).filter("NOT is_deleted").collect()}
assert set(active) == {"O100","O102"}, f"Unexpected active orders: {set(active)}"
assert active["O100"]["amount"] == Decimal("125.00")
assert active["O102"]["amount"] == Decimal("40.00")
deleted = spark.table(silver).filter("order_id='O101'").first()
assert deleted is not None and deleted["is_deleted"] is True and deleted["last_sequence"] == 5
gold_rows = {r["customer_id"]: r for r in spark.table(gold).collect()}
assert sum(r["order_count"] for r in gold_rows.values()) == 2
assert sum(r["revenue"] for r in gold_rows.values()) == Decimal("165.00")
assert gold_rows["C001"]["revenue"] == Decimal("125.00")
assert gold_rows["C002"]["revenue"] == Decimal("0.00")
assert gold_rows["C003"]["revenue"] == Decimal("40.00")
assert spark.table(bronze).count() == 5, "Unexpected Bronze count; reset an earlier non-demo table if needed"
# Replaying older events must not change state or restore the deleted order.
apply_batch(1)
assert {r["order_id"] for r in spark.table(silver).filter("NOT is_deleted").collect()} == {"O100","O102"}
assert spark.table(silver).filter("order_id='O101' AND is_deleted").count() == 1
print("PASS: Bronze=5 unique events; Silver=2 active + 1 tombstone; Gold=$165.00; replay safe")
