#!/bin/bash
# Uninstall fal-bundles CLI wrapper

set -e

# Default installation directory and wrapper name
INSTALL_DIR="${HOME}/.local/bin"
WRAPPER_NAME="fal-bundles"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            WRAPPER_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--name <wrapper_name>]"
            echo ""
            echo "Options:"
            echo "  --name <name>        Wrapper script name to remove (default: fal-bundles)"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

WRAPPER_PATH="$INSTALL_DIR/$WRAPPER_NAME"

echo "==> Uninstalling fal-bundles CLI wrapper..."
echo "   Install directory: $INSTALL_DIR"
echo "   Wrapper name: $WRAPPER_NAME"

if [ -f "$WRAPPER_PATH" ]; then
    rm "$WRAPPER_PATH"
    echo "✓ Removed $WRAPPER_PATH"
else
    echo "⚠️  Wrapper not found at $WRAPPER_PATH"
fi

echo ""
echo "✓ fal-bundles CLI wrapper uninstalled successfully!"
echo ""
echo "Note: The CLI virtual environment and project files are preserved."
echo "To completely remove the project, delete the entire fal-bundles directory."
