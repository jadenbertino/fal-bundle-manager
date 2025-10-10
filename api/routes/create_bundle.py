"""Bundle creation API endpoint."""

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ulid import ULID
from shared.api_contracts.create_bundle import BundleManifestDraft, BundleCreateResponse
from api.storage import blob_exists
from shared.config import MANIFESTS_DIR, SUMMARIES_DIR
from shared.merkle import compute_merkle_root

router = APIRouter()


@router.post("/bundles")
async def create_bundle(request: BundleManifestDraft):
    """
    Create a bundle from already-uploaded blobs.

    This endpoint creates a bundle manifest that maps file paths to content hashes.
    All referenced blobs must already exist in storage.

    Args:
        request: BundleManifestDraft containing files array and merkle_root

    Returns:
        BundleCreateResponse with bundle ID and creation timestamp

    Raises:
        HTTPException:
            - 400: Invalid schema, duplicate paths
            - 409: Missing blobs, merkle root mismatch
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

        # Generate bundle metadata
        bundle_id = str(ULID())
        file_count = len(request.files)
        total_bytes = sum(file.size_bytes for file in request.files)
        computed_merkle_root = compute_merkle_root(request.files)
        
        # Validate that client-provided merkle root matches server-computed one
        if request.merkle_root != computed_merkle_root:
            raise HTTPException(
                status_code=409,
                detail=f"Merkle root mismatch: expected {computed_merkle_root}, got {request.merkle_root}"
            )
        merkle_root = computed_merkle_root
        created_at = datetime.utcnow().isoformat() + "Z"

        # Build summary (does NOT include files)
        summary = {
            "id": bundle_id,
            "created_at": created_at,
            "hash_algo": request.hash_algo,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "merkle_root": merkle_root,
        }

        # Build complete manifest (includes files)
        manifest = {
            **summary,
            "files": [file.model_dump() for file in request.files],
        }

        # Write manifest to storage
        MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = MANIFESTS_DIR / f"{bundle_id}.json"
        manifest_temp_path = manifest_path.with_suffix(".tmp")

        # Write summary to storage
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
        summary_path = SUMMARIES_DIR / f"{bundle_id}.json"
        summary_temp_path = summary_path.with_suffix(".tmp")
        
        try:
            # Write manifest
            manifest_temp_path.write_text(json.dumps(manifest, indent=2))
            manifest_temp_path.rename(manifest_path)

            # Write summary
            summary_temp_path.write_text(json.dumps(summary, indent=2))
            summary_temp_path.rename(summary_path)
        except Exception as e:
            # Clean up temp files on error
            if manifest_temp_path.exists():
                manifest_temp_path.unlink()
            if summary_temp_path.exists():
                summary_temp_path.unlink()
            # Also clean up successfully written manifest if summary failed
            if manifest_path.exists():
                manifest_path.unlink()
            raise

        return JSONResponse(
            status_code=201,
            content={
                "id": bundle_id,
                "created_at": created_at,
                "merkle_root": merkle_root
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
