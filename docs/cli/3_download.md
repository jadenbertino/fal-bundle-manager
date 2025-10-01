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

## Business Logic

- Parse and validate CLI arguments
  - Required positional argument: bundle_id
  - Optional `--format` flag with default "zip"
  - Validates bundle ID format (basic sanity check)
  - Error: Exit code 1 if format is unknown/unsupported
- Download archive from server
  - Makes GET request to `/bundles/{id}/download?format={format}`
  - Error: Exit code 2 if bundle not found (404 response)
  - Error: Exit code 4 if network/connection errors occur
  - Implements streaming download:
    - Writes response chunks to local file as they arrive
    - Doesn't load entire response into memory
    - Handles partial downloads gracefully
  - Generates filename: `bundle_{bundle_id}.{extension}`
  - Saves to current working directory
  - Error: Exit code 4 if disk full or write permissions denied
- Display download progress
  - Shows download progress for large files
  - Displays: current size, total size (if available), percentage
  - Updates progress bar or simple text as download progresses
- Handle file conflicts and ensure data integrity
  - Checks if target file already exists (prompt user or auto-rename)
  - Ensures atomic write (temp file → rename on success)
  - Sets appropriate file permissions on final file
  - Cleans up temporary files on interrupted downloads
- Output success message with filename

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

## Testing

```gherkin
Feature: CLI Download Command

  Scenario: Successfully download bundle with default format
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And the current directory is writable
    When the user runs "cli download 01HQZX123ABC"
    Then the command should make a GET request to "/bundles/01HQZX123ABC/download?format=zip"
    And the response archive should be saved to "bundle_01HQZX123ABC.zip"
    And the command should output "Downloaded bundle_01HQZX123ABC.zip"
    And the command should exit with code 0

  Scenario: Successfully download bundle with explicit format
    Given a bundle with ID "01HQZX456DEF" exists on the server
    And the current directory is writable
    When the user runs "cli download 01HQZX456DEF --format zip"
    Then the command should make a GET request to "/bundles/01HQZX456DEF/download?format=zip"
    And the response archive should be saved to "bundle_01HQZX456DEF.zip"
    And the command should exit with code 0

  Scenario: Download large bundle with progress indication
    Given a bundle with ID "01HQZX789GHI" exists on the server
    And the bundle archive size is 100 MB
    And the current directory is writable
    When the user runs "cli download 01HQZX789GHI"
    Then the command should display progress updates during download
    And the progress should show bytes downloaded and percentage
    And the final file should be saved as "bundle_01HQZX789GHI.zip"
    And the command should exit with code 0

  Scenario: Download bundle not found
    Given no bundle with ID "01HQZX999XXX" exists on the server
    When the user runs "cli download 01HQZX999XXX"
    Then the command should receive a 404 response from the server
    And the command should output an error message "Bundle 01HQZX999XXX not found"
    And no file should be created in the current directory
    And the command should exit with code 2

  Scenario: Unsupported archive format
    Given a bundle with ID "01HQZX123ABC" exists on the server
    When the user runs "cli download 01HQZX123ABC --format tar.bz2"
    Then the command should output an error message "Unsupported format: tar.bz2"
    And no API request should be made
    And no file should be created in the current directory
    And the command should exit with code 1

  Scenario: Network connection failure during download
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And the current directory is writable
    When the user runs "cli download 01HQZX123ABC"
    And the network connection fails during the download
    Then the command should output an error message "Download failed: {network error details}"
    And any partial download files should be cleaned up
    And the command should exit with code 4

  Scenario: Server unavailable
    Given the API server is not running
    When the user runs "cli download 01HQZX123ABC"
    Then the command should output an error message "Download failed: {connection error details}"
    And no file should be created in the current directory
    And the command should exit with code 4

  Scenario: Disk full during download
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And the current directory has insufficient disk space
    When the user runs "cli download 01HQZX123ABC"
    Then the command should output an error message "Download failed: {disk space error}"
    And any partial download files should be cleaned up
    And the command should exit with code 4

  Scenario: No write permissions in current directory
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And the current directory is not writable
    When the user runs "cli download 01HQZX123ABC"
    Then the command should output an error message "Download failed: {permission error}"
    And the command should exit with code 4

  Scenario: File already exists in target location
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And a file "bundle_01HQZX123ABC.zip" already exists in the current directory
    When the user runs "cli download 01HQZX123ABC"
    Then the command should prompt the user or auto-rename the file
    And the download should complete successfully
    And the command should exit with code 0

  Scenario: Download interrupted mid-transfer
    Given a bundle with ID "01HQZX123ABC" exists on the server
    And the current directory is writable
    When the user runs "cli download 01HQZX123ABC"
    And the download is interrupted (e.g., user presses Ctrl+C)
    Then any temporary files should be cleaned up
    And no incomplete archive file should remain in the current directory

  Scenario: Streaming download does not exhaust memory
    Given a bundle with ID "01HQZX999XXX" exists on the server
    And the bundle archive size is 2 GB
    When the user runs "cli download 01HQZX999XXX"
    Then the download should stream chunks to disk
    And the command should not load the entire archive into memory
    And the command should complete successfully
    And the command should exit with code 0

  Scenario: Invalid bundle ID format
    Given the user provides an invalid bundle ID "invalid#id!"
    When the user runs "cli download invalid#id!"
    Then the command should output a validation error message
    And no API request should be made
    And the command should exit with a non-zero code

  Scenario: Empty bundle download
    Given a bundle with ID "01HQZX000000" exists on the server
    And the bundle contains zero files
    When the user runs "cli download 01HQZX000000"
    Then the command should download an empty archive
    And the archive should be saved as "bundle_01HQZX000000.zip"
    And the command should exit with code 0
```

## Implementation Steps

- Ensure contract is filled out
- Create CLI argument parser with bundle_id and --format flag
- Create API client method for download endpoint
- Implement streaming download logic:
  - Create temporary file for atomic writes
  - Stream response chunks to temp file
  - Verify download completion
  - Rename temp file to final name
- Implement progress indication (progress bar or text updates)
- Implement cleanup logic for interrupted downloads
- Implement file conflict handling (existing files)
- Convert Gherkin test scenarios to actual tests
- Run tests, fix any issues, repeat until all tests pass
