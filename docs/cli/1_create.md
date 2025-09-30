# CLI Create

## Summary

Allows users to create a bundle from local files and directories, uploading only missing blobs and creating a bundle manifest on the server.

## Input

- **Sources** — CLI command with arguments
- **Parameters**
  - Args: One or more file or directory paths (positional arguments)
  - Flags: (future: --exclude patterns, --verbose)
- **Pre-Conditions**
  - Each supplied path exists and is readable
  - Effective file set after recursion is non-empty
  - Server is reachable

## Implementation Details

- Parse CLI arguments using argparse or click
- Discovers and hashes files
  - Recursively walks all input directories to find files
  - For each file:
    - Calculates relative path from input base
    - Stream-calculates SHA-256 hash
    - Records file size
    - Creates `Blob` object (see docs/types.md)
  - Handles symbolic links, permissions, etc.
- Performs preflight check
  - Sends `PreflightRequest` to `POST /bundles/preflight`
  - Parses response to get list of missing hashes
  - Filters file list to only include files that need upload
- Uploads missing blobs
  - For each file with missing hash:
    - Streams file content to `PUT /blobs/{hash}?size_bytes={size}`
    - Handles upload errors and retries
    - Shows progress for large files/many files
- Creates bundle
  - Constructs `BundleManifestDraft` with all files
  - Sends to `POST /bundles`
  - Handles bundle creation errors
- Prints bundle ID on success

## Side Effects

- Uploads missing blobs to server
- Creates new bundle manifest on server

## Output: Success

- STDOUT: `"Created bundle: {id}"`
- Exit code: 0

## Output: Errors

- Exit code 2: invalid/missing path(s) (precondition failure)
- Exit code 3: server reported missing blobs at commit (consistency error - shouldn't happen if upload succeeded)
- Exit code 4: network/IO errors
- Clear error messages with context for different failure modes

### Testing
- Unit tests for file discovery and hashing
- Integration tests with mock API server
- Error case testing (network failures, permission errors)
- Performance testing with large files and many files
- End-to-end testing with real API server
