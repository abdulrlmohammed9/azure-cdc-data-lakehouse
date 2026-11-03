# Databricks notebook source
# STARTER TEMPLATE — requires a configured Databricks Runtime with Delta Lake.
# Configure an accessible input path before running. Do not use employer data.
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

input_path = "/Volumes/YOUR_CATALOG/YOUR_SCHEMA/YOUR_VOLUME/ecommerce_orders_cdc.csv"
silver_table = "YOUR_CATALOG.YOUR_SCHEMA.silver_orders"

bronze = (
    spark.read.option("header", True).option("inferSchema", True)
    .csv(input_path)
)
# For a batch CDC example, select the last event per key and then MERGE.
# Production CDC ingestion needs checkpoints, replay semantics, schema controls,
# and explicit handling of ordering/duplicates across micro-batches.
window = Window.partitionBy("order_id").orderBy(F.col("sequence").desc(), F.col("event_id").desc())
latest = bronze.withColumn("rn", F.row_number().over(window)).filter("rn = 1").drop("rn")
latest.createOrReplaceTempView("latest_cdc_events")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {silver_table} (
  order_id STRING, customer_id STRING, order_date DATE, amount DOUBLE
) USING DELTA
""")

target = DeltaTable.forName(spark, silver_table)
(
    target.alias("t").merge(latest.alias("s"), "t.order_id = s.order_id")
    .whenMatchedDelete(condition="s.operation = 'D'")
    .whenMatchedUpdate(
        condition="s.operation IN ('I','U')",
        set={"customer_id": "s.customer_id",
             "order_date": "CAST(s.order_date AS DATE)",
             "amount": "CAST(s.amount AS DOUBLE)"}
    )
    .whenNotMatchedInsert(
        condition="s.operation IN ('I','U')",
        values={"order_id": "s.order_id",
                "customer_id": "s.customer_id",
                "order_date": "CAST(s.order_date AS DATE)",
                "amount": "CAST(s.amount AS DOUBLE)"}
    )
    .execute()
)
