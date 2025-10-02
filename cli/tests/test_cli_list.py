"""Tests for the CLI list command."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from cli.commands.list import list_cmd, format_size, format_timestamp
from shared.api_contracts.list_bundles import BundleListResponse
from shared.types import BundleSummary
import requests


@pytest.fixture
def runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_bundles():
    """Sample bundle data for testing."""
    return BundleListResponse(
        bundles=[
            BundleSummary(
                id="01K6GZ396JT9343XTQ89G69Y3W",
                created_at="2023-12-25T10:30:00Z",
                hash_algo="sha256",
                file_count=5,
                total_bytes=1024,
                merkle_root="a" * 64,
            ),
            BundleSummary(
                id="01K6GZ3GMJYRAJZ60JD178HT6T",
                created_at="2023-12-24T15:20:00Z",
                hash_algo="sha256",
                file_count=3,
                total_bytes=2048000,
                merkle_root="b" * 64,
            ),
            BundleSummary(
                id="01K6GZ3Q2CSWDDC52XK6ZQN15F",
                created_at="2023-12-23T08:45:00Z",
                hash_algo="sha256",
                file_count=10,
                total_bytes=500000000,
                merkle_root="c" * 64,
            ),
        ]
    )


def test_list_bundles_success(runner, sample_bundles):
    """Test successful listing of bundles."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.list_bundles.return_value = sample_bundles
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Assertions
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Files" in result.output
        assert "Total Size" in result.output
        assert "Created" in result.output
        assert "Merkle Root" in result.output
        assert "01K6GZ396JT9343XTQ89G69Y3W" in result.output
        assert "01K6GZ3GMJYRAJZ60JD178HT6T" in result.output
        assert "01K6GZ3Q2CSWDDC52XK6ZQN15F" in result.output
        assert "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in result.output
        assert "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" in result.output
        assert "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc" in result.output


def test_list_bundles_empty(runner):
    """Test listing when no bundles exist."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.list_bundles.return_value = BundleListResponse(bundles=[])
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Assertions
        assert result.exit_code == 0
        assert "No bundles found" in result.output
        assert "create" in result.output.lower()


def test_list_bundles_network_error(runner):
    """Test handling of network connection error."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock to raise ConnectionError
        mock_instance = Mock()
        mock_instance.list_bundles.side_effect = requests.exceptions.ConnectionError()
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Assertions
        assert result.exit_code == 4
        assert "Failed to connect" in result.output


def test_list_bundles_timeout_error(runner):
    """Test handling of request timeout."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock to raise Timeout
        mock_instance = Mock()
        mock_instance.list_bundles.side_effect = requests.exceptions.Timeout()
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Assertions
        assert result.exit_code == 4
        assert "timed out" in result.output


def test_format_size_bytes():
    """Test formatting of byte sizes (< 1KB)."""
    assert format_size(0) == "0 B"
    assert format_size(1) == "1 B"
    assert format_size(100) == "100 B"
    assert format_size(1023) == "1,023 B"


def test_format_size_kilobytes():
    """Test formatting of kilobyte sizes."""
    assert format_size(1024) == "1.0 KB"
    assert format_size(1536) == "1.5 KB"
    assert format_size(12345) == "12.1 KB"
    assert format_size(1024 * 1024 - 1) == "1024.0 KB"


def test_format_size_megabytes():
    """Test formatting of megabyte sizes."""
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(2048 * 1024) == "2.0 MB"
    assert format_size(45 * 1024 * 1024 + 600 * 1024) == "45.6 MB"


def test_format_size_gigabytes():
    """Test formatting of gigabyte sizes."""
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_size(7 * 1024 * 1024 * 1024 + 800 * 1024 * 1024) == "7.8 GB"


def test_format_timestamp():
    """Test formatting of ISO timestamps."""
    assert format_timestamp("2023-12-25T10:30:00Z") == "2023-12-25 10:30:00"
    assert format_timestamp("2024-01-01T00:00:00Z") == "2024-01-01 00:00:00"
    assert format_timestamp("2023-06-15T15:45:30Z") == "2023-06-15 15:45:30"


def test_list_bundles_formats_sizes_correctly(runner, sample_bundles):
    """Test that sizes are formatted correctly in output."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.list_bundles.return_value = sample_bundles
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Check size formatting
        assert "1.0 KB" in result.output  # 1024 bytes
        assert "2.0 MB" in result.output  # 2048000 bytes
        assert "476.8 MB" in result.output  # 500000000 bytes


def test_list_bundles_formats_dates_correctly(runner, sample_bundles):
    """Test that dates are formatted correctly in output."""
    with patch('cli.commands.list.BundlesAPIClient') as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.list_bundles.return_value = sample_bundles
        mock_client.return_value = mock_instance

        # Run command
        result = runner.invoke(list_cmd)

        # Check date formatting (spaces instead of T and Z)
        assert "2023-12-25 10:30:00" in result.output
        assert "2023-12-24 15:20:00" in result.output
        assert "2023-12-23 08:45:00" in result.output
