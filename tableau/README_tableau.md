# Tableau Dashboard Setup

## Data Sources

Connect Tableau to the following tables/CSVs:

### Option A: Direct Postgres Connection
- **Host:** localhost:5432
- **Database:** sharkgraph
- **Tables:**
  - `mart_pitch_features` — one row per pitch with computed features
  - `mart_shark_metrics` — one row per shark x season x industry
  - `mart_network_edges` — network edges for graph visualization
  - `graph_node_metrics` — node centrality scores

### Option B: CSV Files
Run `python graph/export_graph_tables.py` to generate:
- `reports/graph_node_metrics.csv`
- `reports/graph_edges.csv`

Also export marts:
```sql
\copy (SELECT * FROM mart_pitch_features) TO 'reports/mart_pitch_features.csv' CSV HEADER;
\copy (SELECT * FROM mart_shark_metrics) TO 'reports/mart_shark_metrics.csv' CSV HEADER;
```

## Dashboard Tabs

### Tab 1: Deal Drivers Overview
- Deal rate by industry (bar chart)
- Deal rate by season (line chart)
- Asked vs accepted terms scatter plot
- Distribution of valuations (histogram)

### Tab 2: Shark Behavior
- Shark deal rate trend by season (line, color by shark)
- Avg equity taken by industry (heatmap)
- Investment count by shark (bar)

### Tab 3: Portfolio Network Summary
- Top industries by shark investment count (stacked bar)
- Community clusters from network analysis (table/treemap)
- Node centrality rankings (table)

## Filters
- Season range slider
- Industry multi-select
- Shark multi-select
