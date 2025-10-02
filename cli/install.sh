#!/bin/bash
# Install fal-bundles CLI wrapper
# 
# Usage: ./install.sh [--dir <directory>] [--name <wrapper_name>]
# 
# This script creates a wrapper script that references run.sh for the fal-bundles CLI.
# The wrapper is installed to ~/.local/bin by default, or to the specified directory.
# The wrapper handles environment setup and dependency management via run.sh.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$CLI_DIR"

# Default installation directory and wrapper name
INSTALL_DIR="${HOME}/.local/bin"
WRAPPER_NAME="fal-bundles"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --name)
            WRAPPER_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--dir <directory>] [--name <wrapper_name>]"
            echo ""
            echo "Options:"
            echo "  --dir <directory>    Installation directory (default: ~/.local/bin)"
            echo "  --name <name>        Wrapper script name (default: fal-bundles)"
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

echo "==> Installing fal-bundles CLI wrapper..."
echo "   Project root: $PROJECT_ROOT"
echo "   Install directory: $INSTALL_DIR"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Create the wrapper script that references run.sh
cat > "$INSTALL_DIR/$WRAPPER_NAME" << EOF
#!/bin/bash
# fal-bundles CLI wrapper

# Embedded project root path
PROJECT_ROOT="$PROJECT_ROOT"
CLI_DIR="\$PROJECT_ROOT/cli"

# Run the CLI using the run.sh script
exec "\$CLI_DIR/scripts/run.sh" "\$@"
EOF

# Make the wrapper executable
chmod +x "$INSTALL_DIR/$WRAPPER_NAME"

echo ""
echo "✓ fal-bundles CLI wrapper installed successfully!"
echo ""
echo "Installation details:"
echo "  Wrapper script: $INSTALL_DIR/$WRAPPER_NAME"
echo "  Project root: $PROJECT_ROOT"
echo ""

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  Warning: $INSTALL_DIR is not in your PATH"
    echo ""
    echo "To use 'fal-bundles' command, add this to your shell profile:"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    echo ""
    echo "Then reload your shell or run:"
    echo "  source ~/.bashrc  # or ~/.zshrc"
    echo ""
    echo "Alternatively, you can run the CLI directly:"
    echo "  $INSTALL_DIR/$WRAPPER_NAME --help"
else
    echo "✓ $INSTALL_DIR is in your PATH"
    echo ""
    echo "You can now use the 'fal-bundles' command:"
    echo "  fal-bundles --help"
    echo "  fal-bundles list"
    echo "  fal-bundles create <path>"
    echo "  fal-bundles download <bundle-id>"
fi

echo ""
echo "To uninstall, run:"
echo "  rm $INSTALL_DIR/$WRAPPER_NAME"