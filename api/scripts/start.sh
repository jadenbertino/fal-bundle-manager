#!/bin/bash
set -e

# Start script for fal-bundles API
# Ensures dependencies are installed and starts the development server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/dependencies.sh"

echo "Starting fal-bundles API server..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Data directory: $DATA_DIR"
echo ""

# Start the server
cd "$PROJECT_ROOT"
uvicorn api.app:app --reload --host "$HOST" --port "$PORT"
