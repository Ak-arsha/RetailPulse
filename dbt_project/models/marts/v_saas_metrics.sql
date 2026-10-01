SELECT tier,
       COUNT(customer_id) AS total_customers,
       ROUND(CAST(SUM(mrr) AS NUMERIC), 2) AS total_mrr,
       ROUND(CAST(AVG(mrr) AS NUMERIC), 2) AS avg_mrr,
       ROUND(CAST(100.0 * SUM(CASE WHEN churned = 1 THEN 1 ELSE 0 END) / COUNT(*) AS NUMERIC), 1) AS churn_rate_pct
FROM fact_saas_subscriptions
GROUP BY tier
