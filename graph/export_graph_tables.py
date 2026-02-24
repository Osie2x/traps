"""Export graph metrics and edges to Postgres for Tableau and app use."""

import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_URL, MODELS_DIR
from graph.compute_metrics import load_graph

METRICS_PATH = os.path.join(MODELS_DIR, "graph_metrics.csv")


def export_to_db(db_url: str | None = None):
    """Write graph_node_metrics and graph_edges tables to Postgres."""
    if db_url is None:
        db_url = DATABASE_URL

    engine = create_engine(db_url)
    G = load_graph()

    # --- Node metrics ---
    metrics_df = pd.read_csv(METRICS_PATH)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE graph_node_metrics"))
        metrics_df.to_sql("graph_node_metrics", conn, if_exists="append", index=False)
    print(f"Exported {len(metrics_df)} node metrics")

    # --- Edges ---
    edge_rows = []
    for u, v, data in G.edges(data=True):
        edge_rows.append({
            "source": u,
            "target": v,
            "edge_type": data.get("edge_type", "unknown"),
            "weight": data.get("weight", 1),
        })
    edges_df = pd.DataFrame(edge_rows)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE graph_edges"))
        edges_df.to_sql("graph_edges", conn, if_exists="append", index=False)
    print(f"Exported {len(edges_df)} edges")

    # Rebuild mart
    mart_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", "marts", "mart_network_edges.sql")
    if os.path.exists(mart_path):
        with engine.begin() as conn:
            with open(mart_path) as f:
                sql = f.read()
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
        print("Rebuilt mart_network_edges")


def export_to_csv():
    """Export graph data as CSVs (for Tableau without DB connection)."""
    metrics_df = pd.read_csv(METRICS_PATH)
    G = load_graph()

    edge_rows = []
    for u, v, data in G.edges(data=True):
        edge_rows.append({
            "source": u,
            "target": v,
            "edge_type": data.get("edge_type", "unknown"),
            "weight": data.get("weight", 1),
        })
    edges_df = pd.DataFrame(edge_rows)

    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    metrics_df.to_csv(os.path.join(reports_dir, "graph_node_metrics.csv"), index=False)
    edges_df.to_csv(os.path.join(reports_dir, "graph_edges.csv"), index=False)
    print(f"Exported CSVs to {reports_dir}/")


if __name__ == "__main__":
    export_to_csv()
    print("CSV export complete. Run with --db flag for Postgres export.")
    if "--db" in sys.argv:
        export_to_db()
