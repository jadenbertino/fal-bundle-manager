# Shared Types

This document defines the core data types used throughout the fal-bundles system, referenced by both API and CLI operations.

## Scope

**Include in this file:**
- Core domain primitives (e.g., `Blob`, `BundleSummary`, `BundleManifest`)
- Shared data structures used across multiple endpoints
- Common types referenced by both API and CLI

**Do NOT include in this file:**
- Request/response schemas for specific API endpoints (define these inline in `docs/api/*.md`)
- Endpoint-specific types that are only used in one place
- Transient or implementation-specific types

Request and response schemas should be defined directly within their respective API documentation files to keep endpoint contracts self-contained.

## Blob

Represents a file with its content hash and metadata.

```typescript
type Blob = {
  bundle_path: string,      // Relative path within bundle. No `..` or leading `/`
  size_bytes: number,       // File size in bytes. Non-negative integers only.
  hash: string,             // Content hash (format depends on hash_algo).
  hash_algo: "sha256"       // For now, only support SHA-256 hash (64-character lowercase hex)
}
```

## BundleSummary

Core metadata for a bundle, excluding `files` list.

```typescript
type BundleSummary = {
  id: string,                    // Unique bundle identifier
  created_at: string,            // ISO 8601 timestamp (e.g., `2023-12-25T10:30:00Z`)
  hash_algo: "sha256",           // Hash algorithm used
  file_count: number,            // Number of files in bundle
  total_bytes: number,           // Total size of all files in bytes
  merkle_root: string            // SHA-256 binary Merkle root over bundle contents
}
```

`merkle_root` is derived by sorting files by `bundle_path`, hashing each
`"{bundle_path}:{hash}"` string with SHA-256 to produce the leaves, then
building a binary Merkle tree (duplicating the final leaf when necessary)
until a single SHA-256 digest remains.

## BundleManifest

Complete bundle information including all files.

```typescript
type BundleManifest = BundleSummary & {
  files: Blob[]                  // Array of files in the bundle
}
```
