"""Step 2: Clean, parse, and reshape raw data into dim/fact DataFrames."""

import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from etl.ingest import ingest


def _parse_money(val):
    """Convert strings like '$100k', '$1.5M', '100000' to float."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace(",", "").replace("$", "")
    m = re.match(r"^([\d.]+)\s*([kKmM]?)$", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return np.nan
    num = float(m.group(1))
    suffix = m.group(2).lower()
    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000
    return num


def _parse_equity(val):
    """Convert '20%' or 0.20 to float in [0,1]."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace("%", "")
    try:
        num = float(s)
    except ValueError:
        return np.nan
    if num > 1:
        num /= 100.0
    return num


def transform(df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Return dict of dimension and fact DataFrames."""
    if df is None:
        df = ingest()

    # --- Parse monetary / equity fields ---
    money_cols = [c for c in df.columns if "amount" in c]
    for c in money_cols:
        df[c] = df[c].apply(_parse_money)

    equity_cols = [c for c in df.columns if "equity" in c]
    for c in equity_cols:
        df[c] = df[c].apply(_parse_equity)

    # --- dim_episode ---
    dim_episode = (
        df[["season", "episode"]]
        .drop_duplicates()
        .rename(columns={"episode": "episode_number"})
        .reset_index(drop=True)
    )
    dim_episode["episode_id"] = dim_episode.index + 1

    # --- dim_industry ---
    dim_industry = (
        df[["industry"]]
        .drop_duplicates()
        .rename(columns={"industry": "industry_name"})
        .reset_index(drop=True)
    )
    dim_industry["industry_id"] = dim_industry.index + 1
    dim_industry["parent_industry"] = dim_industry["industry_name"].str.split("/").str[0]

    # --- dim_shark ---
    shark_cols = [c for c in df.columns if re.match(r"shark\d+$", c)]
    all_sharks = set()
    for c in shark_cols:
        all_sharks.update(df[c].dropna().unique())
    dim_shark = pd.DataFrame({"name": sorted(all_sharks)})
    dim_shark["shark_id"] = dim_shark.index + 1

    # --- dim_company ---
    df_merged = df.merge(
        dim_industry.rename(columns={"industry_name": "industry"}),
        on="industry",
        how="left",
    )
    dim_company = (
        df_merged[["company_name", "industry_id", "location"]]
        .drop_duplicates(subset=["company_name"])
        .reset_index(drop=True)
    )
    dim_company["company_id"] = dim_company.index + 1

    # --- fact_pitch ---
    df_merged = df_merged.merge(
        dim_episode.rename(columns={"episode_number": "episode"}),
        on=["season", "episode"],
        how="left",
    )
    df_merged = df_merged.merge(dim_company[["company_name", "company_id"]], on="company_name", how="left")

    fact_pitch = df_merged[
        [
            "episode_id",
            "company_id",
            "asked_amount",
            "asked_equity",
            "deal_made",
            "deal_amount",
            "deal_equity",
            "multi_shark",
            "description",
            "location",
        ]
    ].copy()
    fact_pitch = fact_pitch.rename(columns={"description": "description_text"})
    fact_pitch["pitch_id"] = fact_pitch.index + 1

    # Compute valuation_asked
    fact_pitch["valuation_asked"] = np.where(
        fact_pitch["asked_equity"] > 0,
        fact_pitch["asked_amount"] / fact_pitch["asked_equity"],
        np.nan,
    )

    # Enforce consistency: no deal → null deal terms
    no_deal = fact_pitch["deal_made"] == 0
    fact_pitch.loc[no_deal, "deal_amount"] = np.nan
    fact_pitch.loc[no_deal, "deal_equity"] = np.nan

    # --- bridge_pitch_shark ---
    bridge_rows = []
    shark_name_to_id = dict(zip(dim_shark["name"], dim_shark["shark_id"]))
    for idx, row in df_merged.iterrows():
        pitch_id = idx + 1
        for i in range(1, 6):
            scol = f"shark{i}"
            if scol not in row or pd.isna(row[scol]):
                continue
            shark_name = row[scol]
            if shark_name not in shark_name_to_id:
                continue
            invested_col = f"shark{i}_invested"
            offer_amount_col = f"shark{i}_offer_amount"
            offer_equity_col = f"shark{i}_offer_equity"
            bridge_rows.append(
                {
                    "pitch_id": pitch_id,
                    "shark_id": shark_name_to_id[shark_name],
                    "invested": int(row.get(invested_col, 0) or 0),
                    "offer_amount": row.get(offer_amount_col, np.nan),
                    "offer_equity": row.get(offer_equity_col, np.nan),
                }
            )
    bridge_pitch_shark = pd.DataFrame(bridge_rows)

    return {
        "dim_shark": dim_shark,
        "dim_episode": dim_episode,
        "dim_industry": dim_industry,
        "dim_company": dim_company,
        "fact_pitch": fact_pitch,
        "bridge_pitch_shark": bridge_pitch_shark,
    }


if __name__ == "__main__":
    tables = transform()
    for name, tbl in tables.items():
        print(f"{name}: {tbl.shape}")
