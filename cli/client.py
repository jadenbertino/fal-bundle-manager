"""API client for communicating with the fal-bundles server."""

import requests
from typing import BinaryIO
from shared.api_contracts.preflight import PreflightRequest, PreflightResponse
from shared.api_contracts.create_bundle import BundleManifestDraft, BundleCreateResponse


class BundlesAPIClient:
    """Client for interacting with the fal-bundles API."""

    def __init__(self, base_url: str, timeout: int = 300):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API server (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds (default: 300)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def preflight(self, request: PreflightRequest) -> PreflightResponse:
        """
        Check which blobs need to be uploaded.

        Args:
            request: PreflightRequest with list of blobs

        Returns:
            PreflightResponse with list of missing hashes
        """
        url = f"{self.base_url}/bundles/preflight"
        response = self.session.post(
            url,
            json=request.model_dump(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return PreflightResponse(**response.json())

    def upload_blob(self, hash: str, size_bytes: int, file_obj: BinaryIO) -> bool:
        """
        Upload a blob to the server.

        Args:
            hash: SHA-256 hash of the blob
            size_bytes: Size of the blob in bytes
            file_obj: File-like object to read blob data from

        Returns:
            True if blob was newly created (201), False if it already existed (200)
        """
        url = f"{self.base_url}/blobs/{hash}"
        params = {"size_bytes": size_bytes}
        response = self.session.put(
            url,
            params=params,
            data=file_obj,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.status_code == 201

    def create_bundle(self, manifest: BundleManifestDraft) -> BundleCreateResponse:
        """
        Create a bundle from uploaded blobs.

        Args:
            manifest: BundleManifestDraft with list of files

        Returns:
            BundleCreateResponse with bundle id and created_at timestamp
        """
        url = f"{self.base_url}/bundles"
        response = self.session.post(
            url,
            json=manifest.model_dump(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return BundleCreateResponse(**response.json())
