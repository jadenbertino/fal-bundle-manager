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
├── config.py              # Configuration (env vars, constants)
└── requirements.txt
```

### ./cli/
CLI implementation

```
├── __init__.py
├── __main__.py            # CLI entry point (python -m cli)
├── commands/              # CLI command implementations
│   ├── __init__.py
│   ├── create.py          # Create bundle command
│   ├── list.py            # List bundles command
│   └── download.py        # Download bundle command
├── client.py              # API client for server communication
├── utils.py               # Utilities (hashing, formatting, progress)
├── config.py              # CLI configuration (server URL, etc.)
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

### ./tests/
Test suite

```
├── __init__.py
├── api/                   # API tests
│   ├── test_blobs.py
│   └── test_bundles.py
├── cli/                   # CLI tests
│   ├── test_create.py
│   ├── test_list.py
│   └── test_download.py
├── integration/           # End-to-end integration tests
│   └── test_e2e.py
├── fixtures/              # Test fixtures and sample data
└── requirements.txt
```

### ./data/
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
Example files for testing and development

```
├── models/
└── config/
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
