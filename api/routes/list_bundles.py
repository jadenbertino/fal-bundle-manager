"""List bundles API endpoint."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.api_contracts.list_bundles import BundleListResponse
from shared.types import BundleSummary
from shared.config import get_bundle_summaries_dir

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
        bundles = []

        # Check if summaries directory exists
        if not summaries_dir.exists():
            return BundleListResponse(bundles=[])

        # Enumerate all .json files in summaries directory
        for summary_path in summaries_dir.glob("*.json"):
            try:
                # Read summary file
                summary_text = summary_path.read_text()
                summary = json.loads(summary_text)

                # Extract required fields for BundleSummary
                bundle_summary = BundleSummary(
                    id=summary["id"],
                    created_at=summary["created_at"],
                    hash_algo=summary.get("hash_algo", "sha256"),
                    file_count=summary.get("file_count", 0),
                    total_bytes=summary.get("total_bytes", 0)
                )
                bundles.append(bundle_summary)

            except (json.JSONDecodeError, KeyError) as e:
                # Log and skip corrupted/invalid summaries
                # In production, use proper logging
                print(f"Warning: Skipping invalid summary {summary_path}: {e}")
                continue

        # Sort by created_at descending (newest first)
        bundles.sort(key=lambda b: b.created_at, reverse=True)

        return BundleListResponse(bundles=bundles)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
