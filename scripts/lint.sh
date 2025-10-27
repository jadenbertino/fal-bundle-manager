#!/usr/bin/env bash
set -euo pipefail

# lint
uvx ruff check --fix api cli

# format
uvx ruff format api cli

# check types
echo "checking types"
uv run mypy api cli