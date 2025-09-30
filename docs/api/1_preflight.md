# Bundle Preflight

## Summary

Allows clients to check which blobs need to be uploaded before creating a bundle, enabling efficient deduplication by only uploading missing files.

## Input

- **Sources** — HTTP POST request to `/bundles/preflight`
- **Parameters**
  - Body: `PreflightRequest`:
    ```typescript
    type PreflightRequest = {
      files: Blob[]  // Array of Blob objects (see docs/types.md)
    }
    ```
- **Pre-Conditions**
  - Each sha256 is lowercase 64-hex
  - Paths are relative (no '..', no leading '/')
  - `size_bytes` is non-negative integer
  - `hash_algo` is "sha256"
  - No duplicate paths in single request

## Implementation Details

- Accept POST requests to `/bundles/preflight`
- Validates request
  - `PreflightRequest` schema contains array of `Blob` objects
  - Each blob entry has valid `bundle_path`: relative path, no `..` or leading `/`
  - Each blob entry has valid `size_bytes`: non-negative integer
  - Each blob entry has valid `hash`: 64-character lowercase hex; throws `400` error if not
  - Each blob entry has `hash_algo` set to "sha256"
  - Rejects duplicate paths in single request; throws `400` error if duplicates found
- Checks blob existence
  - For each hash, check if blob file exists at `data/blobs/{first2chars}/{next2chars}/{fullhash}`
  - Uses efficient file existence checking (avoids directory scans)
  - Builds set of missing hashes
- Returns `PreflightResponse` with array of missing hashes
- Returns `200` OK with empty array if no files missing

## Side Effects

- None (read-only operation, no writes)

## Output: Success

- HTTP `200` OK with `PreflightResponse`:
  ```typescript
  type PreflightResponse = {
    missing: string[]  // Array of SHA-256 hashes (64-char lowercase hex) that don't exist in blob store
  }
  ```
  - Empty array if all blobs already exist

## Output: Errors

- HTTP `400` Bad Request: invalid schema, duplicate paths, bad sha256, negative size, invalid paths
- HTTP `500` Internal Server Error: storage/index read failure

### Testing
- Unit tests for request validation
- Integration tests with actual blob storage
- Error case testing (malformed requests, storage failures)
- Performance testing with large file lists
- Edge cases (empty requests, all files missing, no files missing)
