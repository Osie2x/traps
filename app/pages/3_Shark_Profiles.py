"""Page 3: Shark Profiles — bias cards per shark."""

import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import MODELS_DIR
from etl.transform import transform

st.header("Shark Profiles")


@st.cache_data
def load_data():
    tables = transform()
    fp = tables["fact_pitch"]
    bridge = tables["bridge_pitch_shark"]
    dim_shark = tables["dim_shark"]
    dim_company = tables["dim_company"]
    dim_industry = tables["dim_industry"]
    dim_episode = tables["dim_episode"]

    # Build shark stats
    shark_map = dict(zip(dim_shark["shark_id"], dim_shark["name"]))
    company_industry = dim_company.merge(dim_industry, on="industry_id")
    pitch_info = fp.merge(company_industry[["company_id", "industry_name"]], on="company_id", how="left")
    pitch_info = pitch_info.merge(dim_episode[["episode_id", "season"]], on="episode_id", how="left")

    bridge_full = bridge.copy()
    bridge_full["shark_name"] = bridge_full["shark_id"].map(shark_map)
    bridge_full = bridge_full.merge(
        pitch_info[["pitch_id", "industry_name", "season", "asked_amount", "asked_equity"]],
        on="pitch_id",
        how="left",
    )

    return bridge_full, sorted(dim_shark["name"].tolist())


# Load graph metrics if available
@st.cache_data
def load_graph_metrics():
    path = os.path.join(MODELS_DIR, "graph_metrics.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None


bridge_full, shark_names = load_data()
graph_metrics = load_graph_metrics()

# Select shark
selected_shark = st.selectbox("Select Shark", shark_names)

shark_data = bridge_full[bridge_full["shark_name"] == selected_shark]
invested_data = shark_data[shark_data["invested"] == 1]

# Bias card
st.subheader(f"{selected_shark} — Bias Card")

col1, col2, col3 = st.columns(3)
col1.metric("Deals Seen", len(shark_data))
col2.metric("Investments Made", len(invested_data))
col3.metric("Deal Rate", f"{len(invested_data) / max(len(shark_data), 1):.0%}")

col4, col5 = st.columns(2)
if len(invested_data) > 0:
    col4.metric("Avg Equity Taken", f"{invested_data['offer_equity'].mean():.1%}")
    col5.metric("Avg Offer Amount", f"${invested_data['offer_amount'].mean():,.0f}")

# Graph metrics
if graph_metrics is not None:
    shark_graph = graph_metrics[
        (graph_metrics["node_name"] == selected_shark) & (graph_metrics["node_type"] == "shark")
    ]
    if len(shark_graph) > 0:
        r = shark_graph.iloc[0]
        st.subheader("Network Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Degree Centrality", f"{r['degree_centrality']:.4f}")
        c2.metric("Betweenness Centrality", f"{r['betweenness_centrality']:.4f}")
        c3.metric("Closeness Centrality", f"{r['closeness_centrality']:.4f}")

# Industry preference
st.subheader("Industry Preference")
if len(invested_data) > 0:
    ind_counts = invested_data["industry_name"].value_counts().reset_index()
    ind_counts.columns = ["Industry", "Investments"]
    fig = px.bar(ind_counts, x="Industry", y="Investments", title=f"{selected_shark}'s Investments by Industry")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No investments recorded for this shark.")

# Trend over seasons
st.subheader("Investment Trend by Season")
if len(shark_data) > 0:
    season_stats = shark_data.groupby("season").agg(
        deals_seen=("invested", "count"),
        investments=("invested", "sum"),
    ).reset_index()
    season_stats["deal_rate"] = season_stats["investments"] / season_stats["deals_seen"]

    fig2 = px.line(
        season_stats, x="season", y="deal_rate",
        markers=True, title=f"{selected_shark}'s Deal Rate by Season",
    )
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, use_container_width=True)
