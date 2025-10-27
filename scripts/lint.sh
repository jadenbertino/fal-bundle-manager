#!/usr/bin/env bash
set -euo pipefail

FOLDERS="api cli shared"

# lint
uvx ruff check --fix $FOLDERS

# format
uvx ruff format $FOLDERS

# check types
echo "checking types"
uv run mypy --exclude 'tests' $FOLDERS