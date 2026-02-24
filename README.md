# SharkGraph — Deal Intelligence Web App

A network-based intelligence system that predicts Shark Tank outcomes and maps investor bias via a NetworkX graph.

## What It Does

- **Predicts deal probability** for a given pitch (industry, amount, equity, season)
- **Recommends likely sharks** using multi-label classification
- **Maps investor networks** — centrality, community detection, co-investment patterns
- **Explains predictions** with feature importance and rule-based drivers
- **Provides exec dashboards** via Tableau-ready data exports

## Architecture

```
Raw CSV → Python ETL → Postgres → Analytics Layer → ML + Graph → Web App + Tableau
```

## Quick Start

### 1. Start Postgres

```bash
make db-up
```

### 2. Run the full pipeline

```bash
make all    # ETL → Graph → ML
```

### 3. Launch the web app

```bash
make app    # Starts Streamlit on localhost:8501
```

### 4. Run tests

```bash
make test
```

## Project Structure

```
sharkgraph/
  config.py                    # Centralized configuration
  data/
    sample_pitches.csv         # Sample dataset (30 pitches)
  sql/
    schema.sql                 # Postgres schema (dims + facts + bridge)
    views/                     # SQL views for analytics
    marts/                     # Materialized mart tables
  etl/
    ingest.py                  # Step 1: Read raw CSV
    transform.py               # Step 2: Clean, parse, reshape
    load.py                    # Step 3: Load into Postgres
    dq_checks.py               # Step 4: Data quality validation
  modeling/
    train_deal_model.py        # Deal probability classifier
    train_shark_model.py       # Shark recommender (one-vs-rest)
    evaluate.py                # Model evaluation + model card
  graph/
    build_graph.py             # Build NetworkX graph
    compute_metrics.py         # Centrality + community detection
    export_graph_tables.py     # Export to Postgres/CSV
  app/
    app.py                     # Streamlit main page
    pages/
      1_Pitch_Predictor.py     # Deal probability + shark ranking
      2_Network_Explorer.py    # Interactive graph visualization
      3_Shark_Profiles.py      # Shark bias cards
      4_Data_Quality.py        # DQ dashboard
  tableau/
    export_for_tableau.py      # Export marts as CSV
    README_tableau.md          # Tableau setup instructions
  reports/                     # Generated reports (DQ, model card)
  tests/
    test_dq.py                 # Data quality tests
    test_features.py           # Feature engineering + graph tests
```

## Database Schema

Star-ish schema with:
- `dim_shark`, `dim_episode`, `dim_industry`, `dim_company`
- `fact_pitch` (one row per pitch)
- `bridge_pitch_shark` (shark participation per pitch)
- `graph_node_metrics`, `graph_edges` (network analysis output)

## ML Models

| Model | Target | Approach | Metrics |
|-------|--------|----------|---------|
| Deal Model | `deal_made` (0/1) | Logistic Regression / Gradient Boosting | AUC-ROC, F1 |
| Shark Model | Which shark(s) invest | One-vs-Rest Logistic Regression | Precision@k |

## Network Graph

- **Nodes:** Sharks, Industries, Companies
- **Edges:** Investment links, industry associations, co-investment ties
- **Metrics:** Degree centrality, betweenness centrality, closeness centrality, Louvain communities
