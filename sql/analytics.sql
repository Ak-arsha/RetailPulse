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
FROM (SELECT customer_id, COUNT(DISTINCT order_id) AS n FROM fact_sales GROUP BY customer_id)
