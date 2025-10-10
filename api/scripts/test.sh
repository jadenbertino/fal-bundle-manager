#!/bin/bash
set -e

# Test script for fal-bundles
# Runs pytest with the project's virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

# Run pytest with any additional arguments passed to the script
echo "Running tests..."
cd "$PROJECT_ROOT"
pytest api/tests/ -v "$@"
