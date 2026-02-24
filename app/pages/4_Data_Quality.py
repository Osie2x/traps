"""Page 4: Data Quality — DQ check results and issue counts."""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import REPORTS_DIR

st.header("Data Quality Dashboard")

# Run DQ checks
from etl.dq_checks import run_dq_checks


@st.cache_data
def get_dq_summary():
    return run_dq_checks()


summary = get_dq_summary()

# Overview
col1, col2, col3 = st.columns(3)
col1.metric("Total Pitches", summary["total_pitches"])
col2.metric("Bridge Rows", summary["total_bridge_rows"])
col3.metric("Issues Found", summary["issues_found"])

if summary["issues_found"] == 0:
    st.success("All data quality checks passed.")
else:
    st.warning(f"{summary['issues_found']} issue(s) detected.")
    issues_df = pd.DataFrame(summary["issues"])
    st.dataframe(issues_df, use_container_width=True)

# Show DQ report link if exists
report_path = os.path.join(REPORTS_DIR, "data_quality_report.html")
if os.path.exists(report_path):
    with open(report_path) as f:
        html = f.read()
    st.subheader("Full Report")
    st.components.v1.html(html, height=400, scrolling=True)

# Issues CSV
issues_path = os.path.join(REPORTS_DIR, "dq_issues.csv")
if os.path.exists(issues_path):
    st.subheader("Download Issues")
    with open(issues_path) as f:
        st.download_button("Download dq_issues.csv", f.read(), file_name="dq_issues.csv")
