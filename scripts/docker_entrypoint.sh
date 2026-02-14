#!/usr/bin/env bash
set -euo pipefail

echo "=== FinSight Lite API Startup ==="

# Build the pipeline if the warehouse doesn't exist
if [ ! -f "$DUCKDB_PATH" ]; then
    echo "No warehouse found. Running full pipeline..."

    # Generate data if CSV is missing
    if [ ! -f "$CSV_PATH" ]; then
        echo "Generating synthetic data..."
        python -m ml.generate_data --rows 50000 --seed 42
    fi

    # Run dbt
    echo "Running dbt models..."
    cd /app/dbt_project
    dbt run --profiles-dir . --project-dir .
    echo "Running dbt tests..."
    dbt test --profiles-dir . --project-dir .
    cd /app

    # Train model
    echo "Training Isolation Forest..."
    python -m ml.train

    # Score transactions
    echo "Scoring transactions..."
    python -m ml.score

    # Generate explanations
    echo "Generating anomaly explanations..."
    python -m ml.explain

    echo "Pipeline complete!"
else
    echo "Warehouse found at $DUCKDB_PATH. Skipping pipeline."
fi

echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
