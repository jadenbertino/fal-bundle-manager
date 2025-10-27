# fal-bundles

A simple system for creating, listing, and downloading resource bundles.

**Watch this demo for a quick walkthrough of usage, project structure, and architecture:**

https://www.loom.com/share/0c885d3c27c04abc97c6b49066cecf00?sid=d907a404-ac68-4548-94da-23d6b21cf5e2

## Quick Start


### 1. Start the server

```bash
./scripts/api.sh
```

The server will auto-install dependencies and run on http://localhost:8000

### 2. Install the CLI

```bash
# Install the CLI wrapper
./cli/install.sh

# Or with custom wrapper name
./cli/install.sh --name fal-bundles
```

### 3. Use the CLI

Create a bundle from files or directories:
```bash
fal-bundles create path/to/files
```

List all bundles:
```bash
fal-bundles list
```

Download a bundle:
```bash
fal-bundles download <bundle-id>
```

View help:
```bash
fal-bundles --help
```

That's it! The system automatically deduplicates files, so you won't waste storage or bandwidth on files you've already uploaded.

## Features

- Efficient storage architecture
  - Automatic deduplication - same file only stored once across all bundles
  - Fanout directory structure - prevents filesystem performance degradation
  - Concurrent file uploads for faster bundle creation times
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