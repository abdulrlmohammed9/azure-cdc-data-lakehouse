-- Phase 3 — reusable Databricks SQL verification queries.
-- Execute each SELECT separately in Databricks SQL Editor with your
-- Serverless Starter Warehouse selected. These queries DO NOT change data.

-- A. Raw event count must be 5
SELECT COUNT(*) AS bronze_events
FROM workspace.cdc_portfolio.bronze_order_events;

-- B. Expect 2 active orders, 1 deleted tombstone, 3 Silver keys
SELECT COUNT(*) AS silver_keys,
       SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_orders,
       SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS tombstones
FROM workspace.cdc_portfolio.silver_orders;

-- C. Inspect CDC sequence and delete state
SELECT order_id, amount, last_sequence, is_deleted
FROM workspace.cdc_portfolio.silver_orders
ORDER BY order_id;

-- D. Expect C001=125.00, C002=0.00, C003=40.00
SELECT customer_id, customer_name, region, order_count, revenue
FROM workspace.cdc_portfolio.gold_customer_revenue
ORDER BY customer_id;

-- E. Expect total_orders=2, total_revenue=165.00
SELECT SUM(order_count) AS total_orders,
       SUM(revenue) AS total_revenue
FROM workspace.cdc_portfolio.gold_customer_revenue;
