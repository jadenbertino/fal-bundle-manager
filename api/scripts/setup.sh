#!/bin/bash
set -e

# Setup script for fal-bundles API
# Creates virtual environment and installs dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/api/.venv"

echo "Setting up fal-bundles API..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install API dependencies
echo "Installing API dependencies..."
pip install -q --upgrade pip
pip install -q -r "$PROJECT_ROOT/api/requirements.txt"

# Install test dependencies
echo "Installing test dependencies..."
pip install -q -r "$PROJECT_ROOT/api/tests/requirements.txt"

# Create marker file to track last install time
touch "$VENV_DIR/.last_install"

echo "✓ Setup complete!"
echo ""
echo "To activate the virtual environment manually, run:"
echo "  source $VENV_DIR/bin/activate"
