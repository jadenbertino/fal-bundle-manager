# Architecture

## System Overview

The fal-bundles system is a content-addressable storage solution for managing resource bundles. It consists of two main components:

1. **API Server** - FastAPI-based REST API for blob and bundle management
2. **CLI** - Python command-line interface for creating, listing, and downloading bundles

The system uses content-addressable storage (hash-based deduplication) to efficiently store files and enable idempotent uploads.

## Core Concepts

- **Blob** - a content-addressed file stored by its SHA-256 hash. Blobs are immutable and deduplicated - the same file content is only stored once regardless of how many bundles reference it.
- **Bundle** - a collection of blobs with associated relative file paths. Bundles are represented by JSON manifests that map paths to blob hashes.
- **Deduplication** - files are identified by their SHA-256 hash. Multiple bundles can reference the same blob without duplicating storage.

## Project Structure

See [docs/project_structure.md](./project_structure.md)

## API Design

See [docs/api/README.md](./api/README.md)

## Storage Implementation

See [docs/storage/README.md](./storage/README.md)

## CLI Design

See [docs/cli/README.md](./cli/README.md)

## Data Flow

### Create Bundle Flow

```
CLI                    API Server              Storage
 |                         |                       |
 |--1. Discover files----> |                       |
 |                         |                       |
 |--2. POST /preflight---->|                       |
 |                         |--Check blob exists--->|
 |<---Missing hashes-------|                       |
 |                         |                       |
 |--3. PUT /blobs/{h}----->|                       |
 |   (for each missing)    |--Verify & store------>|
 |<---201 Created----------|                       |
 |                         |                       |
 |--4. POST /bundles------>|                       |
 |                         |--Verify blobs-------->|
 |                         |--Write manifest------>|
 |<---Bundle ID------------|                       |
 |                         |                       |
 |--5. Print ID            |                       |
```

### Download Bundle Flow

```
CLI                    API Server              Storage
 |                         |                       |
 |--1. GET /bundles/{id}-->|                       |
 |      /download          |--Read manifest------->|
 |                         |--Collect blobs------->|
 |                         |--Stream ZIP---------->|
 |<---Streaming ZIP--------|                       |
 |                         |                       |
 |--2. Write to file       |                       |
 |--3. Print success       |                       |
```

## Key Design Decisions

### 1. Content-Addressable Storage
- **Decision**: Use SHA-256 hashes as primary blob identifiers
- **Rationale**: Enables automatic deduplication, idempotent uploads, and integrity verification
- **Trade-off**: Cannot rename/modify files without creating new blobs

### 2. Fanout Directory Structure
- **Decision**: Use `{aa}/{bb}/{hash}` structure for blob storage
- **Rationale**: Prevents filesystem performance degradation with many files
- **Trade-off**: Adds slight complexity to path construction

### 3. JSON Manifests
- **Decision**: Store bundle metadata as JSON files
- **Rationale**: Simple, human-readable, no database dependency
- **Trade-off**: Not suitable for high-volume production (would need database)

### 4. Streaming Uploads/Downloads
- **Decision**: Stream file content instead of loading into memory
- **Rationale**: Supports large files without memory constraints
- **Trade-off**: Slightly more complex implementation

### 5. Preflight API
- **Decision**: Separate preflight endpoint before upload
- **Rationale**: Minimizes bandwidth by avoiding unnecessary uploads
- **Trade-off**: Adds extra round-trip for create operation

### 6. ULID for Bundle IDs
- **Decision**: Use ULIDs (time-ordered UUIDs) for bundle identifiers
- **Rationale**: Sortable, unique, includes timestamp information
- **Trade-off**: Slightly longer than sequential integers

### 7. FastAPI Framework
- **Decision**: Use FastAPI for API server
- **Rationale**: Modern, fast, built-in validation with Pydantic, async support
- **Trade-off**: Requires understanding of async/await patterns

### 8. Shared API Contracts
- **Decision**: Define request/response schemas in `shared/api_contracts/` using Pydantic
- **Rationale**: Single source of truth prevents API/CLI schema drift, enables type safety
- **Trade-off**: CLI depends on Pydantic (small dependency cost for significant benefit)

## Validation Rules

### Blob Validation
- Hash must be 64-character lowercase hexadecimal (SHA-256)
- Size must be non-negative integer
- Hash algorithm must be "sha256"
- Uploaded content must match provided hash

### Path Validation
- Must be relative (no leading `/`)
- Cannot contain `..` (directory traversal)
- No duplicate paths within single bundle
- Normalized and platform-independent

### Bundle Validation
- All referenced blobs must exist before bundle creation
- Bundle ID must be unique (if client-provided)
- File count and total bytes must match computed stats

## Error Handling

### API Error Codes
- **400 Bad Request**: Invalid input, validation failures
- **404 Not Found**: Bundle/resource doesn't exist
- **409 Conflict**: Hash mismatch, bundle ID collision, missing blobs
- **413 Payload Too Large**: File exceeds size limit
- **415 Unsupported Media Type**: Invalid archive format
- **500 Internal Server Error**: Storage failures, unexpected errors

### CLI Error Codes
- **0**: Success
- **1**: Invalid arguments/flags
- **2**: Resource not found, invalid paths
- **3**: Consistency errors (e.g., missing blobs after upload)
- **4**: Network/IO errors

## Testing Strategy

### Unit Tests
- Validation logic (paths, hashes, schemas)
- Data formatting (sizes, timestamps)
- Path construction/normalization
- Hash calculation

### Integration Tests
- API endpoint behavior with real storage
- CLI commands with mock API server
- Error scenarios and edge cases

### End-to-End Tests
- Full workflow: create → list → download
- Large file handling
- Concurrent operations
- Bundle deduplication

## Configuration

### Environment Variables

**API Server**:
- `DATA_DIR`: Data storage location (default: `./data`)
- `MAX_UPLOAD_BYTES`: Maximum blob size (default: 1GB)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)

**CLI**:
- `FAL_BUNDLES_API_URL`: API server URL (default: `http://localhost:8000`)
- `FAL_BUNDLES_TIMEOUT`: Request timeout in seconds (default: `300`)

## Future Enhancements

### Possible Extensions
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
