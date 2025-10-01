#!/bin/bash
set -e

# Test script for fal-bundles
# Runs pytest with the project's virtual environment

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

echo "Running tests..."
cd "$PROJECT_ROOT"

# Run pytest with any additional arguments passed to the script
pytest api/tests/ -v "$@"
