"""Application configuration read from the environment."""

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://stockroom:stockroom@localhost:5432/stockroom",
)
APP_NAME = os.getenv("APP_NAME", "StockRoom")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
