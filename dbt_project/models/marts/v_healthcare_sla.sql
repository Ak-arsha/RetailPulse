SELECT claim_type,
       COUNT(claim_id) AS total_claims,
       ROUND(CAST(AVG(claim_amount) AS NUMERIC), 2) AS avg_claim_amount,
       ROUND(CAST(AVG(processing_hours) AS NUMERIC), 1) AS avg_processing_hours,
       ROUND(CAST(100.0 * SUM(CASE WHEN processing_hours > 24.0 THEN 1 ELSE 0 END) / COUNT(*) AS NUMERIC), 1) AS sla_breach_pct,
       ROUND(CAST(100.0 * SUM(CASE WHEN readmitted = 1 THEN 1 ELSE 0 END) / COUNT(*) AS NUMERIC), 1) AS readmission_rate_pct
FROM fact_healthcare_claims
GROUP BY claim_type
