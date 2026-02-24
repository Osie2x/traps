"""Tests for feature engineering and graph pipeline."""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from etl.transform import transform, _parse_money, _parse_equity
from graph.build_graph import build_graph
from graph.compute_metrics import compute_metrics


# --- Parse helper tests ---

def test_parse_money_plain_number():
    assert _parse_money("100000") == 100000.0


def test_parse_money_dollar_sign():
    assert _parse_money("$250000") == 250000.0


def test_parse_money_with_commas():
    assert _parse_money("$1,000,000") == 1000000.0


def test_parse_money_k_suffix():
    assert _parse_money("100k") == 100000.0


def test_parse_money_m_suffix():
    assert _parse_money("1.5M") == 1500000.0


def test_parse_money_nan():
    assert np.isnan(_parse_money(np.nan))


def test_parse_equity_percentage():
    assert _parse_equity("20%") == 0.20


def test_parse_equity_decimal():
    assert _parse_equity("0.15") == 0.15


def test_parse_equity_nan():
    assert np.isnan(_parse_equity(np.nan))


# --- Transform tests ---

def test_valuation_asked_computed():
    tables = transform()
    fp = tables["fact_pitch"]
    # Check that valuation_asked = asked_amount / asked_equity where equity > 0
    for _, row in fp.iterrows():
        if row["asked_equity"] > 0 and not np.isnan(row["valuation_asked"]):
            expected = row["asked_amount"] / row["asked_equity"]
            assert abs(row["valuation_asked"] - expected) < 0.01


def test_dim_industry_has_parent():
    tables = transform()
    di = tables["dim_industry"]
    assert "parent_industry" in di.columns
    assert di["parent_industry"].notna().any()


# --- Graph tests ---

def test_graph_builds():
    tables = transform()
    G = build_graph(tables)
    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0


def test_graph_has_shark_nodes():
    tables = transform()
    G = build_graph(tables)
    shark_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "shark"]
    assert len(shark_nodes) > 0


def test_graph_has_industry_nodes():
    tables = transform()
    G = build_graph(tables)
    industry_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "industry"]
    assert len(industry_nodes) > 0


def test_metrics_computed():
    tables = transform()
    G = build_graph(tables)
    metrics = compute_metrics(G)
    assert len(metrics) > 0
    assert "degree_centrality" in metrics.columns
    assert "betweenness_centrality" in metrics.columns
    assert "closeness_centrality" in metrics.columns


def test_metrics_values_valid():
    tables = transform()
    G = build_graph(tables)
    metrics = compute_metrics(G)
    assert (metrics["degree_centrality"] >= 0).all()
    assert (metrics["degree_centrality"] <= 1).all()
    assert (metrics["betweenness_centrality"] >= 0).all()
