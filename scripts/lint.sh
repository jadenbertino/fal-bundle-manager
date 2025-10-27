#!/usr/bin/env bash
set -euo pipefail

# lint
uvx ruff check --fix src

# format
uvx ruff format src

# check types
echo "checking types"
uv run mypy src