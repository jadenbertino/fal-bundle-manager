"""Bundle creation orchestration."""

import asyncio

import aiohttp

from cli.core.file_discovery import discover_files
from cli.core.hashing import hash_file_sha256
from shared.api_contracts.create_bundle import BundleCreateResponse, BundleManifestDraft
from shared.api_contracts.preflight import PreflightRequest
from shared.merkle import compute_merkle_root
from shared.types import Blob


def create_bundle(
    input_paths: list[str],
    api_client,  # BundlesAPIClient - avoiding circular import
    base_dir: str | None = None,
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
            hash_algo="sha256",
        )
        blobs.append(blob)

    # Step 3: Get list of blobs that haven't been uploaded
    preflight_request = PreflightRequest(files=blobs)
    preflight_response = api_client.preflight(preflight_request)
    missing_hashes = set(preflight_response.missing)

    # Step 4: Upload missing blobs concurrently
    if missing_hashes:
        asyncio.run(
            _upload_blobs_async(api_client, blobs, discovered_files, missing_hashes)
        )
    
    # Step 5: Compute merkle root
    computed_merkle_root = compute_merkle_root(blobs)

    # Step 6: Create bundle
    manifest = BundleManifestDraft(
        files=blobs, hash_algo="sha256", merkle_root=computed_merkle_root
    )

    # Step 7: Send request and validate response
    response = api_client.create_bundle(manifest)

    # Validate that server-returned merkle root matches our computed one
    if response.merkle_root != computed_merkle_root:
        raise ValueError(
            f"Merkle root mismatch: expected {computed_merkle_root}, got {response.merkle_root}"
        )

    return response


async def _upload_blobs_async(api_client, blobs, discovered_files, missing_hashes):
    """
    Upload multiple blobs concurrently using asyncio and aiohttp.

    Args:
        api_client: BundlesAPIClient instance
        blobs: List of Blob objects
        discovered_files: List of discovered files
        missing_hashes: Set of blob hashes that need to be uploaded
    """
    # Create a single shared session for all uploads
    async with aiohttp.ClientSession() as session:
        # Create upload tasks for all missing blobs
        tasks = []
        for blob in blobs:
            if blob.hash in missing_hashes:
                # Find the corresponding file
                file = next(
                    f for f in discovered_files if f.relative_path == blob.bundle_path
                )
                task = _upload_blob_async(
                    session,
                    api_client.base_url,
                    blob.hash,
                    blob.size_bytes,
                    file.absolute_path,
                    api_client.timeout,
                )
                tasks.append(task)

        # Execute all uploads concurrently
        await asyncio.gather(*tasks)


async def _upload_blob_async(
    session: aiohttp.ClientSession,
    base_url: str,
    blob_hash: str,
    size_bytes: int,
    file_path: str,
    timeout: int,
) -> bool:
    """
    Upload a single blob asynchronously.

    Args:
        session: aiohttp ClientSession
        base_url: Base URL of the API server
        blob_hash: SHA-256 hash of the blob
        size_bytes: Size of the blob in bytes
        file_path: Path to the file to upload
        timeout: Request timeout in seconds

    Returns:
        True if blob was newly created (201), False if it already existed (200)
    """
    url = f"{base_url}/blobs/{blob_hash}"
    params = {"size_bytes": size_bytes}

    with open(file_path, "rb") as f:
        # Convert timeout to proper type (handle Mock objects in tests)
        timeout_value = timeout if isinstance(timeout, (int, float)) else 300
        async with session.put(
            url,
            params=params,
            data=f,
            timeout=aiohttp.ClientTimeout(total=timeout_value),
        ) as response:
            response.raise_for_status()
            return response.status == 201

