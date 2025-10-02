# Download Bundle

## Summary

Allows clients to download a complete bundle as a streaming archive file with all files organized in their original directory structure.

## Input

- **Sources** — HTTP GET request to `/bundles/{id}/download`
- **Parameters**
  - Path param: `id` (string, bundle identifier)
  - Query param: `format` (optional, default: "zip")
- **Pre-Conditions**
  - Bundle with given id exists on server
  - Requested format is supported (currently "zip" only)
  - All referenced blobs exist in blob store

## Implementation Details

- Accept GET requests to `/bundles/{id}/download`
- Validates request
  - Validates bundle ID format
  - Checks if bundle manifest exists at `.data/bundles/{id}.json`
  - Loads and parses bundle manifest
  - Validates manifest structure (including `merkle_root` field)
  - Validates requested format against supported formats (currently "zip" only); throws `415` if unsupported
- Collects blobs
  - For each file in bundle manifest, verifies blob exists at `.data/blobs/{first2chars}/{next2chars}/{fullhash}`
  - Collects blob file path and bundle path mapping
  - Fails with `500` if any required blobs are missing
  - Optionally recomputes `merkle_root` for integrity checks before streaming
- Generates archive
  - Uses streaming ZIP generation with Python `zipfile`
  - Adds each blob to archive with correct bundle path
  - Streams directly to HTTP response (memory-efficient, avoids loading entire archive into memory)
  - Sets HTTP headers:
    - `Content-Type: application/zip`
    - `Content-Disposition: attachment; filename="bundle_{id}.zip"`
- Handles client disconnection gracefully
- Returns `200` OK with streaming archive

## Side Effects

- None (read-only operation)

## Output: Success

- HTTP `200` OK with streaming archive file
  - Format: ZIP archive (application/zip)
  - Content: All files from bundle with original relative paths preserved
  - Delivery: Streaming response for memory efficiency

## Output: Errors

- HTTP `400` Bad Request: invalid bundle ID format
- HTTP `404` Not Found: bundle does not exist
- HTTP `415` Unsupported Media Type: unsupported format requested
- HTTP `500` Internal Server Error: missing blob files, archive creation errors, storage failures

### Testing
- Unit tests for bundle validation and blob collection
- Integration tests with actual bundle and blob storage
- Error case testing (missing bundles, missing blobs, format errors)
- Performance testing with large bundles
- Streaming response testing
- Multiple format testing (when implemented)
