# CLI Download

## Summary

Allows users to download a bundle as an archive file with streaming support and progress indication.

## Input

- **Sources** — CLI command with arguments and flags
- **Parameters**
  - Args: `bundle_id` (required positional argument)
  - Flags: `--format` (optional, default: "zip")
- **Pre-Conditions**
  - Bundle with given ID exists on server
  - Server is reachable
  - Current directory is writable

## Implementation Details

- Parse CLI arguments
  - Required positional argument: bundle_id
  - Optional `--format` flag with default "zip"
  - Validates bundle ID format (basic sanity check)
- Downloads archive
  - Makes GET request to `/bundles/{id}/download?format={format}`
  - Implements streaming download:
    - Writes response chunks to local file
    - Doesn't load entire response into memory
    - Handles partial downloads gracefully
  - Generates filename: `bundle_{bundle_id}.{extension}`
  - Saves to current working directory
- Shows progress
  - Displays download progress for large files
  - Shows: current size, total size (if available), percentage
  - Uses progress bar or simple text updates
- Handles file conflicts
  - Checks if target file already exists (prompt user or auto-rename)
  - Ensures atomic write (temp file → rename)
  - Sets appropriate file permissions
  - Cleans up on interrupted downloads
- Prints success message with filename

## Side Effects

- Writes archive file to current working directory

## Output: Success

- STDOUT: `"Downloaded bundle_{id}.{ext}"`
- File: `bundle_{bundle_id}.{extension}` in current working directory
- Exit code: 0

## Output: Errors

- Exit code 1: unknown/unsupported format flag
- Exit code 2: bundle not found (404)
- Exit code 4: network/IO errors
- Clear error messages with context:
  - Bundle not found: "Bundle {id} not found"
  - Network error: "Download failed: {reason}"
  - Format error: "Unsupported format: {format}"

### Testing
- Unit tests for filename generation and validation
- Integration tests with mock API responses
- Error case testing (missing bundles, network failures, disk full)
- Progress indication testing
- Large file download testing
- End-to-end testing with real API server
