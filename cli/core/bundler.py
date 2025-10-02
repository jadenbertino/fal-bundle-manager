"""Bundle creation orchestration."""

from pathlib import Path
from typing import Optional
from shared.types import Blob
from shared.api_contracts.preflight import PreflightRequest
from shared.api_contracts.create_bundle import BundleManifestDraft, BundleCreateResponse
from cli.core.file_discovery import discover_files
from cli.core.hashing import hash_file_sha256


def create_bundle(
    input_paths: list[str],
    api_client,  # BundlesAPIClient - avoiding circular import
    bundle_id: Optional[str] = None,
    base_dir: Optional[str] = None
) -> BundleCreateResponse:
    """
    Create a bundle from local files.

    This function orchestrates the full workflow:
    1. Discover files from input paths
    2. Hash all files
    3. Preflight check to find missing blobs
    4. Upload missing blobs
    5. Create bundle manifest

    Args:
        input_paths: List of file or directory paths
        api_client: BundlesAPIClient instance
        bundle_id: Optional client-provided bundle ID
        base_dir: Optional base directory for relative paths

    Returns:
        BundleCreateResponse with bundle id and timestamp

    Raises:
        FileNotFoundError: If input paths don't exist
        ValueError: If no files discovered or validation errors
        requests.HTTPError: If API requests fail
    """
    # Step 1: Discover files
    discovered_files = discover_files(input_paths, base_dir)

    # Step 2: Hash all files and create Blob objects
    blobs: list[Blob] = []
    for file in discovered_files:
        file_hash = hash_file_sha256(file.absolute_path)
        blob = Blob(
            bundle_path=file.relative_path,
            size_bytes=file.size_bytes,
            hash=file_hash,
            hash_algo="sha256"
        )
        blobs.append(blob)

    # Step 3: Preflight check
    preflight_request = PreflightRequest(files=blobs)
    preflight_response = api_client.preflight(preflight_request)
    missing_hashes = set(preflight_response.missing)

    # Step 4: Upload missing blobs
    for blob in blobs:
        if blob.hash in missing_hashes:
            # Find the corresponding file
            file = next(f for f in discovered_files if f.relative_path == blob.bundle_path)
            with open(file.absolute_path, 'rb') as f:
                api_client.upload_blob(blob.hash, blob.size_bytes, f)

    # Step 5: Create bundle
    manifest = BundleManifestDraft(
        id=bundle_id,
        files=blobs,
        hash_algo="sha256"
    )
    return api_client.create_bundle(manifest)
