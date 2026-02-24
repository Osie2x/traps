-- Materialized mart: one row per shark x season x industry
DROP TABLE IF EXISTS mart_shark_metrics;
CREATE TABLE mart_shark_metrics AS
SELECT
    ds.shark_id,
    ds.name AS shark_name,
    de.season,
    di.industry_name,
    COUNT(DISTINCT bps.pitch_id) AS pitches_seen,
    SUM(bps.invested) AS investments_made,
    ROUND(AVG(bps.invested)::NUMERIC, 4) AS invest_rate,
    ROUND(AVG(CASE WHEN bps.invested = 1 THEN bps.offer_equity END), 4) AS avg_equity_taken,
    ROUND(AVG(CASE WHEN bps.invested = 1 THEN bps.offer_amount END), 2) AS avg_offer_amount
FROM bridge_pitch_shark bps
JOIN dim_shark ds     ON bps.shark_id = ds.shark_id
JOIN fact_pitch fp    ON bps.pitch_id = fp.pitch_id
JOIN dim_episode de   ON fp.episode_id = de.episode_id
JOIN dim_company dc   ON fp.company_id = dc.company_id
JOIN dim_industry di  ON dc.industry_id = di.industry_id
GROUP BY ds.shark_id, ds.name, de.season, di.industry_name;
