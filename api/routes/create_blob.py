"""Blob upload API endpoint."""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Query, Response
from shared.api_contracts.create_blob import CreateBlobResponse
from shared.validation import validate_sha256_hash
from api.storage import blob_exists, to_blob_path
from shared.config import TMP_DIR, MAX_UPLOAD_BYTES

router = APIRouter()


@router.put("/blobs/{hash}", response_model=CreateBlobResponse)
async def upload_blob(
    hash: str,
    size_bytes: int = Query(..., ge=0),
    request: Request = None,
    response: Response = None
):
    """
    Upload a blob by its content hash.

    This endpoint accepts raw file bytes and stores them content-addressably.
    The operation is idempotent - uploading the same hash twice will succeed.

    Args:
        hash: SHA-256 hash of the file (64-character lowercase hex)
        size_bytes: Size of the file in bytes
        request: FastAPI request object containing the file body

    Returns:
        CreateBlobResponse indicating whether blob was created or already exists

    Raises:
        HTTPException:
            - 400: Invalid hash format
            - 409: Hash mismatch (uploaded content doesn't match hash)
            - 413: File size exceeds maximum allowed
            - 500: Storage/IO error
    """
    # Validate hash format
    try:
        validate_sha256_hash(hash)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Validate blob under size limit
    if size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_bytes} exceeds maximum allowed {MAX_UPLOAD_BYTES}"
        )

    # Validate blob isn't already uploaded
    if blob_exists(hash):
        response.status_code = 200
        return CreateBlobResponse(status="exists", hash=hash)

    # Prepare temporary file for upload
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    tmp_filename = f"{timestamp}_{uuid.uuid4()}"
    tmp_path = TMP_DIR / tmp_filename

    try:
        # Stream file to temp location + hash
        hasher = hashlib.sha256()
        bytes_written = 0
        with open(tmp_path, "wb") as f:
            async for chunk in request.stream():
                hasher.update(chunk)
                f.write(chunk)
                bytes_written += len(chunk)

        # Validate hash matches
        calculated_hash = hasher.hexdigest()
        if calculated_hash != hash:
            tmp_path.unlink()  # Remove invalid file
            raise HTTPException(
                status_code=409,
                detail=f"Hash mismatch: expected {hash}, got {calculated_hash}"
            )

        # Move to final location with fanout structure
        blob_path = to_blob_path(hash)
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.rename(blob_path)

        # Return success
        response.status_code = 201
        return CreateBlobResponse(status="created", hash=hash)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
