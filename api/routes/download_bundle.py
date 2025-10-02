"""Download bundle API endpoint."""

import json
import zipfile
import io
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from shared.config import get_bundle_manifests_dir
from api.storage import get_blob_path

router = APIRouter()


@router.get("/bundles/{bundle_id}/download")
async def download_bundle(
    bundle_id: str,
    format: str = Query(default="zip", description="Archive format")
):
    """
    Download a bundle as a streaming archive file.

    Args:
        bundle_id: The bundle identifier
        format: Archive format (currently only "zip" supported)

    Returns:
        StreamingResponse with ZIP archive containing all bundle files

    Raises:
        HTTPException:
            - 404: Bundle not found
            - 415: Unsupported format requested
            - 500: Missing blobs or archive creation error
    """
    try:
        # Validate format
        if format != "zip":
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported format '{format}'. Only 'zip' is supported."
            )

        # Check if bundle manifest exists
        manifests_dir = get_bundle_manifests_dir()
        manifest_path = manifests_dir / f"{bundle_id}.json"

        if not manifest_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Bundle '{bundle_id}' not found"
            )

        # Load bundle manifest
        try:
            manifest_text = manifest_path.read_text()
            manifest = json.loads(manifest_text)
        except (json.JSONDecodeError, OSError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read bundle manifest: {str(e)}"
            )

        # Verify all blobs exist and collect paths
        files = manifest.get("files", [])
        blob_mappings = []  # [(blob_path, bundle_path), ...]

        for file_info in files:
            blob_hash = file_info["hash"]
            bundle_path = file_info["bundle_path"]
            blob_path = get_blob_path(blob_hash)

            if not blob_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail=f"Missing blob: {blob_hash}"
                )

            blob_mappings.append((blob_path, bundle_path))

        # Create ZIP archive in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for blob_path, bundle_path in blob_mappings:
                # Read blob content and add to ZIP with bundle path
                zf.write(blob_path, arcname=bundle_path)

        # Seek to beginning for streaming
        zip_buffer.seek(0)

        # Return streaming response
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="bundle_{bundle_id}.zip"'
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create archive: {str(e)}"
        )
