#!/bin/bash
# Run CLI with proper environment setup using uv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Sync workspace dependencies
cd "$PROJECT_ROOT"
uv sync --quiet

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

# Run CLI with all passed arguments (stay in current directory)
# Use the program name from environment variable or default to 'fal-bundles'
PROG_NAME="${FAL_BUNDLES_PROG_NAME:-fal-bundles}"
uv run python -c "
import sys
sys.argv[0] = '$PROG_NAME'
import cli.__main__
cli.__main__.cli()
" "$@"
