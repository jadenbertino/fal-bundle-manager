#!/bin/bash
# Test runner for fal-bundles API
# 
# Usage: ./test.sh [PYTEST_ARGS...]
# 
# This script runs the API test suite using pytest.
# Environment and dependencies are managed automatically via dependencies.sh.
# 
# Examples:
#   ./test.sh                    # Run all tests
#   ./test.sh -k test_create     # Run specific test
#   ./test.sh --cov              # Run with coverage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/dependencies.sh"

# Run pytest with any additional arguments passed to the script
echo "Running tests..."
cd "$PROJECT_ROOT"
pytest api/tests/ -v "$@"
