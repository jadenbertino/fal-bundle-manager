# fal-bundles

A simple system for creating, listing, and downloading resource bundles.

## Quick Start

### 1. Start the server

```bash
./api/scripts/start.sh
```

The server will run on http://localhost:8000

### 2. Use the CLI

Create a bundle from files or directories:
```bash
python -m cli create path/to/files
```

List all bundles:
```bash
python -m cli list
```

Download a bundle:
```bash
python -m cli download <bundle-id>
```

That's it! The system automatically deduplicates files, so you won't waste storage or bandwidth on files you've already uploaded.

## Features

- Efficient storage architecture
  - Automatic deduplication - same file only stored once across all bundles
  - Fanout directory structure - prevents filesystem performance degradation
- Automatic dependency installation
- Efficient bundle listing: separate metadata from file lists for optimal performance
- File integrity
  - Per-file via server-side content hash verification
  - Per-bundle via merkle root calculation and verification

## Planned Features

- Caching for bundle lists - to avoid reading from disk every time
- LRU cache for bundles - to avoid re-creating bundle zips that are frequently downloaded
- Authentication/authorization
- Bundle versioning
- Partial bundle updates
- Compression options (tar.gz, tar.bz2)
- Bundle metadata tags/labels
- Search and filtering
- Garbage collection for unreferenced blobs
- Parallel uploads
- Resume interrupted downloads
- Database backend for scalability
- Remote storage backends (S3, GCS)
- Bundle size limits
- Expiration/TTL for bundles


## What's next?

- Check out [docs/architecture.md](./docs/architecture.md) for more details