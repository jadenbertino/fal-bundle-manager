"""List bundles API endpoint."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.api_contracts.list_bundles import BundleListResponse
from shared.types import BundleSummary, Blob
from shared.config import get_bundle_summaries_dir, get_bundle_manifests_dir
from shared.merkle import compute_merkle_root
from shared.config import PAGE_SIZE

router = APIRouter()


@router.get("/bundles")
async def list_bundles(page: int = 1, page_size: int = PAGE_SIZE):
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
        print(f"Page: {page}, Page Size: {page_size}")

        # Enumerate all .json files in summaries directory
        all_summaries = list(summaries_dir.glob("*.json"))
        
        # Process all summaries first to get complete data for sorting
        all_bundles = []
        for summary_path in all_summaries:
            try:
                # Read summary file
                summary_text = summary_path.read_text()
                summary = json.loads(summary_text)

                # Extract required fields for BundleSummary
                merkle_root = summary.get("merkle_root")
                if not merkle_root:
                    try:
                        manifests_dir = get_bundle_manifests_dir()
                        manifest_path = manifests_dir / f"{summary['id']}.json"
                        manifest = json.loads(manifest_path.read_text())
                        merkle_root = manifest.get("merkle_root")
                        if not merkle_root:
                            files = [Blob(**file_dict) for file_dict in manifest.get("files", [])]
                            merkle_root = compute_merkle_root(files)
                    except Exception as manifest_error:
                        print(
                            f"Warning: Unable to determine merkle root for {summary_path}: {manifest_error}"
                        )
                        continue

                bundle_summary = BundleSummary(
                    id=summary["id"],
                    created_at=summary["created_at"],
                    hash_algo=summary.get("hash_algo", "sha256"),
                    file_count=summary.get("file_count", 0),
                    total_bytes=summary.get("total_bytes", 0),
                    merkle_root=merkle_root,
                )
                all_bundles.append(bundle_summary)

            except (json.JSONDecodeError, KeyError) as e:
                # Log and skip corrupted/invalid summaries
                # In production, use proper logging
                print(f"Warning: Skipping invalid summary {summary_path}: {e}")
                continue

        # Sort by created_at descending (newest first)
        all_bundles.sort(key=lambda b: b.created_at, reverse=True)
        
        # Calculate pagination bounds
        start_idx = page_size * (page - 1)
        end_idx = start_idx + page_size
        
        # Check if start index is out of bounds
        if start_idx >= len(all_bundles):
            return BundleListResponse(bundles=[])
        
        # Get the subset of bundles for this page using slicing
        bundles = all_bundles[start_idx:end_idx]

        return BundleListResponse(bundles=bundles)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
