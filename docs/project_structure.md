## Directory Structure

### ./api/
API server implementation

```
├── __init__.py
├── app.py                 # FastAPI application entry point
├── routes/                # API route handlers
│   ├── __init__.py
│   ├── blobs.py           # Blob upload endpoint
│   └── bundles.py         # Bundle management endpoints
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── blob_service.py    # Blob storage operations
│   └── bundle_service.py  # Bundle management operations
├── storage/               # Storage abstractions
│   ├── __init__.py
│   ├── blob_store.py      # Blob storage implementation
│   └── bundle_store.py    # Bundle manifest storage
├── scripts/               # Development scripts
│   ├── setup.sh           # Setup virtual environment and dependencies
│   ├── start.sh           # Start development server
│   └── test.sh            # Run test suite
├── tests/                 # API tests
│   ├── __init__.py
│   ├── test_status.py     # Status endpoint test
│   └── requirements.txt   # Test dependencies
├── config.py              # Configuration (env vars, constants)
└── requirements.txt
```

### ./cli/
CLI implementation

```
├── __init__.py
├── __main__.py            # CLI entry point with argparse
├── commands/              # CLI command wrappers
│   ├── __init__.py
│   ├── create.py          # CLI wrapper for create command
│   ├── list.py            # CLI wrapper for list command
│   └── download.py        # CLI wrapper for download command
├── core/                  # Core business logic (testable, no CLI deps)
│   ├── __init__.py
│   ├── file_discovery.py  # Walk directories, collect files with metadata
│   ├── hashing.py         # SHA-256 hashing with streaming
│   ├── uploader.py        # Orchestrate preflight + upload missing blobs
│   └── bundler.py         # Full create bundle workflow orchestration
├── client.py              # API client (HTTP requests to server)
├── utils.py               # Formatting, progress bars, display utilities
├── config.py              # CLI configuration (server URL, timeout, etc.)
└── requirements.txt
```

### ./shared/
Shared code between API and CLI

```
├── __init__.py
├── types.py               # Domain types: Blob, BundleSummary, BundleManifest
├── validation.py          # Shared validation logic (hash, path validators)
└── api_contracts/         # API request/response schemas
    ├── __init__.py
    ├── preflight.py       # PreflightRequest, PreflightResponse
    ├── create_blob.py     # Blob upload validation
    ├── create_bundle.py   # BundleManifestDraft, BundleCreateResponse
    ├── list_bundles.py    # BundleListResponse
    └── download_bundle.py # Download parameters
```


### ./.data/
Runtime data (gitignored)

```
├── blobs/                 # Content-addressed blob storage
│   └── {aa}/              # Fanout: first 2 hex chars
│       └── {bb}/          # Fanout: next 2 hex chars
│           └── {hash}     # Full 64-char SHA-256 hash
├── bundles/               # Bundle manifests
│   └── {id}.json          # Bundle manifest files
└── tmp/                   # Temporary upload staging
```

### ./fixtures/
Test fixtures and example files for testing and development

```
└── test_data/              # Test fixtures for CLI/API testing
    ├── README.txt          # Documentation
    ├── file1.txt           # Small test file (12 bytes)
    ├── file2.txt           # Multi-line test file
    ├── empty.txt           # Empty file for edge cases
    ├── large.bin           # Larger file for streaming tests
    ├── configs/            # Directory with config files
    │   ├── app.yaml
    │   └── database.json
    ├── models/             # Model directory
    │   └── model.txt
    ├── nested/             # Deeply nested structure
    │   └── deep/
    │       └── buried.txt
    └── empty_dir/          # Empty directory with .gitkeep
        └── .gitkeep
```

### ./docs/
Documentation

```
├── api/                   # API endpoint contracts
├── cli/                   # CLI command contracts
├── internal/              # Internal documentation
├── types.md               # Shared type definitions
└── architecture.md        # This file
```

### ./
Root files

```
├── .gitignore
├── README.md
└── DEVELOPERS.md
```
