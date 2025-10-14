#!/bin/bash
# Start fal-bundles API development server
# 
# Usage: ./start.sh
# 
# This script starts the FastAPI development server with:
# - Auto-reload enabled for development
# - Environment setup via dependencies.sh
# - Configurable host/port via HOST/PORT environment variables
# - Automatic dependency installation/updates
# 
# Environment variables:
#   HOST       Server host (default: 0.0.0.0)
#   PORT       Server port (default: 8000)
#   DATA_DIR   Data storage directory (default: api/.data)

set -e
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
