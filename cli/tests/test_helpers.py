"""
Shared test helpers for CLI tests.

IMPORTANT: These tests make REAL API calls to http://localhost:8000
DO NOT USE MOCKS - We want true integration tests.
"""

import requests
from pathlib import Path
from cli.client import BundlesAPIClient
from shared.hash import hash_bytes
from shared.merkle import compute_merkle_root
from shared.types import Blob
from shared.config import SUMMARIES_DIR, MANIFESTS_DIR, BLOBS_DIR

BASE_URL = "http://localhost:8000"


def get_api_client() -> BundlesAPIClient:
    """Get a real API client instance."""
    return BundlesAPIClient(base_url=BASE_URL, timeout=30)


def cleanup_all_bundles():
    """Clean up all bundles from the test environment."""
    import shutil

    # Remove all summary files
    if SUMMARIES_DIR.exists():
        for bundle_file in SUMMARIES_DIR.glob("*.json"):
            try:
                bundle_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete {bundle_file}: {e}")

    # Remove all manifest files
    if MANIFESTS_DIR.exists():
        for bundle_file in MANIFESTS_DIR.glob("*.json"):
            try:
                bundle_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete {bundle_file}: {e}")

    # Remove all blobs
    if BLOBS_DIR.exists():
        try:
            shutil.rmtree(BLOBS_DIR)
            BLOBS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not clean blobs directory: {e}")


def create_test_bundle(files_data: list[tuple[bytes, str]]) -> dict:
    """
    Create a bundle for testing using real API calls.

    Args:
        files_data: List of (content, path) tuples

    Returns:
        The bundle creation response data
    """
    client = get_api_client()

    # Create blobs
    blobs = []
    for content, path in files_data:
        hash_val = hash_bytes(content)
        # Upload blob
        with open("/tmp/test_blob", "wb") as f:
            f.write(content)
        with open("/tmp/test_blob", "rb") as f:
            client.upload_blob(hash_val, len(content), f)

        blob = Blob(
            bundle_path=path,
            size_bytes=len(content),
            hash=hash_val,
            hash_algo="sha256"
        )
        blobs.append(blob)

    # Compute merkle root
    merkle_root = compute_merkle_root(blobs)

    # Create bundle
    from shared.api_contracts.create_bundle import CreateBundleRequest
    request = CreateBundleRequest(
        files=blobs,
        hash_algo="sha256",
        merkle_root=merkle_root
    )

    response = client.create_bundle(request)
    return {
        "id": response.id,
        "created_at": response.created_at,
        "merkle_root": response.merkle_root
    }
