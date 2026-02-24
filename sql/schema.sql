-- SharkGraph Database Schema
-- Star-ish schema for Shark Tank deal intelligence

CREATE TABLE IF NOT EXISTS dim_shark (
    shark_id   SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_episode (
    episode_id     SERIAL PRIMARY KEY,
    season         INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    air_date       DATE,
    UNIQUE (season, episode_number)
);

CREATE TABLE IF NOT EXISTS dim_industry (
    industry_id     SERIAL PRIMARY KEY,
    industry_name   VARCHAR(150) NOT NULL UNIQUE,
    parent_industry VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS dim_company (
    company_id   SERIAL PRIMARY KEY,
    company_name VARCHAR(250) NOT NULL,
    industry_id  INTEGER REFERENCES dim_industry(industry_id),
    location     VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS fact_pitch (
    pitch_id         SERIAL PRIMARY KEY,
    episode_id       INTEGER REFERENCES dim_episode(episode_id),
    company_id       INTEGER REFERENCES dim_company(company_id),
    asked_amount     NUMERIC(15,2),
    asked_equity     NUMERIC(5,4),
    valuation_asked  NUMERIC(15,2),
    deal_made        SMALLINT NOT NULL DEFAULT 0 CHECK (deal_made IN (0,1)),
    deal_amount      NUMERIC(15,2),
    deal_equity      NUMERIC(5,4),
    multi_shark      SMALLINT DEFAULT 0 CHECK (multi_shark IN (0,1)),
    description_text TEXT,
    location         VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS bridge_pitch_shark (
    pitch_id     INTEGER REFERENCES fact_pitch(pitch_id),
    shark_id     INTEGER REFERENCES dim_shark(shark_id),
    invested     SMALLINT NOT NULL DEFAULT 0 CHECK (invested IN (0,1)),
    offer_amount NUMERIC(15,2),
    offer_equity NUMERIC(5,4),
    PRIMARY KEY (pitch_id, shark_id)
);

-- Network graph export tables (populated by Python pipeline)
CREATE TABLE IF NOT EXISTS graph_node_metrics (
    node_name           VARCHAR(250) NOT NULL,
    node_type           VARCHAR(50)  NOT NULL,  -- 'shark', 'industry', 'company'
    degree_centrality   NUMERIC(8,6),
    betweenness_centrality NUMERIC(8,6),
    closeness_centrality   NUMERIC(8,6),
    community_id        INTEGER,
    PRIMARY KEY (node_name, node_type)
);

CREATE TABLE IF NOT EXISTS graph_edges (
    source      VARCHAR(250) NOT NULL,
    target      VARCHAR(250) NOT NULL,
    edge_type   VARCHAR(50),  -- 'invested', 'industry_link', 'co_invested'
    weight      NUMERIC(10,4) DEFAULT 1
);
