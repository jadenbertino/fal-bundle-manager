### Usage

#### 1. Create
```bash
python -m cli create <path1> [path2 ...]
```

**Flow**:
1. Discover files (recursive directory walk)
2. Hash all files (SHA-256)
3. Call preflight API to check which blobs exist
4. Upload missing blobs (with progress indication)
5. Create bundle via API
6. Prints bundle details

**Exit Codes**:
- 0: Success
- 2: Invalid/missing paths
- 3: Server reported missing blobs after upload
- 4: Network/IO errors

#### 2. List
```bash
python -m cli list
```

**Flow**:
1. Call list bundles API
2. Format as table with columns: ID, Files, Total Size, Created, Merkle Root
3. Display to stdout

**Format**:
- Human-readable sizes (B, KB, MB, GB)
- Readable timestamps
- Aligned columns

**Exit Codes**:
- 0: Success
- 4: Network/IO errors

#### 3. Download
```bash
python -m cli download <bundle_id>
```

**Flow**:
1. Call download bundle API
2. Stream response to local file: `bundle_{id}.{ext}`
3. Show progress during download
4. Print success message

**Exit Codes**:
- 0: Success
- 1: Unknown/unsupported format
- 2: Bundle not found (404)
- 4: Network/IO errors
