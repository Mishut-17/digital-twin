#!/bin/bash
# Start the Digital Twin Dashboard server
set -e

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "Starting Digital Twin Dashboard on http://${HOST}:${PORT}"
cd "$(dirname "$0")"

python -m uvicorn webapp.app:app --host "$HOST" --port "$PORT" --reload
