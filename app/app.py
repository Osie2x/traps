"""SharkGraph — Deal Intelligence Web App.

Launch: streamlit run app/app.py
"""

import os
import sys

import streamlit as st

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="SharkGraph", page_icon="🦈", layout="wide")

st.title("SharkGraph — Deal Intelligence")
st.markdown(
    "Predict outcomes, map investor bias, and explore the Shark Tank network graph."
)

st.sidebar.success("Select a page above.")

st.markdown("""
### Pages

- **Pitch Predictor** — Enter pitch details and get a deal probability + likely sharks.
- **Network Explorer** — Interactive graph of Sharks, Industries, and Companies.
- **Shark Profiles** — Bias cards showing each shark's preferences and trends.
- **Data Quality** — Latest DQ check results and issue counts.
""")
