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

Define test scenarios in Gherkin syntax, using the following keyword definitions:

- **Feature:** Describes the functionality being tested.
- **Scenario:** Represents a single, specific test case within the feature.
- **Given:** Sets up the initial context or state (preconditions).
- **When:** Specifies the action or event performed by the user or system.
- **Then:** States the expected outcome or result.
- **And / But (Optional):** Used to add extra steps or details to any of the above.

Example:

```gherkin
Feature: [Feature Title]

  Scenario: [Scenario Title]
    Given [initial context or state/precondition]
    When [action or event]
    Then [expected outcome/result]
    And [additional assertions if needed]
  
  Scenario: [Scenario Title 2]
    ...etc
  
  Scenario: [Scenario Title 3]
    ...etc

  ...etc
```

## Implementation Steps

> This stays pretty much the same for most operations.
> Usually there's no need to change this section.

- Ensure contract is filled out
- Create request schema
- Create response schema
- Create implementation, keep the business logic and test scenarios in mind
- Convert Gherkin test scenarios to actual tests
- Run tests, fix any issues, repeat until all tests pass