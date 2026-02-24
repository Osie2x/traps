"""Train a multi-label classifier: which shark(s) are likely to invest."""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MODELS_DIR
from etl.transform import transform

FEATURE_COLS = ["asked_amount", "asked_equity", "valuation_asked", "season"]
CAT_COLS = ["industry_name"]


def train(tables: dict | None = None):
    """Train shark recommendation model (one-vs-rest)."""
    if tables is None:
        tables = transform()

    fp = tables["fact_pitch"]
    bridge = tables["bridge_pitch_shark"]
    dim_shark = tables["dim_shark"]
    dim_company = tables["dim_company"]
    dim_industry = tables["dim_industry"]
    dim_episode = tables["dim_episode"]

    # Build feature df
    df = fp.merge(dim_company[["company_id", "industry_id"]], on="company_id", how="left")
    df = df.merge(dim_industry[["industry_id", "industry_name"]], on="industry_id", how="left")
    df = df.merge(dim_episode[["episode_id", "season"]], on="episode_id", how="left")

    # Only pitches that got a deal
    deals = df[df["deal_made"] == 1].copy()
    if len(deals) == 0:
        print("No deals found; cannot train shark model.")
        return None

    # Build labels: which sharks invested in each deal
    shark_map = dict(zip(dim_shark["shark_id"], dim_shark["name"]))
    invested = bridge[bridge["invested"] == 1]
    pitch_sharks = invested.groupby("pitch_id")["shark_id"].apply(
        lambda ids: [shark_map[i] for i in ids if i in shark_map]
    )

    deals = deals.merge(pitch_sharks.rename("investing_sharks"), left_on="pitch_id", right_index=True, how="inner")
    deals = deals.dropna(subset=["asked_amount", "asked_equity"])

    if len(deals) < 3:
        print("Too few deal samples for shark model.")
        return None

    # Top sharks (those with at least 2 investments)
    all_investing = [s for sharks in deals["investing_sharks"] for s in sharks]
    shark_counts = pd.Series(all_investing).value_counts()
    top_sharks = shark_counts[shark_counts >= 2].index.tolist()

    if not top_sharks:
        top_sharks = shark_counts.head(5).index.tolist()

    # Binarize labels
    mlb = MultiLabelBinarizer(classes=top_sharks)
    Y = mlb.fit_transform(deals["investing_sharks"])

    X = deals[FEATURE_COLS + CAT_COLS].copy()
    X["valuation_asked"] = X["valuation_asked"].fillna(X["valuation_asked"].median())

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), FEATURE_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
        ]
    )

    pipe = Pipeline([
        ("prep", preprocessor),
        ("clf", OneVsRestClassifier(LogisticRegression(max_iter=1000))),
    ])

    pipe.fit(X, Y)
    print(f"Shark model trained on {len(deals)} deals for {len(top_sharks)} sharks: {top_sharks}")

    # Save
    model_path = os.path.join(MODELS_DIR, "shark_model.pkl")
    joblib.dump({"pipeline": pipe, "mlb": mlb, "top_sharks": top_sharks}, model_path)
    print(f"Saved to {model_path}")

    return pipe


if __name__ == "__main__":
    train()
