"""Train Isolation Forest model on enriched transaction features."""

import os
from pathlib import Path

import duckdb
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
DB_PATH = os.environ.get("DUCKDB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"))

FEATURE_COLS = [
    "amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_international",
    "amount_zscore",
    "time_since_last_txn",
    "is_new_merchant",
    "txn_count_last_hour",
]


def load_features() -> tuple[np.ndarray, list[str]]:
    """Load ML features from the enriched DuckDB table."""
    con = duckdb.connect(DB_PATH, read_only=True)
    query = f"""
        select
            transaction_id,
            {', '.join(FEATURE_COLS)}
        from fct_transactions
        order by transaction_id
    """
    df = con.execute(query).fetchdf()
    con.close()

    transaction_ids = df["transaction_id"].tolist()

    # Convert booleans to int
    for col in ["is_weekend", "is_international", "is_new_merchant"]:
        df[col] = df[col].astype(int)

    # Fill nulls for time_since_last_txn (first transaction per customer)
    df["time_since_last_txn"] = df["time_since_last_txn"].fillna(-1)

    X = df[FEATURE_COLS].values.astype(np.float64)
    return X, transaction_ids


def train(contamination: float = 0.03, seed: int = 42):
    """Train Isolation Forest and save model + scaler."""
    X, _ = load_features()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=contamination,
        random_state=seed,
        n_estimators=200,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print(f"Model trained on {len(X)} samples")
    print(f"  Model saved to {MODEL_PATH}")
    print(f"  Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":
    train()
