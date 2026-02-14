"""Orchestrator: run the full ML pipeline end-to-end."""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_CSV = DATA_DIR / "raw" / "transactions.csv"
DBT_DIR = ROOT_DIR / "dbt_project"


def run_step(description: str, cmd: list[str], cwd: str | None = None):
    """Run a subprocess step with logging."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"FAILED: {description}")
        sys.exit(1)


def run_pipeline():
    """Execute the full pipeline: generate -> dbt -> train -> score -> explain."""
    # Step 1: Generate data if missing
    if not RAW_CSV.exists():
        run_step(
            "Generating synthetic data",
            [sys.executable, "-m", "ml.generate_data", "--rows", "50000", "--seed", "42"],
            cwd=str(ROOT_DIR),
        )
    else:
        print(f"\nCSV already exists at {RAW_CSV}, skipping generation.")

    # Step 2: Run dbt
    dbt_path = os.environ.get("DUCKDB_PATH", str(DATA_DIR / "warehouse.duckdb"))
    csv_path = os.environ.get("CSV_PATH", str(RAW_CSV))
    env = {**os.environ, "DUCKDB_PATH": dbt_path, "CSV_PATH": csv_path}

    run_step(
        "Running dbt models",
        ["dbt", "run", "--profiles-dir", ".", "--project-dir", "."],
        cwd=str(DBT_DIR),
    )

    run_step(
        "Running dbt tests",
        ["dbt", "test", "--profiles-dir", ".", "--project-dir", "."],
        cwd=str(DBT_DIR),
    )

    # Step 3: Train model
    run_step(
        "Training Isolation Forest",
        [sys.executable, "-m", "ml.train"],
        cwd=str(ROOT_DIR),
    )

    # Step 4: Score transactions
    run_step(
        "Scoring transactions",
        [sys.executable, "-m", "ml.score"],
        cwd=str(ROOT_DIR),
    )

    # Step 5: Generate explanations
    run_step(
        "Generating anomaly explanations",
        [sys.executable, "-m", "ml.explain"],
        cwd=str(ROOT_DIR),
    )

    print(f"\n{'='*60}")
    print("  Pipeline complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_pipeline()
