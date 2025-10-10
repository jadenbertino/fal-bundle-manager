"""API client for communicating with the fal-bundles server."""

import requests
from typing import BinaryIO, Iterator
from shared.api_contracts.preflight import PreflightRequest, PreflightResponse
from shared.api_contracts.create_bundle import CreateBundleRequest, CreateBundleResponse
from shared.api_contracts.list_bundles import ListBundlesResponse
from shared.api_contracts.download_bundle import DownloadBundleRequest


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

    def create_bundle(self, manifest: CreateBundleRequest) -> CreateBundleResponse:
        """
        Create a bundle from uploaded blobs.

        Args:
            manifest: CreateBundleRequest with list of files

        Returns:
            CreateBundleResponse with bundle id and created_at timestamp
        """
        url = f"{self.base_url}/bundles"
        response = self.session.post(
            url,
            json=manifest.model_dump(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return CreateBundleResponse(**response.json())

    def list_bundles(self) -> ListBundlesResponse:
        """
        List all available bundles.

        Returns:
            ListBundlesResponse with list of bundle summaries
        """
        url = f"{self.base_url}/bundles"
        response = self.session.get(
            url,
            timeout=self.timeout
        )
        response.raise_for_status()
        return ListBundlesResponse(**response.json())

    def download_bundle(self, bundle_id: str, format: str = "zip") -> Iterator[bytes]:
        """
        Download a bundle as a streaming archive.

        Args:
            bundle_id: ID of the bundle to download
            format: Archive format (default: "zip")

        Returns:
            Iterator of bytes chunks for streaming the download

        Raises:
            requests.exceptions.HTTPError: If bundle not found (404) or other HTTP errors
            requests.exceptions.RequestException: For network/connection errors
        """
        url = f"{self.base_url}/bundles/{bundle_id}/download"
        params = DownloadBundleRequest(format=format).model_dump()

        response = self.session.get(
            url,
            params=params,
            stream=True,
            timeout=self.timeout
        )
        response.raise_for_status()

        # Stream the response in chunks
        return response.iter_content(chunk_size=8192)
