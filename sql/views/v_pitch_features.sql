-- View: one row per pitch with computed features
CREATE OR REPLACE VIEW v_pitch_features AS
SELECT
    fp.pitch_id,
    fp.episode_id,
    de.season,
    de.episode_number,
    fp.company_id,
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
        THEN (fp.deal_amount / fp.deal_equity)
        ELSE NULL
    END AS deal_valuation,
    CASE
        WHEN fp.deal_made = 1 AND fp.valuation_asked > 0
        THEN ((fp.deal_amount / NULLIF(fp.deal_equity, 0)) - fp.valuation_asked)
              / fp.valuation_asked
        ELSE NULL
    END AS discount_to_asked,
    fp.multi_shark,
    fp.location
FROM fact_pitch fp
JOIN dim_episode de ON fp.episode_id = de.episode_id
JOIN dim_company dc ON fp.company_id = dc.company_id
JOIN dim_industry di ON dc.industry_id = di.industry_id;
