### Blob Storage

**Location**: `api/.data/blobs/`

**Structure**:
```
api/.data/blobs/{first2}/{next2}/{fullhash}
```

**Example**:
```
SHA-256: a1b2c3d4e5f6...
Path:    api/.data/blobs/a1/b2/a1b2c3d4e5f6...
```

**Benefits**:
- Fanout structure prevents excessive files per directory
- Content-addressable enables automatic deduplication
- Immutable blobs enable caching and safe concurrent access

**Upload Flow**:
1. Write to temp file: `api/.data/tmp/{timestamp}_{uuid}`
2. Stream and verify SHA-256 hash
3. Move to final location (atomic operation)
4. Return 409 Conflict if hash mismatch

### Bundle Storage

Bundle data is split into two separate locations for efficiency:

#### Bundle Manifests

**Location**: `api/.data/bundles/manifests/`

**Structure**:
```
api/.data/bundles/manifests/{id}.json
```

**Purpose**: Complete bundle information including file list (used for downloads)

**Manifest Format**:
```json
{
  "id": "01HQZX...",
  "created_at": "2023-12-25T10:30:00Z",
  "hash_algo": "sha256",
  "merkle_root": "a1b2c3d4...",
  "files": [
    {
      "bundle_path": "models/config.yaml",
      "size_bytes": 1024,
      "hash": "a1b2c3d4...",
      "hash_algo": "sha256"
    }
  ],
  "file_count": 10,
  "total_bytes": 524288
}
```

#### Bundle Summaries

**Location**: `api/.data/bundles/summaries/`

**Structure**:
```
api/.data/bundles/summaries/{id}.json
```

**Purpose**: Lightweight bundle metadata without file list (used for listing operations)

**Summary Format**:
```json
{
  "id": "01HQZX...",
  "created_at": "2023-12-25T10:30:00Z",
  "hash_algo": "sha256",
  "file_count": 10,
  "total_bytes": 524288,
  "merkle_root": "a1b2c3d4..."
}
```

**Benefits**:
- Summaries are much smaller (no `files` array)
- List operations are faster and use less memory
- Download operations use manifests to get complete file information
- Both files are created atomically when a bundle is created
- `merkle_root` enables lightweight integrity checks without reading manifests
