"""Preflight API endpoint."""

from fastapi import APIRouter, HTTPException
from shared.api_contracts.preflight import PreflightRequest, PreflightResponse
from api.storage import blob_exists

router = APIRouter()


@router.post("/bundles/preflight", response_model=PreflightResponse)
async def preflight(request: PreflightRequest) -> PreflightResponse:
    """
    Check which blobs need to be uploaded.

    This endpoint allows clients to check which blobs already exist in storage,
    enabling efficient deduplication by only uploading missing files.

    Args:
        request: PreflightRequest containing array of Blob objects

    Returns:
        PreflightResponse with array of missing hashes

    Raises:
        HTTPException: 400 if validation fails, 500 if storage check fails
    """
    try:
        # Check which blobs are missing
        missing_hashes = []
        for blob in request.files:
            if not blob_exists(blob.hash):
                missing_hashes.append(blob.hash)

        return PreflightResponse(missing=missing_hashes)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage check failed: {str(e)}")
