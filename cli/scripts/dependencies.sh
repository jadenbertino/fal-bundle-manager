#!/bin/bash
# Environment setup and dependency management for fal-bundles CLI
# 
# Usage: source dependencies.sh
# 
# This script handles:
# - Project path configuration and exports
# - Virtual environment creation and activation
# - Smart dependency updates (only when requirements.txt changes)
# - Application environment variables (API URL, timeout, PYTHONPATH)
#
# Designed to be sourced by other scripts (install.sh, run.sh) for consistent
# environment setup across all CLI operations.

set -euo pipefail

# Project configuration
export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CLI_DIR="$(dirname "$SCRIPT_DIR")"
export PROJECT_ROOT="$(dirname "$CLI_DIR")"
export VENV_DIR="$CLI_DIR/.venv"
export INSTALL_MARKER="$VENV_DIR/.last_install"

# Application configuration
export PYTHONPATH="$PROJECT_ROOT"
export FAL_BUNDLES_API_URL="${FAL_BUNDLES_API_URL:-http://localhost:8000}"
export FAL_BUNDLES_TIMEOUT="${FAL_BUNDLES_TIMEOUT:-300}"

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
if [ -f "$CLI_DIR/requirements.txt" ] && [ "$CLI_DIR/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi
# test requirements update
if [ -f "$CLI_DIR/tests/requirements.txt" ] && [ "$CLI_DIR/tests/requirements.txt" -nt "$INSTALL_MARKER" ]; then
    needs_update=true
fi

# Update dependencies if needed
if [ "$needs_update" = true ]; then
    echo "Updating dependencies..."
    pip install -q --upgrade pip
    pip install -q -r "$CLI_DIR/requirements.txt"
    echo "Updating test dependencies..."
    pip install -q -r "$CLI_DIR/tests/requirements.txt"
    touch "$INSTALL_MARKER"
    echo "✓ Dependencies updated"
fi