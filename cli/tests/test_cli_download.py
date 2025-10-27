"""Tests for the CLI download command."""

import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from click.testing import CliRunner
from cli.commands.download import (
    download,
    generate_filename,
    get_file_extension,
    handle_file_conflict,
    download_with_progress,
    validate_format,
)
import requests


@pytest.fixture
def runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_chunks():
    """Mock streaming chunks of data."""
    return [b"chunk1", b"chunk2", b"chunk3"]


# Test utility functions


def test_get_file_extension():
    """Test file extension mapping."""
    assert get_file_extension("zip") == "zip"


def test_generate_filename():
    """Test filename generation."""
    assert generate_filename("01HQZX123ABC", "zip") == "bundle_01HQZX123ABC.zip"


def test_handle_file_conflict_no_conflict(tmp_path):
    """Test file conflict handling when no conflict exists."""
    filepath = tmp_path / "bundle_test.zip"
    result = handle_file_conflict(filepath)
    assert result == filepath


def test_handle_file_conflict_with_existing_file(tmp_path):
    """Test file conflict handling with existing file."""
    filepath = tmp_path / "bundle_test.zip"
    filepath.touch()  # Create the file

    result = handle_file_conflict(filepath)
    assert result == tmp_path / "bundle_test.1.zip"


def test_handle_file_conflict_multiple_conflicts(tmp_path):
    """Test file conflict handling with multiple existing files."""
    filepath = tmp_path / "bundle_test.zip"
    filepath.touch()
    (tmp_path / "bundle_test.1.zip").touch()
    (tmp_path / "bundle_test.2.zip").touch()

    result = handle_file_conflict(filepath)
    assert result == tmp_path / "bundle_test.3.zip"


def test_validate_format_valid():
    """Test format validation with valid format."""
    validate_format("zip")  # Should not raise


def test_validate_format_invalid():
    """Test format validation with invalid format."""
    with pytest.raises(ValueError, match="Unsupported format: tar.bz2"):
        validate_format("tar.bz2")


def test_download_with_progress_success(tmp_path):
    """Test downloading with progress indication."""
    output_path = tmp_path / "test.zip"
    chunks = [b"hello", b"world", b"test"]

    total_bytes = download_with_progress(chunks, output_path, show_progress=False)

    assert total_bytes == 14  # len("hello") + len("world") + len("test")
    assert output_path.exists()
    assert output_path.read_bytes() == b"helloworldtest"


def test_download_with_progress_io_error(tmp_path):
    """Test handling of IO error during download."""
    # Create a read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)

    output_path = readonly_dir / "test.zip"
    chunks = [b"test"]

    try:
        with pytest.raises(IOError):
            download_with_progress(chunks, output_path, show_progress=False)
    finally:
        # Restore permissions to allow cleanup
        readonly_dir.chmod(0o755)

        # Verify cleanup happened (file should not exist)
        # Note: we can't check exists() when dir was readonly, but after restoring
        # permissions we can verify the file was never created or was cleaned up
        if output_path.exists():
            pytest.fail("Partial download file was not cleaned up")


def test_download_with_progress_filters_empty_chunks(tmp_path):
    """Test that empty chunks are filtered out."""
    output_path = tmp_path / "test.zip"
    chunks = [b"hello", b"", b"world", None, b"test"]

    total_bytes = download_with_progress(chunks, output_path, show_progress=False)

    assert output_path.read_bytes() == b"helloworldtest"


# Test download command scenarios (from Gherkin)


def test_download_bundle_success_default_format(runner):
    """
    Scenario: Successfully download bundle with default format
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.download_bundle.return_value = iter([b"test", b"data"])
        mock_client.return_value = mock_instance

        # Run command in isolated filesystem
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 0
            assert "Downloaded bundle_01HQZX123ABC.zip" in result.output
            assert Path("bundle_01HQZX123ABC.zip").exists()

            # Verify API was called correctly
            mock_instance.download_bundle.assert_called_once_with("01HQZX123ABC", "zip")


def test_download_bundle_success_explicit_format(runner):
    """
    Scenario: Successfully download bundle with explicit format
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.download_bundle.return_value = iter([b"test", b"data"])
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX456DEF", "--format", "zip"])

            # Assertions
            assert result.exit_code == 0
            assert Path("bundle_01HQZX456DEF.zip").exists()
            mock_instance.download_bundle.assert_called_once_with("01HQZX456DEF", "zip")


def test_download_bundle_not_found(runner):
    """
    Scenario: Download bundle not found
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock to raise 404 HTTPError
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        error = requests.exceptions.HTTPError(response=mock_response)
        mock_instance.download_bundle.side_effect = error
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX999XXX"])

            # Assertions
            assert result.exit_code == 2
            assert "Bundle 01HQZX999XXX not found" in result.output
            assert not Path("bundle_01HQZX999XXX.zip").exists()


def test_download_unsupported_format(runner):
    """
    Scenario: Unsupported archive format
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC", "--format", "tar.bz2"])

            # Assertions
            assert result.exit_code == 1
            assert "Unsupported format: tar.bz2" in result.output
            assert not Path("bundle_01HQZX123ABC.tar.bz2").exists()

            # Verify API was never called
            mock_client.return_value.download_bundle.assert_not_called()


