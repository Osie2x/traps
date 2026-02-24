"""Centralized configuration for SharkGraph."""

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://shark:sharkpass@localhost:5432/sharkgraph",
)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
