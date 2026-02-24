-- Materialized mart: one row per pitch with all features for ML + Tableau
DROP TABLE IF EXISTS mart_pitch_features;
CREATE TABLE mart_pitch_features AS
SELECT
    fp.pitch_id,
    de.season,
    de.episode_number,
    dc.company_name,
    di.industry_name,
    fp.asked_amount,
    fp.asked_equity,
    fp.valuation_asked,
    fp.deal_made,
    fp.deal_amount,
    fp.deal_equity,
    CASE
        WHEN fp.deal_made = 1 AND fp.deal_equity > 0
        THEN ROUND((fp.deal_amount / fp.deal_equity)::NUMERIC, 2)
        ELSE NULL
    END AS deal_valuation,
    fp.multi_shark,
    fp.location,
    -- industry-level aggregates
    ind_stats.avg_asked_amount AS industry_avg_asked,
    CASE
        WHEN ind_stats.avg_asked_amount > 0
        THEN ROUND((fp.asked_amount / ind_stats.avg_asked_amount)::NUMERIC, 4)
        ELSE NULL
    END AS capital_intensity
FROM fact_pitch fp
JOIN dim_episode de   ON fp.episode_id = de.episode_id
JOIN dim_company dc   ON fp.company_id = dc.company_id
JOIN dim_industry di  ON dc.industry_id = di.industry_id
LEFT JOIN (
    SELECT di2.industry_id,
           ROUND(AVG(fp2.asked_amount)::NUMERIC, 2) AS avg_asked_amount
    FROM fact_pitch fp2
    JOIN dim_company dc2 ON fp2.company_id = dc2.company_id
    JOIN dim_industry di2 ON dc2.industry_id = di2.industry_id
    GROUP BY di2.industry_id
) ind_stats ON di.industry_id = ind_stats.industry_id;
