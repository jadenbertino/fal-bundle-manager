#!/bin/bash
# Run CLI tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$CLI_DIR")"

cd "$CLI_DIR"

# Check if venv exists, run setup if not
if [ ! -d ".venv" ]; then
    echo "==> First run detected, setting up environment..."
    "$SCRIPT_DIR/setup.sh"
    if [ $? -ne 0 ]; then
        echo "Error: Setup failed"
        exit 1
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

echo "==> Running CLI tests..."
pytest tests/ -v "$@"
