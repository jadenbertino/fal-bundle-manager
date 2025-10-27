"""
Tests for bundle creation workflow.
"""

import pytest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, MagicMock
from cli.core.file_discovery import discover_files, DiscoveredFile
from cli.core.hashing import hash_file_sha256
from cli.core.bundler import create_bundle
from cli.tests.fixtures import get_fixture_path, FIXTURE_FILES, FIXTURE_DIRS
from shared.types import Blob
from shared.api_contracts.preflight import PreflightResponse
from shared.api_contracts.create_bundle import BundleCreateResponse


# ============================================================================
# 1. FILE DISCOVERY TESTS
# ============================================================================


class TestFileDiscovery:
    """Tests for file discovery logic."""

    def test_discover_single_file(self):
        """Test discovering a single file."""
        file = get_fixture_path("file1")

        result = discover_files([str(file)])

        assert len(result) == 1
        assert result[0].absolute_path == file
        assert result[0].relative_path == "file1.txt"
        assert result[0].size_bytes == 12  # "Hello World\n"

    def test_discover_directory_recursive(self):
        """Test discovering files in a directory recursively."""
        nested_dir = get_fixture_path("nested")

        result = discover_files([str(nested_dir)])

        assert len(result) >= 1
        paths = {f.relative_path for f in result}
        assert "deep/buried.txt" in paths

    def test_discover_multiple_paths(self):
        """Test discovering files from multiple paths."""
        file1 = get_fixture_path("file1")
        configs_dir = get_fixture_path("configs")

        result = discover_files([str(file1), str(configs_dir)])

        assert len(result) >= 3  # file1.txt + configs files
        paths = {f.relative_path for f in result}
        assert "file1.txt" in paths

    def test_discover_empty_directory(self, tmp_path):
        """Test discovering from an empty directory."""
        empty_dir = tmp_path / "truly_empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="No files discovered"):
            discover_files([str(empty_dir)])

    def test_discover_nonexistent_path(self):
        """Test discovering from a non-existent path."""
        with pytest.raises(FileNotFoundError):
            discover_files(["nonexistent.txt"])


# ============================================================================
# 2. HASHING TESTS
# ============================================================================


class TestHashing:
    """Tests for file hashing logic."""

    def test_hash_small_file(self):
        """Test SHA-256 calculation for a small file."""
        file = get_fixture_path("file1")

        result = hash_file_sha256(file)

        # Verify hash properties
        assert len(result) == 64
        assert result.islower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_large_file(self):
        """Test SHA-256 calculation for a large file (streaming)."""
        file = get_fixture_path("large")

        result = hash_file_sha256(file)

        # Verify hash properties
        assert len(result) == 64
        assert result.islower()

    def test_hash_empty_file(self):
        """Test SHA-256 calculation for an empty file."""
        file = get_fixture_path("empty")

        result = hash_file_sha256(file)

        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_consistency(self):
        """Test that hashing the same file twice gives the same result."""
        file = get_fixture_path("file1")

        result1 = hash_file_sha256(file)
        result2 = hash_file_sha256(file)

        assert result1 == result2


# ============================================================================
# 3. PATH NORMALIZATION TESTS
# ============================================================================


class TestPathNormalization:
    """Tests for path normalization in file discovery."""

    def test_relative_path_uses_forward_slashes(self):
        """Test that relative paths use forward slashes (POSIX style)."""
        nested_dir = get_fixture_path("nested")

        result = discover_files([str(nested_dir)])

        # Should use forward slashes even on Windows
        buried_file = [f for f in result if "buried" in f.relative_path][0]
        assert "deep/buried.txt" == buried_file.relative_path
        assert "\\" not in buried_file.relative_path

    def test_paths_no_leading_slash(self):
        """Test that relative paths don't start with '/'."""
        file = get_fixture_path("file1")

        result = discover_files([str(file)])

        assert not result[0].relative_path.startswith("/")

    def test_paths_no_parent_references(self):
        """Test that relative paths don't contain '..'."""
        configs_dir = get_fixture_path("configs")

        result = discover_files([str(configs_dir)])

        for discovered in result:
            assert ".." not in discovered.relative_path


# ============================================================================
# 4. API CLIENT MOCK TESTS
# ============================================================================


