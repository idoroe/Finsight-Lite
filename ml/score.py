"""Score all transactions with the trained Isolation Forest model."""

import os
from pathlib import Path

import duckdb
import joblib
import numpy as np

from ml.train import FEATURE_COLS, MODEL_PATH, SCALER_PATH

DB_PATH = os.environ.get("DUCKDB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"))


def score():
    """Score transactions and write anomaly_score + is_anomaly into DuckDB."""
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

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

    for col in ["is_weekend", "is_international", "is_new_merchant"]:
        df[col] = df[col].astype(int)
    df["time_since_last_txn"] = df["time_since_last_txn"].fillna(-1)

    X = df[FEATURE_COLS].values.astype(np.float64)
    X_scaled = scaler.transform(X)

    # decision_function: lower = more anomalous
    raw_scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)  # -1 = anomaly, 1 = normal

    # Normalize score to 0..1 where 1 = most anomalous
    score_min = raw_scores.min()
    score_max = raw_scores.max()
    anomaly_scores = 1 - (raw_scores - score_min) / (score_max - score_min)
    anomaly_scores = np.round(anomaly_scores, 6)

    is_anomaly = (predictions == -1).astype(int)

    # Write scored table to DuckDB
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS scored_transactions")
    con.execute("""
        CREATE TABLE scored_transactions AS
        SELECT * FROM fct_transactions
    """)
    con.execute("ALTER TABLE scored_transactions ADD COLUMN anomaly_score DOUBLE")
    con.execute("ALTER TABLE scored_transactions ADD COLUMN is_anomaly INTEGER")
    con.execute("ALTER TABLE scored_transactions ADD COLUMN anomaly_reasons VARCHAR")

    # Update scores
    transaction_ids = df["transaction_id"].tolist()
    for i, tid in enumerate(transaction_ids):
        con.execute(
            "UPDATE scored_transactions SET anomaly_score = ?, is_anomaly = ? WHERE transaction_id = ?",
            [float(anomaly_scores[i]), int(is_anomaly[i]), tid],
        )

    con.close()

    n_anomalies = int(is_anomaly.sum())
    print(f"Scored {len(transaction_ids)} transactions")
    print(f"  Anomalies flagged: {n_anomalies} ({n_anomalies / len(transaction_ids) * 100:.1f}%)")


if __name__ == "__main__":
    score()
