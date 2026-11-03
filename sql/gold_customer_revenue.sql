-- Databricks SQL STARTER: run only after staging a customer dimension
-- and the silver_orders Delta table in your own configured catalog.
-- Replace catalog and schema placeholders before executing.
CREATE OR REPLACE VIEW YOUR_CATALOG.YOUR_SCHEMA.gold_customer_revenue AS
SELECT
  c.customer_id,
  c.customer_name,
  c.region,
  COUNT(o.order_id) AS order_count,
  COALESCE(SUM(o.amount), 0) AS revenue
FROM YOUR_CATALOG.YOUR_SCHEMA.dim_customers c
LEFT JOIN YOUR_CATALOG.YOUR_SCHEMA.silver_orders o
  ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.region;
