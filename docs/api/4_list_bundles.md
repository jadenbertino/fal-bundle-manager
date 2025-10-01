# List Bundles

## Summary

Allows clients to retrieve a list of all available bundles with basic metadata, enabling bundle discovery and selection for download operations.

## Input

- **Sources** — HTTP GET request to `/bundles`
- **Parameters**
  - None (MVP)
- **Pre-Conditions**
  - None

## Implementation Details

- Accept GET requests to `/bundles`
- Discovers bundles
  - Enumerates all `*.json` files in `.data/bundles/` directory
  - Uses efficient directory listing (avoids loading file contents initially)
  - Filters for valid bundle manifest files
- Reads manifests
  - For each bundle file, reads minimal required fields: `id`, `created_at`, `stats.file_count`, `stats.bytes`
  - Uses streaming JSON parsing if needed for large manifests
  - Handles corrupted/invalid manifest files gracefully (logs and skips)
- Processes data
  - Converts data to `BundleSummary` format
  - Sorts by `created_at` in descending order (newest first)
  - Ensures consistent ordering for identical timestamps
- Returns `200` OK with array of bundle summaries
- Returns empty array `[]` if no bundles exist

## Side Effects

- None (read-only operation)

## Output: Success

- HTTP `200` OK with `BundleListResponse`:
  ```typescript
  type BundleListResponse = {
    bundles: BundleSummary[]  // Array of BundleSummary (see docs/types.md), sorted by created_at descending
  }
  ```
  - Empty array if no bundles exist

## Output: Errors

- HTTP `500` Internal Server Error: unable to read bundle directory or manifests, permission errors, storage failures

### Testing
- Unit tests for manifest parsing
- Integration tests with actual bundle storage
- Error case testing (corrupted files, permission errors)
- Performance testing with many bundles
- Edge cases (empty directory, invalid JSON files)
