#!/usr/bin/env bash
set -euo pipefail

# Start script for fal-bundles API
# Ensures dependencies are installed and starts the development server using uv

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Set default environment variables
export DATA_DIR="${DATA_DIR:-api/.data}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

echo "Starting fal-bundles API server..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Data directory: $DATA_DIR"
echo ""

# Start the server using uv run with PYTHONPATH set for shared module access
uv run uvicorn api.app:app --reload --host "$HOST" --port "$PORT"
