# CLI List

## Summary

Allows users to see all available bundles in a readable table format, sorted by creation time.

## Input

- **Sources** — CLI command
- **Parameters**
  - None (MVP)
  - Flags: (future: --format, --sort)
- **Pre-Conditions**
  - Server is reachable

## Implementation Details

- Parse CLI command (no arguments required)
- Fetches bundle list
  - Makes GET request to `/bundles` endpoint
  - Parses JSON response into `BundleListResponse`
  - Handles HTTP errors appropriately
  - Adds request timeout and retry logic
- Formats data
  - Implements human-readable size formatting:
    - Bytes: "1,234 B"
    - Kilobytes: "12.3 KB"
    - Megabytes: "45.6 MB"
    - Gigabytes: "7.8 GB"
  - Formats timestamps for readability:
    - ISO format: "2023-12-25T10:30:00Z" → "2023-12-25 10:30:00"
    - Or relative: "2 hours ago"
- Renders table
  - Uses library like `tabulate` or implements simple table formatting
  - Column headers: "ID | Files | Total Size | Created"
  - Proper column alignment (left for ID, right for numbers)
  - Handles varying ID lengths and large numbers
- Handles empty state
  - Displays helpful message when no bundles exist
  - Example: "No bundles found. Use 'create' command to add bundles."

## Side Effects

- None (read-only operation)

## Output: Success

- STDOUT: Formatted table with columns: ID | Files | Total Size | Created
  - Bundles sorted by creation time (newest first)
  - Human-readable size formatting
  - Readable date/time formatting
- Exit code: 0

## Output: Errors

- Exit code 4: network/IO errors or server 5xx responses
- Clear error messages for connection failures
- Graceful handling of malformed server responses

### Testing
- Unit tests for data formatting functions
- Integration tests with mock API responses
- Error case testing (network failures, empty responses)
- Table formatting tests with various data sizes
- End-to-end testing with real API server

## Implementation Steps

> This stays pretty much the same for most operations, but it's good to have a record of it.

- Create request schema
- Create response schema
- Create pseudo-code tests
- Create implementation, keep the business logic and pseudo-code in mind
- Convert pseudo-code tests to actual tests
- Run tests, fix any issues, repeat until all tests pass