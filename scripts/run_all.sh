#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."

cd "$ROOT_DIR"

echo "=== Running full pipeline ==="
python -m ml.run_pipeline

echo ""
echo "=== Starting API and Frontend ==="
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""

# Start API in background
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start frontend
cd frontend
npm run dev &
FE_PID=$!

# Trap to kill both on exit
trap "kill $API_PID $FE_PID 2>/dev/null" EXIT

wait
