# fal-bundles CLI

Command-line interface for managing resource bundles.

## Quick Start

Just run the CLI! The setup happens automatically on first use:

```bash
cd cli
./scripts/run.sh --help
./scripts/run.sh create file.txt
```

On first run, the script will:
1. Create a virtual environment (if needed)
2. Install dependencies
3. Auto-update dependencies when requirements change

## Manual Setup (Optional)

If you prefer to set up manually:

```bash
cd cli
./scripts/setup.sh
```

## Usage

### Using the run script (recommended)

```bash
./scripts/run.sh --help
./scripts/run.sh create file.txt
./scripts/run.sh create file1.txt dir/ file2.txt
```

### With activated venv

```bash
cd cli
source .venv/bin/activate
export PYTHONPATH=..
python -m cli --help
```

## Commands

### create

Create a bundle from local files and directories.

```bash
# Single file
./scripts/run.sh create myfile.txt

# Directory (recursive)
./scripts/run.sh create my_directory/

# Multiple paths
./scripts/run.sh create file1.txt dir1/ file2.txt

# Custom API URL
./scripts/run.sh create --api-url http://localhost:8000 myfile.txt
```

**Output:** `Created bundle: <bundle-id>`

**Exit codes:**
- `0` - Success
- `2` - Invalid/missing paths
- `4` - Network/IO errors

## Testing

Run all tests:

```bash
./scripts/test.sh
```

Run specific test file:

```bash
./scripts/test.sh tests/test_cli_create.py
```

Run with verbose output:

```bash
./scripts/test.sh -v
```

## Development

### Project Structure

```
cli/
├── __init__.py
├── __main__.py              # CLI entry point
├── client.py                # API client
├── config.py                # Configuration
├── commands/                # Command implementations
│   ├── create.py
│   ├── list.py              # TODO
│   └── download.py          # TODO
├── core/                    # Core business logic
│   ├── file_discovery.py
│   ├── hashing.py
│   ├── bundler.py
│   └── uploader.py
├── tests/                   # Tests
│   ├── test_create_bundle.py   # Core logic tests
│   └── test_cli_create.py      # CLI integration tests
└── scripts/                 # Helper scripts
    ├── setup.sh
    ├── test.sh
    └── run.sh
```

### Environment Variables

- `FAL_BUNDLES_API_URL` - API server URL (default: `http://localhost:8000`)
- `FAL_BUNDLES_TIMEOUT` - Request timeout in seconds (default: `300`)

## Dependencies

- **pydantic** - Data validation (shared types)
- **requests** - HTTP client
- **click** - CLI framework
- **pytest** - Testing framework
