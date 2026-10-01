SELECT service_name,
       COUNT(log_id) AS total_requests,
       ROUND(CAST(AVG(latency_ms) AS NUMERIC), 2) AS avg_latency_ms,
       ROUND(CAST(SUM(compute_cost) AS NUMERIC), 2) AS total_cost_usd,
       SUM(error_count) AS total_errors,
       ROUND(CAST(100.0 * SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) / COUNT(*) AS NUMERIC), 2) AS error_rate_pct
FROM fact_hitech_telemetry
GROUP BY service_name
