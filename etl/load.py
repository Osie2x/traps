"""Step 3: Load transformed DataFrames into Postgres."""

import os
import sys

from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_URL
from etl.transform import transform


TABLE_ORDER = [
    "dim_shark",
    "dim_episode",
    "dim_industry",
    "dim_company",
    "fact_pitch",
    "bridge_pitch_shark",
]


def load(tables: dict | None = None, db_url: str | None = None):
    """Load all tables into Postgres (truncate + insert)."""
    if tables is None:
        tables = transform()
    if db_url is None:
        db_url = DATABASE_URL

    engine = create_engine(db_url)

    with engine.begin() as conn:
        # Truncate in reverse FK order
        for tbl_name in reversed(TABLE_ORDER):
            conn.execute(text(f"TRUNCATE TABLE {tbl_name} CASCADE"))

        # Insert
        for tbl_name in TABLE_ORDER:
            df = tables[tbl_name]
            df.to_sql(tbl_name, conn, if_exists="append", index=False)
            print(f"  Loaded {len(df)} rows into {tbl_name}")

    # Build mart tables
    print("Building mart tables...")
    with engine.begin() as conn:
        for mart_file in ["mart_pitch_features.sql", "mart_shark_metrics.sql", "mart_network_edges.sql"]:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", "marts", mart_file)
            if os.path.exists(path):
                with open(path) as f:
                    sql = f.read()
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        conn.execute(text(stmt))
                print(f"  Executed {mart_file}")

    print("Load complete.")


if __name__ == "__main__":
    load()
