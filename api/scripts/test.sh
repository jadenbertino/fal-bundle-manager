#!/bin/bash
set -e

# Test script for fal-bundles
# Runs pytest with the project's virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/api/.venv"
INSTALL_MARKER="$VENV_DIR/.last_install"

# Run setup if venv doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "==> First run detected, setting up environment..."
    bash "$SCRIPT_DIR/setup.sh"
    if [ $? -ne 0 ]; then
        echo "Error: Setup failed"
        exit 1
    fi
fi

# Check if dependencies need updating
needs_update=false

# Check if marker file exists
if [ ! -f "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Check if requirements.txt is newer than last install
if [ -f "$PROJECT_ROOT/api/requirements.txt" ] && [ "$PROJECT_ROOT/api/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Check if test requirements.txt is newer than last install
if [ -f "$PROJECT_ROOT/api/tests/requirements.txt" ] && [ "$PROJECT_ROOT/api/tests/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Update dependencies if needed
if [ "$needs_update" = true ]; then
    echo "==> Dependencies have changed, updating..."
    source "$VENV_DIR/bin/activate"
    pip install -q -r "$PROJECT_ROOT/api/requirements.txt"
    if [ -f "$PROJECT_ROOT/api/tests/requirements.txt" ]; then
        pip install -q -r "$PROJECT_ROOT/api/tests/requirements.txt"
    fi
    touch "$INSTALL_MARKER"
    echo "✓ Dependencies updated"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Running tests..."
cd "$PROJECT_ROOT"

# Run pytest with any additional arguments passed to the script
pytest api/tests/ -v "$@"
