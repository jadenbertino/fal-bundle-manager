# Create Bundle

## Summary

Allows clients to create a bundle from already-uploaded blobs, generating a manifest that maps file paths to content hashes for later retrieval.

## Input

- **Sources** — HTTP POST request to `/bundles`
- **Parameters**
  - Body: `BundleManifestDraft`:
    ```typescript
    type BundleManifestDraft = {
      files: Blob[],       // Array of Blob objects (see docs/types.md)
      hash_algo: "sha256", // Hash algorithm (must be "sha256")
      merkle_root: string  // SHA-256 Merkle root over bundle files
    }
    ```
- **Pre-Conditions**
  - All referenced blob hashes exist in blob store
  - Paths are unique (no duplicates)
  - Paths are relative (no '..', no leading '/')
  - `size_bytes` is non-negative integer
  - `hash_algo` is "sha256"
  - Each hash is 64-character lowercase hex

## Implementation Details

- Accept POST requests to `/bundles`
- Validates request
  - `BundleManifestDraft` schema contains array of `Blob` objects in `files` field
  - Each file entry has unique `bundle_path`: relative path, no `..` or leading `/`
  - Each file entry has valid `size_bytes`: non-negative integer
  - Each file entry has valid `hash`: 64-character lowercase hex; throws `400` error if not
  - Each file entry has `hash_algo` set to "sha256"
  - Rejects duplicate paths; throws `400` error if duplicates found
  - Validates `merkle_root` is a valid SHA-256 hash
- Verifies blob existence
  - For each file in manifest, verify blob exists at `api/.data/blobs/{first2chars}/{next2chars}/{fullhash}`
  - Uses efficient batch checking (reuses preflight logic)
  - Fails with `409` Conflict if any blob is missing
- Generates bundle ID
  - Always generates unique ULID for time-ordering
- Computes statistics
  - Calculates `file_count` (length of files array)
  - Sums `size_bytes` for all files to get `total_bytes`
  - Validates client-provided `merkle_root` matches server-computed value
- Stores bundle data
  - Creates complete `BundleManifest` object with id, created_at (ISO-8601), hash_algo, files, file_count, total_bytes, and merkle_root
  - Writes **manifest** as JSON to `api/.data/bundles/manifests/{id}.json` (includes `files` array)
  - Writes **summary** as JSON to `api/.data/bundles/summaries/{id}.json` (excludes `files` array for efficiency but retains `merkle_root`)
  - Ensures atomic write operation for both files
- Returns `201` Created with bundle metadata

## Side Effects

- Writes bundle manifest file to `api/.data/bundles/manifests/{id}.json`
- Writes bundle summary file to `api/.data/bundles/summaries/{id}.json`

## Output: Success

- HTTP `201` Created with `BundleCreateResponse`:
  ```typescript
  type BundleCreateResponse = {
    id: string,           // Unique bundle identifier (ULID if auto-generated)
    created_at: string,   // ISO 8601 timestamp (e.g., `2023-12-25T10:30:00Z`)
    merkle_root: string   // SHA-256 Merkle root over bundle contents
  }
  ```

## Output: Errors

- HTTP `400` Bad Request: invalid schema, duplicate paths, bad sha256, negative size, invalid paths
- HTTP `409` Conflict: manifest references missing blob(s), merkle root mismatch
- HTTP `500` Internal Server Error: storage write failure

### Testing
- Unit tests for validation logic
- Integration tests with blob storage
- Error case testing (missing blobs, merkle root mismatch, malformed data)
- Atomic operation testing (partial failure scenarios)
- Statistics calculation testing
