#!/bin/bash
# Setup script for CLI development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$CLI_DIR")"

cd "$CLI_DIR"

echo "==> Setting up CLI development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv .venv
else
    echo "==> Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "==> Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "==> Installing CLI dependencies..."
pip install -r requirements.txt --quiet

# Install test dependencies
echo "==> Installing test dependencies..."
pip install -r tests/requirements.txt --quiet

# Create marker file to track last install time
touch .venv/.last_install

echo ""
echo "✓ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  cd $CLI_DIR"
echo "  source .venv/bin/activate"
echo ""
echo "To run the CLI (from project root):"
echo "  export PYTHONPATH=$PROJECT_ROOT"
echo "  python -m cli --help"
echo ""
echo "To run tests:"
echo "  cd $CLI_DIR"
echo "  source .venv/bin/activate"
echo "  export PYTHONPATH=$PROJECT_ROOT"
echo "  pytest tests/ -v"
echo ""