class TestBundleCreationWithMocks:
    """Tests for bundle creation using mocked API client."""

    def test_preflight_all_missing(self):
        """Test preflight when all blobs are missing."""
        file = get_fixture_path("file1")

        # Mock API client
        api_client = Mock()
        file_hash = hash_file_sha256(file)
        api_client.preflight.return_value = PreflightResponse(missing=[file_hash])
        api_client.upload_blob.return_value = True
        api_client.create_bundle.return_value = BundleCreateResponse(
            id="test-bundle-id",
            created_at="2024-01-01T00:00:00Z",
            merkle_root="e" * 64,
        )

        result = create_bundle([str(file)], api_client)

        assert result.id == "test-bundle-id"
        assert api_client.preflight.called
        assert api_client.upload_blob.called
        assert api_client.create_bundle.called

    def test_preflight_none_missing(self):
        """Test preflight when no blobs are missing."""
        file = get_fixture_path("file1")

        # Mock API client
        api_client = Mock()
        api_client.preflight.return_value = PreflightResponse(missing=[])
        api_client.create_bundle.return_value = BundleCreateResponse(
            id="test-bundle-id",
            created_at="2024-01-01T00:00:00Z",
            merkle_root="e" * 64,
        )

        result = create_bundle([str(file)], api_client)

        assert result.id == "test-bundle-id"
        assert api_client.preflight.called
        assert not api_client.upload_blob.called  # Should not upload
        assert api_client.create_bundle.called

    def test_upload_only_missing_blobs(self):
        """Test that only missing blobs are uploaded."""
        file1 = get_fixture_path("file1")
        file2 = get_fixture_path("file2")

        hash1 = hash_file_sha256(file1)
        hash2 = hash_file_sha256(file2)

        # Mock API client - only file2 is missing
        api_client = Mock()
        api_client.preflight.return_value = PreflightResponse(missing=[hash2])
        api_client.upload_blob.return_value = True
        api_client.create_bundle.return_value = BundleCreateResponse(
            id="test-bundle-id",
            created_at="2024-01-01T00:00:00Z",
            merkle_root="e" * 64,
        )

        result = create_bundle([str(file1), str(file2)], api_client)

        # Should only upload once (for file2)
        assert api_client.upload_blob.call_count == 1
        # Check that file2's hash was uploaded
        uploaded_hash = api_client.upload_blob.call_args[0][0]
        assert uploaded_hash == hash2

    def test_bundle_creation_multiple_files(self):
        """Test creating a bundle with multiple files."""
        configs_dir = get_fixture_path("configs")

        api_client = Mock()
        api_client.preflight.return_value = PreflightResponse(missing=[])
        api_client.create_bundle.return_value = BundleCreateResponse(
            id="test-bundle-id",
            created_at="2024-01-01T00:00:00Z",
            merkle_root="e" * 64,
        )

        result = create_bundle([str(configs_dir)], api_client)

        # Verify manifest has config files
        manifest = api_client.create_bundle.call_args[0][0]
        assert len(manifest.files) >= 2  # app.yaml and database.json
        paths = {f.bundle_path for f in manifest.files}
        assert "app.yaml" in paths or "database.json" in paths


# ============================================================================
# 5. INTEGRATION TESTS
# ============================================================================


class TestBundleCreationIntegration:
    """Integration tests for full bundle creation workflow."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from discovery to bundle creation."""
        # Use real fixture files
        configs_dir = get_fixture_path("configs")

        # Mock API client
        api_client = Mock()

        # Get hashes of actual files
        discovered = discover_files([str(configs_dir)])
        hashes = [hash_file_sha256(f.absolute_path) for f in discovered]

        api_client.preflight.return_value = PreflightResponse(missing=hashes)
        api_client.upload_blob.return_value = True
        api_client.create_bundle.return_value = BundleCreateResponse(
            id="bundle-123",
            created_at="2024-01-01T00:00:00Z",
            merkle_root="e" * 64,
        )

        # Execute
        result = create_bundle([str(configs_dir)], api_client)

        # Verify
        assert result.id == "bundle-123"
        assert api_client.preflight.call_count == 1
        assert api_client.upload_blob.call_count == len(hashes)
        assert api_client.create_bundle.call_count == 1

        # Verify manifest structure
        manifest = api_client.create_bundle.call_args[0][0]
        assert manifest.hash_algo == "sha256"
        assert len(manifest.files) == len(hashes)
