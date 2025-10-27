"""List bundles API endpoint."""

import json

from fastapi import APIRouter, HTTPException

from shared.api_contracts.list_bundles import BundleListResponse
from shared.config import get_bundle_manifests_dir, get_bundle_summaries_dir
from shared.logs import get_logger
from shared.merkle import compute_merkle_root
from shared.types import Blob, BundleSummary

logger = get_logger(__name__)

router = APIRouter()


@router.get("/bundles")
async def list_bundles():
    """
    List all available bundles with metadata.

    Returns bundle summaries sorted by created_at descending (newest first).
    Reads from summaries directory (which does NOT include files list).

    Returns:
        BundleListResponse with array of BundleSummary objects

    Raises:
        HTTPException:
            - 500: Storage read failure
    """
    try:
        summaries_dir = get_bundle_summaries_dir()

        # Check if summaries directory exists
        if not summaries_dir.exists():
            return BundleListResponse(bundles=[])

        # Enumerate all .json files in summaries directory
        bundles = []
        for summary_path in summaries_dir.glob("*.json"):
            try:
                # Read summary file
                summary = json.loads(summary_path.read_text())

                # Backfill merkle root
                merkle_root = summary.get("merkle_root")
                if not merkle_root:
                    try:
                        manifests_dir = get_bundle_manifests_dir()
                        manifest_path = manifests_dir / f"{summary['id']}.json"
                        manifest = json.loads(manifest_path.read_text())
                        merkle_root = manifest.get("merkle_root")
                        if not merkle_root:
                            files = [
                                Blob(**file_dict)
                                for file_dict in manifest.get("files", [])
                            ]
                            merkle_root = compute_merkle_root(files)
                    except Exception as manifest_error:
                        logger.warning(
                            f"Unable to determine merkle root for {summary_path}: {manifest_error}"
                        )
                        continue

                # Append bundle
                bundle_summary = BundleSummary(
                    id=summary["id"],
                    created_at=summary["created_at"],
                    hash_algo=summary.get("hash_algo", "sha256"),
                    file_count=summary.get("file_count", 0),
                    total_bytes=summary.get("total_bytes", 0),
                    merkle_root=merkle_root,
                )
                bundles.append(bundle_summary)

            except (json.JSONDecodeError, KeyError) as e:
                # Log and skip corrupted/invalid summaries
                logger.warning(f"Skipping invalid summary {summary_path}: {e}")
                continue

        # Sort by created_at descending (newest first)
        bundles.sort(key=lambda b: b.created_at, reverse=True)

        return BundleListResponse(bundles=bundles)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}") from e
