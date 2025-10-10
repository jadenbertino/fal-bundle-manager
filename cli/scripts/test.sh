#!/bin/bash
set -e

# Test script for fal-bundles CLI
# Runs pytest with the project's virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/dependencies.sh"

# Run pytest with any additional arguments passed to the script
echo "==> Running CLI tests..."
cd "$CLI_DIR"
pytest tests/ -v "$@"
