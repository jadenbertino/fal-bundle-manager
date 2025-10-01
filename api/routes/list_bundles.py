"""List bundles API endpoint."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.api_contracts.list_bundles import BundleListResponse
from shared.types import BundleSummary
from shared.config import get_bundles_dir

router = APIRouter()


@router.get("/bundles")
async def list_bundles():
    """
    List all available bundles with metadata.

    Returns bundle summaries sorted by created_at descending (newest first).

    Returns:
        BundleListResponse with array of BundleSummary objects

    Raises:
        HTTPException:
            - 500: Storage read failure
    """
    try:
        bundles_dir = get_bundles_dir()
        bundles = []

        # Check if bundles directory exists
        if not bundles_dir.exists():
            return BundleListResponse(bundles=[])

        # Enumerate all .json files in bundles directory
        for manifest_path in bundles_dir.glob("*.json"):
            try:
                # Read manifest file
                manifest_text = manifest_path.read_text()
                manifest = json.loads(manifest_text)

                # Extract required fields for BundleSummary
                bundle_summary = BundleSummary(
                    id=manifest["id"],
                    created_at=manifest["created_at"],
                    hash_algo=manifest.get("hash_algo", "sha256"),
                    file_count=manifest.get("file_count", 0),
                    total_bytes=manifest.get("total_bytes", 0)
                )
                bundles.append(bundle_summary)

            except (json.JSONDecodeError, KeyError) as e:
                # Log and skip corrupted/invalid manifests
                # In production, use proper logging
                print(f"Warning: Skipping invalid manifest {manifest_path}: {e}")
                continue

        # Sort by created_at descending (newest first)
        bundles.sort(key=lambda b: b.created_at, reverse=True)

        return BundleListResponse(bundles=bundles)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
