"""Tests for data quality checks."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from etl.transform import transform
from etl.dq_checks import run_dq_checks


def test_transform_returns_all_tables():
    tables = transform()
    expected = {"dim_shark", "dim_episode", "dim_industry", "dim_company", "fact_pitch", "bridge_pitch_shark"}
    assert set(tables.keys()) == expected


def test_transform_no_empty_tables():
    tables = transform()
    for name, df in tables.items():
        assert len(df) > 0, f"{name} is empty"


def test_pitch_ids_unique():
    tables = transform()
    fp = tables["fact_pitch"]
    assert fp["pitch_id"].is_unique


def test_asked_equity_valid_range():
    tables = transform()
    fp = tables["fact_pitch"]
    valid = fp["asked_equity"].dropna()
    assert (valid >= 0).all(), "asked_equity has negative values"
    assert (valid <= 1).all(), "asked_equity has values > 1"


def test_asked_amount_positive():
    tables = transform()
    fp = tables["fact_pitch"]
    valid = fp["asked_amount"].dropna()
    assert (valid > 0).all(), "asked_amount has non-positive values"


def test_no_deal_nullifies_terms():
    tables = transform()
    fp = tables["fact_pitch"]
    no_deal = fp[fp["deal_made"] == 0]
    assert no_deal["deal_amount"].isna().all(), "deal_amount should be null when deal_made=0"
    assert no_deal["deal_equity"].isna().all(), "deal_equity should be null when deal_made=0"


def test_dq_checks_run():
    summary = run_dq_checks()
    assert "total_pitches" in summary
    assert "issues" in summary
    assert summary["total_pitches"] > 0


def test_bridge_has_valid_shark_ids():
    tables = transform()
    bridge = tables["bridge_pitch_shark"]
    shark_ids = set(tables["dim_shark"]["shark_id"])
    assert bridge["shark_id"].isin(shark_ids).all()


def test_bridge_has_valid_pitch_ids():
    tables = transform()
    bridge = tables["bridge_pitch_shark"]
    pitch_ids = set(tables["fact_pitch"]["pitch_id"])
    assert bridge["pitch_id"].isin(pitch_ids).all()
