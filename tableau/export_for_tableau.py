"""Export all mart tables and graph data as CSVs for Tableau."""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REPORTS_DIR
from etl.transform import transform
from graph.build_graph import build_graph
from graph.compute_metrics import compute_metrics


def export_all():
    """Run pipeline and export everything to CSV for Tableau."""
    tables = transform()

    # Build graph and metrics
    G = build_graph(tables)
    metrics_df = compute_metrics(G)

    # Export graph data
    from graph.export_graph_tables import export_to_csv
    export_to_csv()

    # Export feature mart
    fp = tables["fact_pitch"]
    dim_company = tables["dim_company"]
    dim_industry = tables["dim_industry"]
    dim_episode = tables["dim_episode"]

    mart_pitch = fp.merge(dim_company[["company_id", "company_name", "industry_id"]], on="company_id", how="left")
    mart_pitch = mart_pitch.merge(dim_industry[["industry_id", "industry_name"]], on="industry_id", how="left")
    mart_pitch = mart_pitch.merge(dim_episode[["episode_id", "season", "episode_number"]], on="episode_id", how="left")
    mart_pitch.to_csv(os.path.join(REPORTS_DIR, "mart_pitch_features.csv"), index=False)

    # Export shark metrics mart
    bridge = tables["bridge_pitch_shark"]
    dim_shark = tables["dim_shark"]
    shark_map = dict(zip(dim_shark["shark_id"], dim_shark["name"]))

    bridge_full = bridge.copy()
    bridge_full["shark_name"] = bridge_full["shark_id"].map(shark_map)
    bridge_full = bridge_full.merge(
        mart_pitch[["pitch_id", "industry_name", "season"]],
        on="pitch_id",
        how="left",
    )

    mart_shark = bridge_full.groupby(["shark_name", "season", "industry_name"]).agg(
        pitches_seen=("invested", "count"),
        investments=("invested", "sum"),
        avg_equity=("offer_equity", "mean"),
        avg_amount=("offer_amount", "mean"),
    ).reset_index()
    mart_shark["invest_rate"] = mart_shark["investments"] / mart_shark["pitches_seen"]
    mart_shark.to_csv(os.path.join(REPORTS_DIR, "mart_shark_metrics.csv"), index=False)

    print(f"All exports written to {REPORTS_DIR}/")
    print("Files: mart_pitch_features.csv, mart_shark_metrics.csv, graph_node_metrics.csv, graph_edges.csv")


if __name__ == "__main__":
    export_all()
