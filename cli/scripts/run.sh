#!/bin/bash
# Run CLI with proper environment setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$CLI_DIR")"
INSTALL_MARKER="$CLI_DIR/.venv/.last_install"

# Check if venv exists, run setup if not
if [ ! -d "$CLI_DIR/.venv" ]; then
    echo "==> First run detected, setting up environment..."
    "$SCRIPT_DIR/setup.sh"
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
if [ -f "$CLI_DIR/requirements.txt" ] && [ "$CLI_DIR/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Check if test requirements.txt is newer than last install
if [ -f "$CLI_DIR/tests/requirements.txt" ] && [ "$CLI_DIR/tests/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Update dependencies if needed
if [ "$needs_update" = true ]; then
    echo "==> Dependencies have changed, updating..."
    source "$CLI_DIR/.venv/bin/activate"
    pip install -q -r "$CLI_DIR/requirements.txt"
    if [ -f "$CLI_DIR/tests/requirements.txt" ]; then
        pip install -q -r "$CLI_DIR/tests/requirements.txt"
    fi
    touch "$INSTALL_MARKER"
    echo "✓ Dependencies updated"
fi

# Activate virtual environment
source "$CLI_DIR/.venv/bin/activate"

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

# Run CLI with all passed arguments (stay in current directory)
python -m cli "$@"
