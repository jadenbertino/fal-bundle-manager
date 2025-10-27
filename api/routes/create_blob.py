"""Blob upload API endpoint."""

from datetime import datetime
import hashlib
import uuid

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from api.storage import blob_exists, get_blob_path
from shared.config import MAX_UPLOAD_BYTES, get_tmp_dir
from shared.validation import validate_sha256_hash

router = APIRouter()


@router.put("/blobs/{hash}")
async def upload_blob(
    hash: str,
    size_bytes: int = Query(..., ge=0),
    request: Request = None
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
        BlobUploadResponse indicating whether blob was created or already exists

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

    # Check size limit
    if size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_bytes} exceeds maximum allowed {MAX_UPLOAD_BYTES}"
        )

    # Check if blob already exists (idempotency)
    if blob_exists(hash):
        return JSONResponse(
            status_code=200,
            content={"status": "exists", "hash": hash}
        )

    # Prepare temporary file for upload
    tmp_dir = get_tmp_dir()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    tmp_filename = f"{timestamp}_{uuid.uuid4()}"
    tmp_path = tmp_dir / tmp_filename

    try:
        # Stream file to temp location while calculating hash
        hasher = hashlib.sha256()
        bytes_written = 0
        with open(tmp_path, "wb") as f:
            async for chunk in request.stream():
                hasher.update(chunk)
                f.write(chunk)
                bytes_written += len(chunk)

        # Verify hash matches
        calculated_hash = hasher.hexdigest()
        if calculated_hash != hash:
            tmp_path.unlink()  # Remove invalid file
            raise HTTPException(
                status_code=409,
                detail=f"Hash mismatch: expected {hash}, got {calculated_hash}"
            )

        # Move to final location with fanout structure
        blob_path = get_blob_path(hash)
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.rename(blob_path)

        # Return success
        return JSONResponse(
            status_code=201,
            content={"status": "created", "hash": hash}
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
