-- ==========================================================
-- RETAIL ANALYTICS VIEWS
-- ==========================================================
DROP VIEW IF EXISTS v_monthly_revenue;
CREATE VIEW v_monthly_revenue AS
SELECT order_month,
       SUM(revenue)                AS revenue,
       COUNT(DISTINCT order_id)    AS orders,
       COUNT(DISTINCT customer_id) AS customers
FROM fact_sales GROUP BY order_month;

DROP VIEW IF EXISTS v_category_performance;
CREATE VIEW v_category_performance AS
SELECT p.category,
       SUM(f.revenue)  AS revenue,
       SUM(f.quantity) AS units,
       ROUND(100.0 * SUM(f.revenue) / (SELECT SUM(revenue) FROM fact_sales), 1) AS revenue_share_pct
FROM fact_sales f JOIN dim_product p USING (product_id)
GROUP BY p.category;

DROP VIEW IF EXISTS v_customer_rfm;
CREATE VIEW v_customer_rfm AS
WITH base AS (
  SELECT customer_id,
         (SELECT MAX(order_day) FROM fact_sales) - MAX(order_day) AS recency_days,
         COUNT(DISTINCT order_id) AS frequency,
         ROUND(SUM(revenue), 2)   AS monetary
  FROM fact_sales GROUP BY customer_id
), scored AS (
  SELECT *,
         NTILE(4) OVER (ORDER BY recency_days DESC) AS r,
         NTILE(4) OVER (ORDER BY frequency)         AS f,
         NTILE(4) OVER (ORDER BY monetary)          AS m
  FROM base
)
SELECT *,
       CASE WHEN r >= 3 AND f >= 3 THEN 'Champions'
            WHEN r >= 3             THEN 'Active'
            WHEN f >= 3             THEN 'At risk'
            ELSE 'Dormant' END AS segment
FROM scored;

DROP VIEW IF EXISTS v_repeat_customers;
CREATE VIEW v_repeat_customers AS
SELECT ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct
FROM (SELECT customer_id, COUNT(DISTINCT order_id) AS n FROM fact_sales GROUP BY customer_id);


-- ==========================================================
-- SAAS ANALYTICS VIEWS
-- ==========================================================
DROP VIEW IF EXISTS v_saas_metrics;
CREATE VIEW v_saas_metrics AS
SELECT tier,
       COUNT(customer_id) AS total_customers,
       ROUND(SUM(mrr), 2) AS total_mrr,
       ROUND(AVG(mrr), 2) AS avg_mrr,
       ROUND(100.0 * SUM(CASE WHEN churned = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS churn_rate_pct
FROM fact_saas_subscriptions
GROUP BY tier;


-- ==========================================================
-- HEALTHCARE ANALYTICS VIEWS
-- ==========================================================
DROP VIEW IF EXISTS v_healthcare_sla;
CREATE VIEW v_healthcare_sla AS
SELECT claim_type,
       COUNT(claim_id) AS total_claims,
       ROUND(AVG(claim_amount), 2) AS avg_claim_amount,
       ROUND(AVG(processing_hours), 1) AS avg_processing_hours,
       ROUND(100.0 * SUM(CASE WHEN processing_hours > 24.0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS sla_breach_pct,
       ROUND(100.0 * SUM(CASE WHEN readmitted = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS readmission_rate_pct
FROM fact_healthcare_claims
GROUP BY claim_type;


-- ==========================================================
-- HI-TECH TELEMETRY VIEWS
-- ==========================================================
DROP VIEW IF EXISTS v_hitech_telemetry;
CREATE VIEW v_hitech_telemetry AS
SELECT service_name,
       COUNT(log_id) AS total_requests,
       ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
       ROUND(SUM(compute_cost), 2) AS total_cost_usd,
       SUM(error_count) AS total_errors,
       ROUND(100.0 * SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS error_rate_pct
FROM fact_hitech_telemetry
GROUP BY service_name;
