#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/../dbt_project"

echo "=== Running dbt build ==="
cd "$PROJECT_DIR"
dbt run --profiles-dir . --project-dir .
echo ""
echo "=== Running dbt tests ==="
dbt test --profiles-dir . --project-dir .
echo ""
echo "=== dbt pipeline complete ==="
