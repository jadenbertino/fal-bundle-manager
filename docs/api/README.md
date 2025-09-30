
### Endpoints

#### 1. Preflight Check
- For more details, see [docs/api/1_preflight.md](./1_preflight.md)
- **Route**: `POST /bundles/preflight`
- **Purpose**: Check which blobs need to be uploaded
- **Request**: Array of `Blob` objects
- **Response**: Array of missing SHA-256 hashes
- **Details**: Enables efficient deduplication by identifying blobs that already exist

#### 2. Upload Blob
- For more details, see [docs/api/2_create_blob.md](./2_create_blob.md)
- **Route**: `PUT /blobs/{hash}?size_bytes={size}`
- **Purpose**: Upload a blob by its content hash
- **Request**: Raw file bytes
- **Response**: `201 Created` (new) or `200 OK` (exists)
- **Details**:
  - Idempotent operation
  - Verifies hash matches content
  - Stores in fanout directory structure: `data/blobs/{aa}/{bb}/{hash}`

#### 3. Create Bundle
- For more details, see [docs/api/3_create_bundle.md](./3_create_bundle.md)
- **Route**: `POST /bundles`
- **Purpose**: Create a bundle from uploaded blobs
- **Request**: `BundleManifestDraft` (files array, optional id)
- **Response**: Bundle id and created_at timestamp
- **Details**:
  - Validates all referenced blobs exist
  - Generates ULID for bundle id if not provided
  - Stores manifest as JSON

#### 4. List Bundles
- For more details, see [docs/api/4_list_bundles.md](./4_list_bundles.md)
- **Route**: `GET /bundles`
- **Purpose**: Retrieve all bundle metadata
- **Response**: Array of `BundleSummary` objects
- **Details**: Sorted by created_at descending (newest first)

#### 5. Download Bundle
- For more details, see [docs/api/5_download_bundle.md](./5_download_bundle.md)
- **Route**: `GET /bundles/{id}/download?format=zip`
- **Purpose**: Download bundle as archive
- **Response**: Streaming ZIP file
- **Details**:
  - Streams archive directly to avoid loading into memory
  - Preserves relative file paths from bundle manifest
