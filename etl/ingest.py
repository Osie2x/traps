"""Step 1: Ingest raw CSV and standardize column names."""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DATA_DIR


def ingest(csv_path: str | None = None) -> pd.DataFrame:
    """Read raw CSV and return a DataFrame with snake_case columns."""
    if csv_path is None:
        csv_path = os.path.join(DATA_DIR, "sample_pitches.csv")

    df = pd.read_csv(csv_path)

    # Standardize column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


if __name__ == "__main__":
    df = ingest()
    print(f"Ingested {len(df)} rows, {len(df.columns)} columns")
    print(df.dtypes)
