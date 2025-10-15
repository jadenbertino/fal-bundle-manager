"""
Tests for the CLI list command.

IMPORTANT: These tests make REAL API calls to http://localhost:8000
DO NOT USE MOCKS - We want true integration tests that verify the API server works correctly.
"""

import pytest
import time
from click.testing import CliRunner
from cli.commands.list import list_cmd, format_size, format_timestamp
from cli.tests.test_helpers import create_test_bundle, cleanup_all_bundles


@pytest.fixture
def runner():
    """Create a Click CLI runner."""
    return CliRunner()


def test_list_bundles_success(runner):
    """Test successful listing of bundles."""
    # Clean up and create test bundles
    cleanup_all_bundles()

    bundle1 = create_test_bundle([(b"test1" * 200, "file1.txt")])
    time.sleep(0.01)
    bundle2 = create_test_bundle([(b"test2" * 400, "file2.txt")])
    time.sleep(0.01)
    bundle3 = create_test_bundle([(b"test3" * 100, "file3.txt")])

    # Run command
    result = runner.invoke(list_cmd)

    # Assertions
    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Files" in result.output
    assert "Total Size" in result.output
    assert "Created" in result.output
    assert bundle1["id"] in result.output
    assert bundle2["id"] in result.output
    assert bundle3["id"] in result.output


def test_list_bundles_empty(runner):
    """Test listing when no bundles exist."""
    # Clean up all bundles
    cleanup_all_bundles()

    # Run command
    result = runner.invoke(list_cmd)

    # Assertions
    assert result.exit_code == 0
    assert "No bundles found" in result.output
    assert "create" in result.output.lower()


def test_list_bundles_network_error(runner):
    """Test handling of network connection error."""
    # Use an invalid API URL to trigger connection error
    result = runner.invoke(list_cmd, ['--api-url', 'http://localhost:9999'])

    # Assertions
    assert result.exit_code == 4
    assert "Failed to connect" in result.output


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


def test_list_bundles_formats_sizes_correctly(runner):
    """Test that sizes are formatted correctly in output."""
    # Clean up and create bundles with specific sizes
    cleanup_all_bundles()

    create_test_bundle([(b"a" * 1024, "1kb.txt")])  # 1 KB
    time.sleep(0.01)
    create_test_bundle([(b"b" * (2 * 1024 * 1024), "2mb.txt")])  # 2 MB

    # Run command
    result = runner.invoke(list_cmd)

    # Check size formatting
    assert "1.0 KB" in result.output
    assert "2.0 MB" in result.output


def test_list_bundles_formats_dates_correctly(runner):
    """Test that dates are formatted correctly in output."""
    # Clean up and create a test bundle
    cleanup_all_bundles()
    create_test_bundle([(b"test", "file.txt")])

    # Run command
    result = runner.invoke(list_cmd)

    # Check date formatting (should contain date in format YYYY-MM-DD HH:MM:SS)
    # We can't predict the exact date, but we can check the format
    import re
    # Look for pattern like "2024-01-15 10:30:00"
    date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    assert re.search(date_pattern, result.output), "Expected formatted date not found in output"
