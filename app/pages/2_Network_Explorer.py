"""Page 2: Network Explorer — Interactive graph visualization."""

import os
import pickle
import sys
import tempfile

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import MODELS_DIR

st.header("Network Explorer")

GRAPH_PATH = os.path.join(MODELS_DIR, "sharkgraph.gpickle")
METRICS_PATH = os.path.join(MODELS_DIR, "graph_metrics.csv")


@st.cache_resource
def load_graph():
    import networkx as nx
    with open(GRAPH_PATH, "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_metrics():
    return pd.read_csv(METRICS_PATH)


try:
    G = load_graph()
    metrics_df = load_metrics()
except FileNotFoundError:
    st.error("Graph not built yet. Run `make graph` first.")
    st.stop()

# Filters
col1, col2 = st.columns(2)
with col1:
    node_types = st.multiselect(
        "Node types",
        ["shark", "industry", "company"],
        default=["shark", "industry"],
    )
with col2:
    min_degree = st.slider("Min degree centrality", 0.0, 1.0, 0.0, 0.01)

# Filter metrics
filtered = metrics_df[
    (metrics_df["node_type"].isin(node_types))
    & (metrics_df["degree_centrality"] >= min_degree)
]

# Build subgraph for visualization
import networkx as nx

visible_nodes = set(filtered["node_name"].tolist())
subG = G.subgraph(visible_nodes).copy()

if subG.number_of_nodes() == 0:
    st.warning("No nodes match the current filters.")
    st.stop()

# Layout
pos = nx.spring_layout(subG, seed=42, k=2.0)

# Color map
color_map = {"shark": "#FF6B6B", "industry": "#4ECDC4", "company": "#95E1D3"}
size_map = {"shark": 20, "industry": 15, "company": 10}

# Build plotly figure
edge_x, edge_y = [], []
for u, v in subG.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.8, color="#888"),
    hoverinfo="none",
    mode="lines",
)

node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
for node in subG.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    ntype = G.nodes[node].get("node_type", "unknown")
    node_color.append(color_map.get(ntype, "#999"))
    node_size.append(size_map.get(ntype, 8))

    # Hover text with metrics
    row = filtered[filtered["node_name"] == node]
    if len(row) > 0:
        r = row.iloc[0]
        node_text.append(
            f"{node}<br>Type: {ntype}<br>"
            f"Degree: {r['degree_centrality']:.4f}<br>"
            f"Betweenness: {r['betweenness_centrality']:.4f}<br>"
            f"Community: {r.get('community_id', 'N/A')}"
        )
    else:
        node_text.append(node)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode="markers+text",
    hoverinfo="text",
    text=[n if G.nodes[n].get("node_type") == "shark" else "" for n in subG.nodes()],
    textposition="top center",
    textfont=dict(size=9),
    hovertext=node_text,
    marker=dict(color=node_color, size=node_size, line=dict(width=1, color="#333")),
)

fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        title="SharkGraph Network",
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=650,
        margin=dict(l=20, r=20, t=40, b=20),
    ),
)

st.plotly_chart(fig, use_container_width=True)

# Node details on click
st.subheader("Node Metrics")
selected_node = st.selectbox("Select a node to inspect", sorted(visible_nodes))
if selected_node:
    row = filtered[filtered["node_name"] == selected_node]
    if len(row) > 0:
        r = row.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Degree Centrality", f"{r['degree_centrality']:.4f}")
        c2.metric("Betweenness Centrality", f"{r['betweenness_centrality']:.4f}")
        c3.metric("Closeness Centrality", f"{r['closeness_centrality']:.4f}")

        neighbors = list(G.neighbors(selected_node))
        st.write(f"**Connected to:** {', '.join(sorted(neighbors)[:15])}")
        if len(neighbors) > 15:
            st.write(f"... and {len(neighbors) - 15} more")

# Legend
st.markdown("""
**Legend:**
- 🔴 Sharks | 🟢 Industries | 🟩 Companies
""")
