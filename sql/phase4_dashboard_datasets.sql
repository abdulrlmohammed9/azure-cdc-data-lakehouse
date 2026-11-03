-- Phase 4: Databricks AI/BI dashboard read-only datasets.
-- Use one SELECT per dashboard dataset in the Data tab.
-- The following data is synthetic and requires workspace.cdc_portfolio.
-- Dataset: kpi_summary
SELECT COALESCE(SUM(revenue), 0) AS total_revenue,
       COALESCE(SUM(order_count), 0) AS active_orders,
       (SELECT COUNT(*) FROM workspace.cdc_portfolio.silver_orders WHERE is_deleted = true) AS deleted_orders,
       (SELECT COUNT(*) FROM workspace.cdc_portfolio.bronze_order_events) AS total_cdc_events
FROM workspace.cdc_portfolio.gold_customer_revenue;

-- Dataset: revenue_by_region
SELECT region, SUM(revenue) AS revenue, SUM(order_count) AS active_orders
FROM workspace.cdc_portfolio.gold_customer_revenue
GROUP BY region ORDER BY revenue DESC;

-- Dataset: cdc_event_distribution
SELECT CASE operation WHEN 'I' THEN 'Insert' WHEN 'U' THEN 'Update'
                      WHEN 'D' THEN 'Delete' ELSE 'Other' END AS operation_type,
       COUNT(*) AS event_count
FROM workspace.cdc_portfolio.bronze_order_events
GROUP BY operation ORDER BY event_count DESC;

-- Dataset: customer_performance
SELECT customer_id, customer_name, region, order_count, revenue
FROM workspace.cdc_portfolio.gold_customer_revenue
ORDER BY revenue DESC, customer_id;

-- Dataset: silver_order_status
SELECT CASE WHEN is_deleted THEN 'Deleted' ELSE 'Active' END AS order_status,
       COUNT(*) AS order_count
FROM workspace.cdc_portfolio.silver_orders
GROUP BY is_deleted;
