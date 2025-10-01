# Upload Blob

## Summary

Allows clients to upload a blob by its hash, ensuring idempotency and deduplication.

## Input

- **Sources** — HTTP PUT request to `/blobs/{hash}?size_bytes={size_bytes}`
- **Parameters**
  - Path params: `hash` (hex64, lowercase), size_bytes (non-negative integer)
  - Body: raw bytes of the file
- **Pre-Conditions**
  - sha256 matches the SHA-256 of the body bytes (caller's promise)
  - Target blob does not need to be absent; operation is idempotent

## Implementation Details

- Accept PUT requests to `/blobs/{hash}?size_bytes={size_bytes}`
- Validates request
  - hash is sha256 64-character lowercase hex; throws `400` error if not
  - size_bytes <= ENV.MAX_UPLOAD_BYTES (1gb default); throws `413` if exceeded
- Checks if file already exists; if yes then early `200` return
- verifies file integrity
  - Writes the file to `.data/tmp/<iso timestamp>_<uuid>`
  - stream hashes the file and verifies it matches the provided SHA-256 hash
  - throws `409` on mismatch
- Stores file
  - moves file from `.data/tmp/` to `.data/blobs`
  - Store blobs with fanout directory structure in the format: `.data/blobs/{first2chars}/{next2chars}/{fullhash}`
- Return `201` Created for new blob

## Side Effects

- Writes blob to blob store; creates fanout dirs as needed

## Output: Success

- HTTP `201` Created (first write)
- HTTP `200` OK (already exists)

## Output: Errors

- HTTP `400` Bad Request: invalid sha256 format
- HTTP `409` Conflict: digest mismatch (hash != body)
- HTTP `413` Payload Too Large: exceeds server limit (if enforced)
- HTTP `500` Internal Server Error: disk/full/IO error

### Testing
- Unit tests for hash validation
- Integration tests for file storage
- Error case testing (invalid hash, size limits, storage failures)
- Idempotency testing
- Large file streaming tests