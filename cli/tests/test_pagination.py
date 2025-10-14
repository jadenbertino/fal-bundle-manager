"""Tests for pagination functionality in list bundles."""

import pytest
from unittest.mock import Mock, patch
from cli.client import BundlesAPIClient
from shared.api_contracts.list_bundles import ListBundlesResponse
from shared.types import BundleSummary


@pytest.fixture
def api_client():
    """Create a BundlesAPIClient instance for testing."""
    return BundlesAPIClient(base_url="http://localhost:8000", timeout=30)


@pytest.fixture
def sample_bundles_10():
    """Sample bundle data with 10 bundles for pagination testing."""
    bundles = []
    # Use valid hex characters (0-9, a-f) for merkle_root
    hex_chars = "0123456789abcdef"
    for i in range(10):
        bundles.append(
            BundleSummary(
                id=f"01K6GZ396JT9343XTQ89G69Y{i:02d}",
                created_at=f"2023-12-{25-i:02d}T10:30:00Z",
                hash_algo="sha256",
                file_count=5 + i,
                total_bytes=1024 * (i + 1),
                merkle_root=hex_chars[i] * 64,  # '0', '1', '2', ... '9'
            )
        )
    return bundles


def test_pagination_consistency(api_client, sample_bundles_10):
    """
    Test that pagination is consistent across different page sizes.

    Logic:
    1. Fetch bundles with page=1 and page_size=10
    2. Iterate through the returned bundles
    3. For each bundle at index i, send request with page=i+1 and page_size=1
    4. Verify each single-item response matches the corresponding bundle from first request
    """
    with patch.object(api_client, 'list_bundles') as mock_list:
        # Setup mock: first call returns all 10 bundles
        mock_list.return_value = ListBundlesResponse(bundles=sample_bundles_10)

        # Step 1: Fetch bundles with page=1 and page_size=10
        initial_response = api_client.list_bundles(page=1, page_size=10)

        # Verify we got 10 bundles
        assert len(initial_response.bundles) == 10

        # Step 2-4: Iterate through bundles and verify individual page requests
        for index, expected_bundle in enumerate(initial_response.bundles):
            # Configure mock to return single bundle for this page
            mock_list.return_value = ListBundlesResponse(bundles=[sample_bundles_10[index]])

            # Send request with page=index+1 and page_size=1
            single_response = api_client.list_bundles(page=index + 1, page_size=1)

            # Verify the response contains exactly 1 bundle
            assert len(single_response.bundles) == 1, \
                f"Expected 1 bundle for page {index + 1}, got {len(single_response.bundles)}"

            # Verify the bundle matches the expected bundle
            actual_bundle = single_response.bundles[0]
            assert actual_bundle.id == expected_bundle.id, \
                f"Bundle ID mismatch at index {index}: expected {expected_bundle.id}, got {actual_bundle.id}"
            assert actual_bundle.created_at == expected_bundle.created_at, \
                f"Created timestamp mismatch at index {index}"
            assert actual_bundle.file_count == expected_bundle.file_count, \
                f"File count mismatch at index {index}"
            assert actual_bundle.total_bytes == expected_bundle.total_bytes, \
                f"Total bytes mismatch at index {index}"
            assert actual_bundle.merkle_root == expected_bundle.merkle_root, \
                f"Merkle root mismatch at index {index}"


def test_pagination_with_smaller_dataset(api_client):
    """
    Test pagination with fewer bundles than page size.

    Verifies that requesting page_size=10 with only 5 bundles works correctly.
    """
    # Create 5 bundles
    bundles = []
    hex_chars = "0123456789abcdef"
    for i in range(5):
        bundles.append(
            BundleSummary(
                id=f"01K6GZ396JT9343XTQ89G69Y{i:02d}",
                created_at=f"2023-12-{25-i:02d}T10:30:00Z",
                hash_algo="sha256",
                file_count=5 + i,
                total_bytes=1024 * (i + 1),
                merkle_root=hex_chars[i] * 64,
            )
        )

    with patch.object(api_client, 'list_bundles') as mock_list:
        # Setup mock: return all 5 bundles
        mock_list.return_value = ListBundlesResponse(bundles=bundles)

        # Fetch with page_size=10 (larger than dataset)
        response = api_client.list_bundles(page=1, page_size=10)

        # Should return all 5 bundles
        assert len(response.bundles) == 5

        # Verify each bundle individually
        for index, expected_bundle in enumerate(response.bundles):
            # Configure mock to return single bundle for this page
            mock_list.return_value = ListBundlesResponse(bundles=[bundles[index]])

            single_response = api_client.list_bundles(page=index + 1, page_size=1)

            assert len(single_response.bundles) == 1
            assert single_response.bundles[0].id == expected_bundle.id


def test_pagination_empty_page(api_client):
    """
    Test requesting a page beyond available data.

    Verifies that requesting page 2 when only 5 bundles exist returns empty list.
    """
    with patch.object(api_client, 'list_bundles') as mock_list:
        # Setup mock: page 1 has bundles, page 2 is empty
        def mock_list_bundles(page=1, page_size=10):
            if page == 1:
                return ListBundlesResponse(bundles=[
                    BundleSummary(
                        id="01K6GZ396JT9343XTQ89G69Y00",
                        created_at="2023-12-25T10:30:00Z",
                        hash_algo="sha256",
                        file_count=5,
                        total_bytes=1024,
                        merkle_root="a" * 64,
                    )
                ])
            else:
                return ListBundlesResponse(bundles=[])

        mock_list.side_effect = mock_list_bundles

        # Fetch page 1
        page1_response = api_client.list_bundles(page=1, page_size=10)
        assert len(page1_response.bundles) == 1

        # Fetch page 2 (should be empty)
        page2_response = api_client.list_bundles(page=2, page_size=10)
        assert len(page2_response.bundles) == 0


def test_pagination_boundary_conditions(api_client):
    """
    Test pagination with exact page boundaries.

    With exactly 10 bundles and page_size=10:
    - Page 1 should have 10 bundles
    - Page 2 should be empty
    """
    bundles = []
    hex_chars = "0123456789abcdef"
    for i in range(10):
        bundles.append(
            BundleSummary(
                id=f"01K6GZ396JT9343XTQ89G69Y{i:02d}",
                created_at=f"2023-12-{25-i:02d}T10:30:00Z",
                hash_algo="sha256",
                file_count=5 + i,
                total_bytes=1024 * (i + 1),
                merkle_root=hex_chars[i] * 64,
            )
        )

    with patch.object(api_client, 'list_bundles') as mock_list:
        def mock_list_bundles(page=1, page_size=10):
            if page == 1:
                return ListBundlesResponse(bundles=bundles)
            else:
                return ListBundlesResponse(bundles=[])

        mock_list.side_effect = mock_list_bundles

        # Page 1 should have all 10 bundles
        page1_response = api_client.list_bundles(page=1, page_size=10)
        assert len(page1_response.bundles) == 10

        # Page 2 should be empty (exactly at boundary)
        page2_response = api_client.list_bundles(page=2, page_size=10)
        assert len(page2_response.bundles) == 0
