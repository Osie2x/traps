"""Train a model to predict deal_made (0/1) from pitch features."""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MODELS_DIR
from etl.transform import transform


FEATURE_COLS = ["asked_amount", "asked_equity", "valuation_asked", "season", "multi_shark"]
CAT_COLS = ["industry_name"]
TARGET = "deal_made"


def _build_feature_df(tables: dict) -> pd.DataFrame:
    """Merge tables into a flat feature DataFrame."""
    fp = tables["fact_pitch"]
    dim_company = tables["dim_company"]
    dim_industry = tables["dim_industry"]
    dim_episode = tables["dim_episode"]

    df = fp.merge(dim_company[["company_id", "industry_id"]], on="company_id", how="left")
    df = df.merge(dim_industry[["industry_id", "industry_name"]], on="industry_id", how="left")
    df = df.merge(dim_episode[["episode_id", "season"]], on="episode_id", how="left")
    return df


def train(tables: dict | None = None) -> Pipeline:
    """Train deal prediction model and save artifacts."""
    if tables is None:
        tables = transform()

    df = _build_feature_df(tables)
    all_cols = FEATURE_COLS + CAT_COLS
    df = df.dropna(subset=["asked_amount", "asked_equity", TARGET])

    X = df[all_cols].copy()
    y = df[TARGET].astype(int)

    # Fill NaN in valuation_asked
    X["valuation_asked"] = X["valuation_asked"].fillna(X["valuation_asked"].median())

    # Preprocessing
    num_features = FEATURE_COLS
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
        ]
    )

    # Baseline: Logistic Regression
    lr_pipe = Pipeline([("prep", preprocessor), ("clf", LogisticRegression(max_iter=1000))])
    lr_scores = cross_val_score(lr_pipe, X, y, cv=min(5, len(df)), scoring="roc_auc")
    print(f"Logistic Regression AUC: {lr_scores.mean():.3f} (+/- {lr_scores.std():.3f})")

    # Strong: Gradient Boosting
    gb_pipe = Pipeline([
        ("prep", preprocessor),
        ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)),
    ])
    gb_scores = cross_val_score(gb_pipe, X, y, cv=min(5, len(df)), scoring="roc_auc")
    print(f"Gradient Boosting AUC:   {gb_scores.mean():.3f} (+/- {gb_scores.std():.3f})")

    # Pick best
    if gb_scores.mean() >= lr_scores.mean():
        best_pipe = gb_pipe
        best_name = "GradientBoosting"
    else:
        best_pipe = lr_pipe
        best_name = "LogisticRegression"

    best_pipe.fit(X, y)
    print(f"Selected model: {best_name}")

    # Save model
    model_path = os.path.join(MODELS_DIR, "deal_model.pkl")
    joblib.dump(best_pipe, model_path)
    print(f"Saved to {model_path}")

    # Save feature schema
    schema = {
        "numeric_features": FEATURE_COLS,
        "categorical_features": CAT_COLS,
        "target": TARGET,
        "model_type": best_name,
        "cv_auc_mean": round(max(gb_scores.mean(), lr_scores.mean()), 4),
        "industries": sorted(df["industry_name"].dropna().unique().tolist()),
    }
    schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema saved to {schema_path}")

    return best_pipe


if __name__ == "__main__":
    train()
