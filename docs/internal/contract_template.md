<!--
Usage Guide:
This template provides a consistent structure for documenting API endpoints and CLI commands.
Adapt sections to fit your specific operation's needs:

- For API endpoints: Include HTTP method, path, body, query params as applicable
- For CLI commands: Include args, flags, and command structure
- Omit sections that don't apply (e.g., Path params if none exist, Body if GET request)
- Add inline type definitions for request/response schemas (don't add to docs/types.md)
- Reference docs/types.md only for shared primitives (Blob, BundleSummary, BundleManifest)
- Adjust parameter sections based on what your operation actually uses
- Keep the overall structure consistent but flexible to your needs
-->

# [Operation Name]

## Summary

Plain language explanation of what this operation does and its purpose. Keep it concise (1-2 sentences).

## Input

- **Source** — (e.g., HTTP POST request to `/endpoint`, CLI command with arguments)
- **Parameters**
  - Body: `RequestType` (define inline if endpoint-specific, or reference docs/types.md for shared types):
    ```typescript
    type RequestType = {
      field: Type  // Description (reference docs/types.md for shared types like Blob)
    }
    ```
  - Path params
    - (e.g. `id` - description)
  - Query params
    - (e.g. `format` - optional, default: "value")
  - etc...
- **Pre-Conditions**
  - (List conditions that must be true before calling)
  - (What validation is required)
  - (Expected state of system)

## Business Logic

- (High-level description of what the operation accepts/does)
- (e.g. Validates request)
  - (Specific validation rules)
  - (e.g. What errors are thrown on validation failure)
- (e.g. Core processing steps)
  - (e.g. Detailed implementation steps)
  - (Error handling at each step)
- (e.g. Final actions)
  - (e.g. What is returned/output)

## Side Effects

- (Changes to system state, e.g., writes files, creates database records, uploads data)
- (Or "None (read-only operation)" if applicable)

## Implementation Steps

> This stays pretty much the same for most operations, but it's good to have a record of it.

- Create request schema
- Create response schema
- Create pseudo-code tests
- Create implementation, keep the business logic and pseudo-code in mind
- Convert pseudo-code tests to actual tests
- Run tests, fix any issues, repeat until all tests pass

## Output: Success

- HTTP `2XX` Status with `ResponseType` (for APIs):
  ```typescript
  type ResponseType = {
    field: Type  // Description
  }
  ```
- STDOUT: (for CLI) - Example output format
- Exit code / Status code: (specific value)

## Output: Errors

- HTTP `4XX`/`5XX` (for APIs) or Exit code X (for CLI): Description of error condition
- (List all possible error conditions with their codes and meanings)
- (Include specific error messages where applicable)

### Testing
- (Types of tests needed)
- (Specific test scenarios to cover)
- (Edge cases to validate)
