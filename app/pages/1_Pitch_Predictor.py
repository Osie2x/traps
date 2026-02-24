"""Page 1: Pitch Predictor — deal probability + shark recommendations."""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import MODELS_DIR

st.header("Pitch Predictor")

# Load model artifacts
@st.cache_resource
def load_models():
    deal_model = joblib.load(os.path.join(MODELS_DIR, "deal_model.pkl"))
    shark_data = joblib.load(os.path.join(MODELS_DIR, "shark_model.pkl"))
    with open(os.path.join(MODELS_DIR, "feature_schema.json")) as f:
        schema = json.load(f)
    return deal_model, shark_data, schema


try:
    deal_model, shark_data, schema = load_models()
except FileNotFoundError:
    st.error("Models not found. Run `make train` first.")
    st.stop()

# --- Input form ---
col1, col2 = st.columns(2)

with col1:
    industry = st.selectbox("Industry", schema["industries"])
    asked_amount = st.number_input("Asked Amount ($)", min_value=1000, value=200000, step=10000)
    asked_equity = st.slider("Asked Equity (%)", min_value=1, max_value=100, value=15) / 100.0

with col2:
    season = st.number_input("Season", min_value=1, max_value=20, value=5)
    multi_shark = st.selectbox("Open to multiple sharks?", [0, 1], format_func=lambda x: "Yes" if x else "No")

valuation = asked_amount / asked_equity if asked_equity > 0 else 0

st.markdown(f"**Implied valuation:** ${valuation:,.0f}")

if st.button("Predict", type="primary"):
    # Build input DataFrame
    input_df = pd.DataFrame([{
        "asked_amount": asked_amount,
        "asked_equity": asked_equity,
        "valuation_asked": valuation,
        "season": season,
        "multi_shark": multi_shark,
        "industry_name": industry,
    }])

    # Deal probability
    proba = deal_model.predict_proba(input_df)[0][1]

    st.subheader("Results")

    # Gauge-like display
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Deal Probability", f"{proba:.0%}")
        if proba >= 0.6:
            st.success("Strong chance of a deal!")
        elif proba >= 0.4:
            st.warning("Moderate chance — consider adjusting terms.")
        else:
            st.error("Low probability — review your ask.")

    # Shark recommendations
    with col_b:
        shark_pipe = shark_data["pipeline"]
        mlb = shark_data["mlb"]
        top_sharks = shark_data["top_sharks"]

        shark_input = pd.DataFrame([{
            "asked_amount": asked_amount,
            "asked_equity": asked_equity,
            "valuation_asked": valuation,
            "season": season,
            "industry_name": industry,
        }])

        try:
            shark_proba = shark_pipe.predict_proba(shark_input)
            # OneVsRest returns list of arrays
            if isinstance(shark_proba, list):
                shark_scores = [p[0][1] if p.shape[1] > 1 else p[0][0] for p in shark_proba]
            else:
                shark_scores = shark_proba[0]

            shark_ranking = sorted(zip(top_sharks, shark_scores), key=lambda x: -x[1])
            st.markdown("**Likely Sharks (ranked):**")
            for shark_name, score in shark_ranking:
                bar = "█" * int(score * 20)
                st.write(f"- {shark_name}: {score:.0%} {bar}")
        except Exception as e:
            st.info(f"Shark model unavailable: {e}")

    # Explainability
    st.subheader("Why this prediction?")
    feature_importance = []
    try:
        schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
        # Simple rule-based explanation
        if valuation > 1_000_000:
            feature_importance.append(("High valuation", "down", "Valuations >$1M face more scrutiny"))
        if asked_equity < 0.10:
            feature_importance.append(("Low equity offer", "down", "Sharks prefer higher equity stakes"))
        if asked_equity > 0.25:
            feature_importance.append(("Generous equity", "up", "Higher equity makes the deal attractive"))
        if asked_amount < 150_000:
            feature_importance.append(("Modest ask", "up", "Lower asks are easier to commit to"))

        if feature_importance:
            for name, direction, explanation in feature_importance[:3]:
                icon = "📈" if direction == "up" else "📉"
                st.write(f"{icon} **{name}**: {explanation}")
        else:
            st.info("No strong signal drivers identified for this combination.")
    except Exception:
        pass

    # Expected equity range
    st.subheader("Expected Deal Terms")
    st.write(f"- **Suggested equity range:** {max(asked_equity, 0.10):.0%} – {min(asked_equity * 2, 0.50):.0%}")
    st.write(f"- **Typical deal amount:** ${asked_amount * 0.8:,.0f} – ${asked_amount * 1.2:,.0f}")
