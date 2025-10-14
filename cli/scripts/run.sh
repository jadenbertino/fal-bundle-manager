#!/bin/bash
# Run fal-bundles CLI with proper environment setup
# 
# Usage: ./run.sh [CLI_ARGS...]
# 
# This script handles:
# - Environment setup via dependencies.sh (venv, PYTHONPATH, etc.)
# - Running the CLI with all passed arguments
# - Preserving the program name for help text
#
# Used by the installed wrapper script but can also be run directly for development.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/dependencies.sh"

# Run CLI with all passed arguments (stay in current directory)
# Use the program name from environment variable or default to 'fal-bundles'
PROG_NAME="${FAL_BUNDLES_PROG_NAME:-fal-bundles}"
python -c "
import sys
sys.argv[0] = '$PROG_NAME'
import cli.__main__
cli.__main__.cli()
" "$@"
