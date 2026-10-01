WITH base AS (
  SELECT customer_id,
         (SELECT MAX(order_day) FROM fact_sales) - MAX(order_day) AS recency_days,
         COUNT(DISTINCT order_id) AS frequency,
         ROUND(CAST(SUM(revenue) AS NUMERIC), 2) AS monetary
  FROM fact_sales GROUP BY customer_id
), scored AS (
  SELECT *,
         NTILE(4) OVER (ORDER BY recency_days DESC) AS r,
         NTILE(4) OVER (ORDER BY frequency)         AS f,
         NTILE(4) OVER (ORDER BY monetary)          AS m
  FROM base
)
SELECT customer_id,
       recency_days,
       frequency,
       monetary,
       r, f, m,
       CASE WHEN r >= 3 AND f >= 3 THEN 'Champions'
            WHEN r >= 3             THEN 'Active'
            WHEN f >= 3             THEN 'At risk'
            ELSE 'Dormant' END AS segment
FROM scored
