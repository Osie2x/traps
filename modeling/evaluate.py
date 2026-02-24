"""Evaluate trained models and produce a model card."""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_predict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MODELS_DIR, REPORTS_DIR
from etl.transform import transform
from modeling.train_deal_model import FEATURE_COLS, CAT_COLS, TARGET, _build_feature_df


def evaluate():
    """Evaluate deal model and write model card."""
    tables = transform()
    df = _build_feature_df(tables)
    df = df.dropna(subset=["asked_amount", "asked_equity", TARGET])

    X = df[FEATURE_COLS + CAT_COLS].copy()
    y = df[TARGET].astype(int)
    X["valuation_asked"] = X["valuation_asked"].fillna(X["valuation_asked"].median())

    model = joblib.load(os.path.join(MODELS_DIR, "deal_model.pkl"))

    # Cross-validated predictions
    cv_folds = min(5, len(df))
    y_pred_proba = cross_val_predict(model, X, y, cv=cv_folds, method="predict_proba")[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc = roc_auc_score(y, y_pred_proba)
    report = classification_report(y, y_pred, output_dict=True)

    print(f"Deal Model AUC: {auc:.3f}")
    print(classification_report(y, y_pred))

    # Feature importance (permutation)
    model.fit(X, y)
    X_transformed = model.named_steps["prep"].transform(X)
    perm_imp = permutation_importance(
        model.named_steps["clf"], X_transformed, y, n_repeats=10, random_state=42
    )

    # Map feature names
    cat_encoder = model.named_steps["prep"].transformers_[1][1]
    cat_names = list(cat_encoder.get_feature_names_out(CAT_COLS))
    all_feature_names = FEATURE_COLS + cat_names
    importance_df = pd.DataFrame({
        "feature": all_feature_names[:len(perm_imp.importances_mean)],
        "importance_mean": perm_imp.importances_mean,
        "importance_std": perm_imp.importances_std,
    }).sort_values("importance_mean", ascending=False)

    print("\nFeature Importance:")
    print(importance_df.to_string(index=False))

    # Write model card
    _write_model_card(auc, report, importance_df)

    return auc


def _write_model_card(auc: float, report: dict, importance_df: pd.DataFrame):
    """Write an HTML model card."""
    html_parts = [
        "<html><head><title>SharkGraph Model Card</title>",
        "<style>body{font-family:sans-serif;margin:2em;max-width:800px}",
        "table{border-collapse:collapse;margin:1em 0}",
        "th,td{border:1px solid #ccc;padding:6px 12px;text-align:left}",
        "th{background:#f0f0f0}.warn{color:#c00}</style></head><body>",
        "<h1>SharkGraph Model Card</h1>",
        "<h2>Deal Prediction Model</h2>",
        f"<p><strong>AUC-ROC:</strong> {auc:.3f}</p>",
        f"<p><strong>Precision (deal=1):</strong> {report.get('1', {}).get('precision', 0):.3f}</p>",
        f"<p><strong>Recall (deal=1):</strong> {report.get('1', {}).get('recall', 0):.3f}</p>",
        f"<p><strong>F1 (deal=1):</strong> {report.get('1', {}).get('f1-score', 0):.3f}</p>",
        "<h2>Feature Importance (Permutation)</h2>",
        "<table><tr><th>Feature</th><th>Importance</th><th>Std</th></tr>",
    ]
    for _, row in importance_df.head(15).iterrows():
        html_parts.append(
            f"<tr><td>{row['feature']}</td><td>{row['importance_mean']:.4f}</td>"
            f"<td>{row['importance_std']:.4f}</td></tr>"
        )
    html_parts.append("</table>")

    html_parts.extend([
        "<h2>Limitations & Bias Notes</h2>",
        "<ul class='warn'>",
        "<li>Small sample size — model performance is approximate.</li>",
        "<li>The dataset reflects the show's editing and selection bias.</li>",
        "<li>Industry categories are coarse; finer taxonomy may improve results.</li>",
        "<li>Deal terms on the show may differ from final closed terms.</li>",
        "<li>Seasonal trends may be confounded with production changes.</li>",
        "</ul>",
        "</body></html>",
    ])

    path = os.path.join(REPORTS_DIR, "model_card.html")
    with open(path, "w") as f:
        f.write("\n".join(html_parts))
    print(f"Model card written to {path}")


if __name__ == "__main__":
    evaluate()
