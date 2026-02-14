"""DuckDB connection helper for the API."""

import os
from pathlib import Path

import duckdb

DB_PATH = os.environ.get(
    "DUCKDB_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"),
)


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Get a DuckDB connection."""
    return duckdb.connect(DB_PATH, read_only=read_only)
