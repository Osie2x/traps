"""Compute network centrality metrics and community detection."""

import os
import pickle
import sys

import networkx as nx
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MODELS_DIR

try:
    from community import community_louvain
except ImportError:
    community_louvain = None

GRAPH_PATH = os.path.join(MODELS_DIR, "sharkgraph.gpickle")
METRICS_PATH = os.path.join(MODELS_DIR, "graph_metrics.csv")


def load_graph() -> nx.Graph:
    with open(GRAPH_PATH, "rb") as f:
        return pickle.load(f)


def compute_metrics(G: nx.Graph | None = None) -> pd.DataFrame:
    """Compute centrality metrics for all nodes."""
    if G is None:
        G = load_graph()

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)

    # Community detection
    communities = {}
    if community_louvain is not None:
        try:
            communities = community_louvain.best_partition(G)
        except Exception:
            communities = {}

    rows = []
    for node in G.nodes():
        rows.append({
            "node_name": node,
            "node_type": G.nodes[node].get("node_type", "unknown"),
            "degree_centrality": round(degree.get(node, 0), 6),
            "betweenness_centrality": round(betweenness.get(node, 0), 6),
            "closeness_centrality": round(closeness.get(node, 0), 6),
            "community_id": communities.get(node),
        })

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(METRICS_PATH, index=False)
    print(f"Computed metrics for {len(metrics_df)} nodes -> {METRICS_PATH}")

    # Print shark metrics summary
    sharks = metrics_df[metrics_df["node_type"] == "shark"].sort_values(
        "degree_centrality", ascending=False
    )
    if len(sharks) > 0:
        print("\nShark Centrality Rankings:")
        print(sharks[["node_name", "degree_centrality", "betweenness_centrality"]].to_string(index=False))

    return metrics_df


if __name__ == "__main__":
    compute_metrics()
