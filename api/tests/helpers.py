"""Shared test helpers and utilities."""

import requests
from api.storage import calculate_sha256


BASE_URL = "http://localhost:8000"


def create_blob(content: bytes) -> str:
    """
    Helper: Create a blob and return its hash.

    Args:
        content: The file content as bytes

    Returns:
        The SHA-256 hash of the uploaded blob

    Raises:
        AssertionError: If the upload fails
    """
    hash_val = calculate_sha256(content)
    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code in [200, 201], f"Failed to create blob: {response.status_code}"
    return hash_val


def create_bundle(files_data: list[tuple[bytes, str]], bundle_id: str = None) -> dict:
    """
    Helper: Create a bundle and return the response data.

    Args:
        files_data: List of (content, path) tuples
        bundle_id: Optional client-provided bundle ID

    Returns:
        The bundle creation response JSON data

    Raises:
        AssertionError: If the bundle creation fails
    """
    files_payload = []
    for content, path in files_data:
        hash_val = create_blob(content)
        files_payload.append({
            "bundle_path": path,
            "size_bytes": len(content),
            "hash": hash_val,
            "hash_algo": "sha256"
        })

    payload = {"files": files_payload, "hash_algo": "sha256"}
    if bundle_id:
        payload["id"] = bundle_id

    response = requests.post(f"{BASE_URL}/bundles", json=payload)
    assert response.status_code == 201, f"Failed to create bundle: {response.status_code}"
    return response.json()
