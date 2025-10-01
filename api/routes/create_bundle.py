"""Bundle creation API endpoint."""

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ulid import ULID
from shared.api_contracts.create_bundle import BundleManifestDraft, BundleCreateResponse
from api.storage import blob_exists
from api.config import get_bundles_dir

router = APIRouter()


@router.post("/bundles")
async def create_bundle(request: BundleManifestDraft):
    """
    Create a bundle from already-uploaded blobs.

    This endpoint creates a bundle manifest that maps file paths to content hashes.
    All referenced blobs must already exist in storage.

    Args:
        request: BundleManifestDraft containing files array and optional ID

    Returns:
        BundleCreateResponse with bundle ID and creation timestamp

    Raises:
        HTTPException:
            - 400: Invalid schema, duplicate paths
            - 409: Missing blobs, duplicate bundle ID
            - 500: Storage write failure
    """
    try:
        # Verify all referenced blobs exist
        missing_hashes = []
        for file in request.files:
            if not blob_exists(file.hash):
                missing_hashes.append(file.hash)
        if missing_hashes:
            raise HTTPException(
                status_code=409,
                detail=f"Missing blobs: {', '.join(missing_hashes)}"
            )

        # Generate or validate bundle ID
        if request.id:
            bundle_id = request.id
            # Check for ID collision
            bundles_dir = get_bundles_dir()
            manifest_path = bundles_dir / f"{bundle_id}.json"
            if manifest_path.exists():
                raise HTTPException(
                    status_code=409,
                    detail=f"Bundle ID '{bundle_id}' already exists"
                )
        else:
            # Generate ULID for time-ordered unique ID
            bundle_id = str(ULID())

        # Calculate statistics
        file_count = len(request.files)
        total_bytes = sum(file.size_bytes for file in request.files)

        # Create timestamp
        created_at = datetime.utcnow().isoformat() + "Z"

        # Build complete manifest
        manifest = {
            "id": bundle_id,
            "created_at": created_at,
            "hash_algo": request.hash_algo,
            "files": [file.model_dump() for file in request.files],
            "file_count": file_count,
            "bytes": total_bytes
        }

        # Write manifest to storage
        bundles_dir = get_bundles_dir()
        bundles_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = bundles_dir / f"{bundle_id}.json"

        # Atomic write: write to temp file, then rename
        temp_path = manifest_path.with_suffix(".tmp")
        try:
            temp_path.write_text(json.dumps(manifest, indent=2))
            temp_path.rename(manifest_path)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

        return JSONResponse(
            status_code=201,
            content={
                "id": bundle_id,
                "created_at": created_at
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
