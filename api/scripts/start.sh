#!/bin/bash
set -e

# Start script for fal-bundles API
# Ensures dependencies are installed and starts the development server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/api/.venv"

# Run setup if venv doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running setup..."
    bash "$SCRIPT_DIR/setup.sh"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set default environment variables
export DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/.data}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

echo "Starting fal-bundles API server..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Data directory: $DATA_DIR"
echo ""

# Start the server
cd "$PROJECT_ROOT"
uvicorn api.app:app --reload --host "$HOST" --port "$PORT"
