# Integration Tests

This directory contains comprehensive integration tests for the fal-bundles CLI system.

## Files

- `integration_simple.py` - Simplified integration tests that work with proper mocking
- `integration.py` - Comprehensive integration tests (may need environment setup)

## Test Coverage

The integration tests cover the complete workflow:

### 1. Bundle Creation
- Single file uploads
- Directory uploads with multiple files
- Mixed files and directories
- Complex nested directory structures
- Special characters in filenames
- Empty files and large files

### 2. Bundle Listing
- Verify bundle appears in list
- Check metadata (file count, size, creation date)
- Verify merkle root is displayed

### 3. Bundle Download
- Download bundle as ZIP file
- Extract and verify all files are present
- Verify file contents match original

### 4. Merkle Root Verification
- Compute merkle root from original files
- Download and extract bundle
- Recompute hashes from extracted files
- Recompute merkle root from extracted files
- Verify merkle roots match (integrity check)

### 5. Error Handling
- Non-existent files
- Empty directories
- Network errors
- Invalid bundle IDs

## Key Features Tested

### Complete Workflow
1. **Create** bundle from files/directories
2. **List** bundles and verify existence
3. **Download** bundle and extract contents
4. **Verify** merkle root integrity

### Merkle Root Verification
The tests implement the full integrity verification process:
1. Compute expected merkle root from original files
2. Create bundle with computed merkle root
3. Download bundle and extract files
4. Recompute hashes from extracted files
5. Recompute merkle root from extracted files
6. Verify both merkle roots match

This ensures that:
- Files are not corrupted during upload/download
- Bundle integrity is maintained
- Content-addressable storage works correctly

## Running Tests

```bash
# Run simplified integration tests
python -m pytest tests/integration_simple.py -v

# Run all integration tests (requires proper environment)
python -m pytest tests/integration.py -v
```

## Test Scenarios

### Single File Workflow
- Creates a single file
- Computes merkle root
- Creates bundle
- Lists bundle
- Downloads bundle
- Extracts and verifies content
- Recomputes merkle root and verifies match

### Complex Directory Workflow
- Creates nested directory structure
- Multiple files at different levels
- Mixed text and binary files
- Computes merkle root for all files
- Creates bundle
- Downloads and extracts
- Verifies all files and content
- Recomputes merkle root and verifies integrity

### Error Scenarios
- Non-existent files
- Empty directories
- Merkle root mismatches
- Network failures

## Mocking Strategy

The tests use comprehensive mocking to:
- Mock API client responses
- Simulate ZIP file creation and download
- Test error scenarios
- Verify complete workflows without requiring a real API server

This ensures tests are fast, reliable, and don't depend on external services.
