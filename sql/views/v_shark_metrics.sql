-- View: shark-level aggregated metrics
CREATE OR REPLACE VIEW v_shark_metrics AS
SELECT
    ds.shark_id,
    ds.name AS shark_name,
    COUNT(DISTINCT bps.pitch_id) AS pitches_seen,
    SUM(bps.invested) AS investments_made,
    ROUND(AVG(bps.invested)::NUMERIC, 4) AS deal_rate,
    ROUND(AVG(CASE WHEN bps.invested = 1 THEN bps.offer_equity END), 4) AS avg_equity_taken,
    ROUND(AVG(CASE WHEN bps.invested = 1 THEN bps.offer_amount END), 2) AS avg_offer_amount
FROM dim_shark ds
JOIN bridge_pitch_shark bps ON ds.shark_id = bps.shark_id
GROUP BY ds.shark_id, ds.name;
