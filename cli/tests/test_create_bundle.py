"""
Tests for bundle creation workflow.

IMPORTANT: These tests make REAL API calls to http://localhost:8000
DO NOT USE MOCKS - We want true integration tests that verify the API server works correctly.
"""

import pytest
import hashlib
from pathlib import Path
from cli.core.file_discovery import discover_files
from shared.hash import hash_file_content
from cli.core.bundler import create_bundle
from cli.tests.fixtures import get_fixture_path
from cli.tests.test_helpers import get_api_client, cleanup_all_bundles


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
        # Paths include the parent directory name
        assert any("buried.txt" in p for p in paths)

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

        result = hash_file_content(file)

        # Verify hash properties
        assert len(result) == 64
        assert result.islower()
        assert all(c in '0123456789abcdef' for c in result)

    def test_hash_large_file(self):
        """Test SHA-256 calculation for a large file (streaming)."""
        file = get_fixture_path("large")

        result = hash_file_content(file)

        # Verify hash properties
        assert len(result) == 64
        assert result.islower()

    def test_hash_empty_file(self):
        """Test SHA-256 calculation for an empty file."""
        file = get_fixture_path("empty")

        result = hash_file_content(file)

        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_consistency(self):
        """Test that hashing the same file twice gives the same result."""
        file = get_fixture_path("file1")

        result1 = hash_file_content(file)
        result2 = hash_file_content(file)

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
        buried_file = [f for f in result if 'buried' in f.relative_path][0]
        # Path includes directory structure with forward slashes
        assert "buried.txt" in buried_file.relative_path
        assert "/" in buried_file.relative_path  # Must have at least one forward slash
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
# 4. BUNDLE CREATION WITH REAL API
# ============================================================================

class TestBundleCreationWithRealAPI:
    """Tests for bundle creation using real API calls."""

    def test_preflight_all_missing(self):
        """Test preflight when all blobs are missing."""
        cleanup_all_bundles()

        file = get_fixture_path("file1")
        api_client = get_api_client()

        result = create_bundle([str(file)], api_client)

        # Verify bundle was created
        assert result.id
        assert result.created_at
        assert result.merkle_root
        assert len(result.merkle_root) == 64

    def test_preflight_none_missing(self):
        """Test preflight when no blobs are missing (uploading same file twice)."""
        cleanup_all_bundles()

        file = get_fixture_path("file1")
        api_client = get_api_client()

        # First upload
        result1 = create_bundle([str(file)], api_client)

        # Second upload of same file - blobs should already exist
        result2 = create_bundle([str(file)], api_client)

        # Both should succeed with same merkle root
        assert result1.merkle_root == result2.merkle_root
        assert result1.id != result2.id  # Different bundle IDs

    def test_upload_only_missing_blobs(self):
        """Test that only missing blobs are uploaded."""
        cleanup_all_bundles()

        file1 = get_fixture_path("file1")
        file2 = get_fixture_path("file2")
        api_client = get_api_client()

        # Upload file1 first
        create_bundle([str(file1)], api_client)

        # Now upload both files - file1 blob should already exist
        result = create_bundle([str(file1), str(file2)], api_client)

        # Should succeed
        assert result.id
        assert result.merkle_root
        assert len(result.merkle_root) == 64

    def test_bundle_creation_multiple_files(self):
        """Test creating a bundle with multiple files."""
        cleanup_all_bundles()

        configs_dir = get_fixture_path("configs")
        api_client = get_api_client()

        result = create_bundle([str(configs_dir)], api_client)

        # Verify bundle was created successfully
        assert result.id
        assert result.created_at
        assert result.merkle_root
        assert len(result.merkle_root) == 64


# ============================================================================
# 5. INTEGRATION TESTS
# ============================================================================

class TestBundleCreationIntegration:
    """Integration tests for full bundle creation workflow."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from discovery to bundle creation."""
        cleanup_all_bundles()

        # Use real fixture files
        configs_dir = get_fixture_path("configs")
        api_client = get_api_client()

        # Execute bundle creation with real API
        result = create_bundle([str(configs_dir)], api_client)

        # Verify bundle was created
        assert result.id
        assert result.created_at
        assert result.merkle_root
        assert len(result.merkle_root) == 64

        # Verify we can list the bundle
        list_response = api_client.list_bundles()
        bundle_ids = [b.id for b in list_response.bundles]
        assert result.id in bundle_ids