def test_download_network_connection_failure(runner):
    """
    Scenario: Network connection failure during download
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock to raise ConnectionError
        mock_instance = Mock()
        mock_instance.download_bundle.side_effect = (
            requests.exceptions.ConnectionError()
        )
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 4
            assert "Failed to connect" in result.output
            assert not Path("bundle_01HQZX123ABC.zip").exists()


def test_download_server_unavailable(runner):
    """
    Scenario: Server unavailable
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.download_bundle.side_effect = (
            requests.exceptions.ConnectionError()
        )
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 4
            assert "Failed to connect" in result.output


def test_download_timeout_error(runner):
    """
    Scenario: Request timeout during download
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock to raise Timeout
        mock_instance = Mock()
        mock_instance.download_bundle.side_effect = requests.exceptions.Timeout()
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 4
            assert "timed out" in result.output


def test_download_file_already_exists(runner):
    """
    Scenario: File already exists in target location
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock
        mock_instance = Mock()
        mock_instance.download_bundle.return_value = iter([b"new", b"data"])
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            # Create existing file
            Path("bundle_01HQZX123ABC.zip").write_bytes(b"old data")

            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 0
            assert "exists, saving as bundle_01HQZX123ABC.1.zip" in result.output
            assert Path("bundle_01HQZX123ABC.1.zip").exists()
            assert Path("bundle_01HQZX123ABC.1.zip").read_bytes() == b"newdata"


def test_download_interrupted_cleanup(runner, tmp_path):
    """
    Scenario: Download interrupted mid-transfer

    Tests that temporary files are cleaned up when download fails.
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock to fail during iteration
        def failing_chunks():
            yield b"chunk1"
            raise requests.exceptions.RequestException("Connection lost")

        mock_instance = Mock()
        mock_instance.download_bundle.return_value = failing_chunks()
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 4
            assert "Network error" in result.output

            # Verify no partial files remain
            assert not Path("bundle_01HQZX123ABC.zip").exists()
            # Check for no .tmp files
            tmp_files = list(Path.cwd().glob("*.tmp"))
            assert len(tmp_files) == 0


def test_download_disk_full_cleanup(runner):
    """
    Scenario: Disk full during download

    Tests cleanup when write fails due to disk space.
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock
        mock_instance = Mock()

        # Create chunks that will cause write to fail
        def chunks_generator():
            for _ in range(1000000):  # Many chunks
                yield b"x" * 1024 * 1024  # 1MB each

        mock_instance.download_bundle.return_value = chunks_generator()
        mock_client.return_value = mock_instance

        with patch("cli.commands.download.download_with_progress") as mock_download:
            # Simulate disk full error
            mock_download.side_effect = IOError("No space left on device")

            # Run command
            with runner.isolated_filesystem():
                result = runner.invoke(download, ["01HQZX123ABC"])

                # Assertions
                assert result.exit_code == 4
                assert "Failed to write file" in result.output


def test_download_empty_bundle(runner):
    """
    Scenario: Empty bundle download
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock with empty response
        mock_instance = Mock()
        mock_instance.download_bundle.return_value = iter([])
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX000000"])

            # Assertions
            assert result.exit_code == 0
            assert Path("bundle_01HQZX000000.zip").exists()
            # Empty archive should still exist but be 0 bytes
            assert Path("bundle_01HQZX000000.zip").stat().st_size == 0


def test_download_large_file_streaming(runner):
    """
    Scenario: Streaming download does not exhaust memory

    Tests that large downloads are streamed (can't fully test memory, but verify chunks work).
    """
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock with many chunks (simulating 10MB file)
        def large_chunks():
            for _ in range(100):
                yield b"x" * (100 * 1024)  # 100KB per chunk

        mock_instance = Mock()
        mock_instance.download_bundle.return_value = large_chunks()
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX999XXX"])

            # Assertions
            assert result.exit_code == 0
            assert Path("bundle_01HQZX999XXX.zip").exists()
            # Verify file size is as expected (10MB)
            assert Path("bundle_01HQZX999XXX.zip").stat().st_size == 100 * 100 * 1024


def test_download_http_error_non_404(runner):
    """Test handling of non-404 HTTP errors."""
    with patch("cli.commands.download.BundlesAPIClient") as mock_client:
        # Setup mock to raise 500 HTTPError
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        error = requests.exceptions.HTTPError(response=mock_response)
        mock_instance.download_bundle.side_effect = error
        mock_client.return_value = mock_instance

        # Run command
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["01HQZX123ABC"])

            # Assertions
            assert result.exit_code == 4
            assert "HTTP error" in result.output
