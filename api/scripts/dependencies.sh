#!/bin/bash
# Environment setup and dependency management for fal-bundles API
# 
# Usage: source dependencies.sh
# 
# This script handles:
# - Project path configuration and exports
# - Virtual environment creation and activation
# - Smart dependency updates (only when requirements.txt changes)
# - Application environment variables (DATA_DIR, HOST, PORT)
#
# Designed to be sourced by other scripts (start.sh, test.sh) for consistent
# environment setup across all API operations.

set -euo pipefail

# Project configuration
export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export VENV_DIR="$PROJECT_ROOT/api/.venv"
export INSTALL_MARKER="$VENV_DIR/.last_install"

# Application configuration
export DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/api/.data}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

# Activate venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# Check if dependencies need updating
needs_update=false
if [ ! -f "$INSTALL_MARKER" ]; then
    needs_update=true
fi
# requirements update
if [ -f "$PROJECT_ROOT/api/requirements.txt" ] && [ "$PROJECT_ROOT/api/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi
# test requirements update
if [ -f "$PROJECT_ROOT/api/tests/requirements.txt" ] && [ "$PROJECT_ROOT/api/tests/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Update dependencies if needed
if [ "$needs_update" = true ]; then
    echo "Updating dependencies..."
    pip install -q --upgrade pip
    pip install -q -r "$PROJECT_ROOT/api/requirements.txt"
    echo "Updating test dependencies..."
    pip install -q -r "$PROJECT_ROOT/api/tests/requirements.txt"
    touch "$INSTALL_MARKER"
    echo "✓ Dependencies updated"
fi