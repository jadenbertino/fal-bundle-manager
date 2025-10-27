#!/bin/bash
# Run CLI tests using uv

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Sync workspace dependencies (includes dev dependencies with pytest)
echo "==> Syncing workspace dependencies with uv..."
cd "$PROJECT_ROOT"
uv sync

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

echo "==> Running CLI tests..."
uv run pytest cli/tests/ -v "$@"
