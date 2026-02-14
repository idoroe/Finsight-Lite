# FinSight Lite

An end-to-end anomaly detection pipeline that ingests banking transactions, transforms them through a dimensional model using dbt, and flags suspicious activity with human-readable explanations.

## Quick Start

```bash
docker compose up --build
```

Then visit [http://localhost:3000](http://localhost:3000)

## Tech Stack

- **Data Warehouse:** DuckDB (local, file-based)
- **Transformations:** dbt-core + dbt-duckdb
- **ML:** scikit-learn (Isolation Forest), joblib
- **Backend:** FastAPI + Uvicorn
- **Frontend:** React + TypeScript + Recharts + React Router
- **Infrastructure:** Docker + Docker Compose

## Project Structure

```
.
├── data/
│   └── raw/               # Generated CSV data
├── dbt_project/           # dbt transformations (staging → intermediate → marts)
├── ml/                    # Data generation, training, scoring, explainability
├── api/                   # FastAPI backend
├── frontend/              # React + TypeScript dashboard
├── scripts/               # Dev and run scripts
├── docker-compose.yml
├── Dockerfile.api
└── Dockerfile.frontend
```

*Full documentation coming in later stages.*
