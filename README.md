# fal-bundles

A content-addressable storage system for managing resource bundles.

## Quickstart

### Setup

```bash
./api/scripts/setup.sh
```

This will create a virtual environment at `api/.venv` and install all dependencies.

### Start the Development Server

```bash
./api/scripts/start.sh
```

The server will start on http://localhost:8000 (configurable via `HOST` and `PORT` environment variables).

### Run Tests

```bash
./api/scripts/test.sh
```

### Available Endpoints

- `GET /status` - Health check endpoint (returns 200 OK)

## Development

### Scripts

All development scripts are located in `api/scripts/`:

- **`setup.sh`** - Creates virtual environment and installs dependencies
- **`start.sh`** - Starts the development server (runs setup automatically if needed)
- **`test.sh`** - Runs the test suite with pytest

### Environment Variables

**API Server:**
- `DATA_DIR` - Data storage location (default: `./data`)
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)

### Manual Commands

If you prefer to run commands manually:

```bash
# Activate virtual environment
source api/.venv/bin/activate

# Run server
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v
```

### Project Structure

```
api/
├── app.py              # FastAPI application
├── requirements.txt    # API dependencies
└── scripts/
    ├── setup.sh        # Setup script
    ├── start.sh        # Start server script
    └── test.sh         # Test runner script

tests/
├── test_status.py      # API tests
└── requirements.txt    # Test dependencies
```