### Blob Storage

**Location**: `data/blobs/`

**Structure**:
```
data/blobs/{first2}/{next2}/{fullhash}
```

**Example**:
```
SHA-256: a1b2c3d4e5f6...
Path:    data/blobs/a1/b2/a1b2c3d4e5f6...
```

**Benefits**:
- Fanout structure prevents excessive files per directory
- Content-addressable enables automatic deduplication
- Immutable blobs enable caching and safe concurrent access

**Upload Flow**:
1. Write to temp file: `data/tmp/{timestamp}_{uuid}`
2. Stream and verify SHA-256 hash
3. Move to final location (atomic operation)
4. Return 409 Conflict if hash mismatch

### Bundle Storage

**Location**: `data/bundles/`

**Structure**:
```
data/bundles/{id}.json
```

**Manifest Format**:
```json
{
  "id": "01HQZX...",
  "created_at": "2023-12-25T10:30:00Z",
  "hash_algo": "sha256",
  "files": [
    {
      "bundle_path": "models/config.yaml",
      "size_bytes": 1024,
      "hash": "a1b2c3d4...",
      "hash_algo": "sha256"
    }
  ],
  "stats": {
    "file_count": 10,
    "bytes": 524288
  }
}
```
