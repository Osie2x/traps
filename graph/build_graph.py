"""Build the SharkGraph network from transformed data.

Nodes: Sharks, Industries, Companies
Edges:
  - Shark -> Company (invested=1)
  - Company -> Industry
  - Shark -> Industry (derived, weight = # investments)
"""

import os
import pickle
import sys

import networkx as nx
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MODELS_DIR
from etl.transform import transform


GRAPH_PATH = os.path.join(MODELS_DIR, "sharkgraph.gpickle")


def build_graph(tables: dict | None = None) -> nx.Graph:
    """Construct the multi-type network graph."""
    if tables is None:
        tables = transform()

    G = nx.Graph()

    dim_shark = tables["dim_shark"]
    dim_industry = tables["dim_industry"]
    dim_company = tables["dim_company"]
    fact_pitch = tables["fact_pitch"]
    bridge = tables["bridge_pitch_shark"]

    # Build lookup maps
    shark_map = dict(zip(dim_shark["shark_id"], dim_shark["name"]))
    company_map = dict(zip(dim_company["company_id"], dim_company["company_name"]))
    industry_map = dict(zip(dim_industry["industry_id"], dim_industry["industry_name"]))
    company_industry = dict(zip(dim_company["company_id"], dim_company["industry_id"]))

    # Add shark nodes
    for _, row in dim_shark.iterrows():
        G.add_node(row["name"], node_type="shark")

    # Add industry nodes
    for _, row in dim_industry.iterrows():
        G.add_node(row["industry_name"], node_type="industry")

    # Add company nodes
    for _, row in dim_company.iterrows():
        G.add_node(row["company_name"], node_type="company")
        # Company -> Industry edge
        ind_id = row["industry_id"]
        if ind_id in industry_map:
            G.add_edge(row["company_name"], industry_map[ind_id], edge_type="industry_link")

    # Shark -> Company edges (investments only)
    invested = bridge[bridge["invested"] == 1].copy()
    pitch_company = dict(zip(fact_pitch["pitch_id"], fact_pitch["company_id"]))

    for _, row in invested.iterrows():
        shark_name = shark_map.get(row["shark_id"])
        company_id = pitch_company.get(row["pitch_id"])
        company_name = company_map.get(company_id)
        if shark_name and company_name:
            G.add_edge(
                shark_name,
                company_name,
                edge_type="invested",
                amount=row.get("offer_amount"),
                equity=row.get("offer_equity"),
            )

    # Shark -> Industry derived edges (weighted by # investments)
    shark_industry_counts = {}
    for _, row in invested.iterrows():
        shark_name = shark_map.get(row["shark_id"])
        company_id = pitch_company.get(row["pitch_id"])
        ind_id = company_industry.get(company_id)
        ind_name = industry_map.get(ind_id)
        if shark_name and ind_name:
            key = (shark_name, ind_name)
            shark_industry_counts[key] = shark_industry_counts.get(key, 0) + 1

    for (shark_name, ind_name), count in shark_industry_counts.items():
        if G.has_edge(shark_name, ind_name):
            G[shark_name][ind_name]["weight"] = count
        else:
            G.add_edge(shark_name, ind_name, edge_type="shark_industry", weight=count)

    # Co-investment edges between sharks
    pitch_investors = invested.groupby("pitch_id")["shark_id"].apply(list)
    for investors in pitch_investors:
        if len(investors) < 2:
            continue
        names = [shark_map[sid] for sid in investors if sid in shark_map]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if G.has_edge(names[i], names[j]):
                    G[names[i]][names[j]]["weight"] = G[names[i]][names[j]].get("weight", 1) + 1
                else:
                    G.add_edge(names[i], names[j], edge_type="co_invested", weight=1)

    # Persist
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(G, f)
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Saved to {GRAPH_PATH}")

    return G


if __name__ == "__main__":
    build_graph()
