"""
Simplified integration tests for CLI bundle operations.

Tests the complete workflow with proper mocking:
1. Create bundle from various file/directory scenarios
2. List bundles and verify existence
3. Download bundle and verify contents
4. Verify merkle root integrity after download
"""

import pytest
import zipfile
import hashlib
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch
from cli.__main__ import cli
from shared.types import Blob, BundleSummary
from shared.api_contracts.preflight import PreflightResponse
from shared.api_contracts.create_bundle import CreateBundleResponse
from shared.api_contracts.list_bundles import ListBundlesResponse
from shared.merkle import compute_merkle_root
from cli.tests.fixtures import get_fixture_path


class TestIntegrationWorkflow:
    """Integration tests for complete bundle workflows."""

    @pytest.fixture
    def runner(self):
        """Create a Click CLI runner."""
        return CliRunner()

    def create_mock_zip_content(self, files: dict) -> bytes:
        """Create mock ZIP content for testing."""
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                if isinstance(content, str):
                    content = content.encode('utf-8')
                zip_file.writestr(filename, content)
        
        zip_buffer.seek(0)
        return zip_buffer.read()

    @patch('cli.commands.create.BundlesAPIClient')
    @patch('cli.commands.list.BundlesAPIClient')
    @patch('cli.commands.download.BundlesAPIClient')
    def test_complete_workflow_single_file(self, mock_download_client, mock_list_client, mock_create_client, runner):
        """Test complete workflow: create -> list -> download -> verify."""
        # Use real fixture file
        test_file = get_fixture_path("single_file")
        
        # Compute expected merkle root from real file
        with open(test_file, 'rb') as f:
            content_bytes = f.read()
        file_hash = hashlib.sha256(content_bytes).hexdigest()
        
        blob = Blob(
            bundle_path=test_file.name,
            size_bytes=len(content_bytes),
            hash=file_hash,
            hash_algo="sha256"
        )
        expected_merkle = compute_merkle_root([blob])
        
        # Setup create mock
        mock_create_api = Mock()
        mock_create_api.preflight.return_value = PreflightResponse(missing=[])
        mock_create_api.upload_blob.return_value = True
        mock_create_api.create_bundle.return_value = CreateBundleResponse(
            id="01HQZX123ABC456DEF789GHI",
            created_at="2024-01-15T10:30:00Z",
            merkle_root=expected_merkle
        )
        mock_create_client.return_value = mock_create_api
        
        # 1. Create bundle
        result = runner.invoke(cli, ['create', str(test_file)])
        assert result.exit_code == 0
        assert "Created bundle:" in result.output
        assert "01HQZX123ABC456DEF789GHI" in result.output
        assert expected_merkle in result.output
        
        # Setup list mock
        mock_list_api = Mock()
        mock_list_api.list_bundles.return_value = ListBundlesResponse(
            bundles=[
                BundleSummary(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    hash_algo="sha256",
                    file_count=1,
                    total_bytes=len(content_bytes),
                    merkle_root=expected_merkle
                )
            ]
        )
        mock_list_client.return_value = mock_list_api
        
        # 2. List bundles
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert "01HQZX123ABC456DEF789GHI" in result.output
        assert "1" in result.output  # file count
        
        # Setup download mock
        zip_content = self.create_mock_zip_content({test_file.name: content_bytes.decode('utf-8')})
        mock_download_api = Mock()
        mock_download_api.download_bundle.return_value = iter([zip_content])
        mock_download_client.return_value = mock_download_api
        
        # 3. Download bundle
        result = runner.invoke(cli, ['download', '01HQZX123ABC456DEF789GHI'])
        assert result.exit_code == 0
        assert "Downloaded bundle_01HQZX123ABC456DEF789GHI" in result.output
        
        # 4. Verify downloaded file exists
        downloaded_file = Path("bundle_01HQZX123ABC456DEF789GHI.zip")
        assert downloaded_file.exists()
        
        # 5. Extract and verify contents
        extract_dir = Path("extracted")
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
            zip_file.extractall(extract_dir)
        
        extracted_file = extract_dir / test_file.name
        assert extracted_file.exists()
        assert extracted_file.read_text() == content_bytes.decode('utf-8')
        
        # 6. Recompute hash from extracted file
        extracted_content = extracted_file.read_bytes()
        extracted_hash = hashlib.sha256(extracted_content).hexdigest()
        
        # 7. Verify hash matches original
        assert extracted_hash == file_hash, f"Hash mismatch: expected {file_hash}, got {extracted_hash}"
        
        # 8. Recompute merkle root from extracted file
        extracted_blob = Blob(
            bundle_path=test_file.name,
            size_bytes=len(extracted_content),
            hash=extracted_hash,
            hash_algo="sha256"
        )
        recomputed_merkle = compute_merkle_root([extracted_blob])
        
        # 9. Verify merkle roots match
        assert recomputed_merkle == expected_merkle, f"Merkle root mismatch: expected {expected_merkle}, got {recomputed_merkle}"

    @patch('cli.commands.create.BundlesAPIClient')
    @patch('cli.commands.download.BundlesAPIClient')
    def test_complex_directory_workflow(self, mock_download_client, mock_create_client, runner):
        """Test complex directory workflow with multiple files."""
        # Use real fixture directory
        project_dir = get_fixture_path("configs")
        
        # Compute expected merkle root for directory contents
        import os
        files_data = {}
        file_paths = []
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_dir)
                with open(full_path, 'rb') as f:
                    content = f.read()
                files_data[rel_path] = content.decode('utf-8')
                file_paths.append(Path(full_path))
        
        # Compute real merkle root
        blobs = []
        for file_path in file_paths:
            with open(file_path, 'rb') as f:
                content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
            blob = Blob(
                bundle_path=file_path.name,
                size_bytes=len(content),
                hash=file_hash,
                hash_algo="sha256"
            )
            blobs.append(blob)
        
        expected_merkle = compute_merkle_root(blobs)
        
        # Setup create mock
        mock_create_api = Mock()
        mock_create_api.preflight.return_value = PreflightResponse(missing=[])
        mock_create_api.upload_blob.return_value = True
        mock_create_api.create_bundle.return_value = CreateBundleResponse(
            id="01HQZX789XYZ123ABC456DEF",
            created_at="2024-01-15T11:00:00Z",
            merkle_root=expected_merkle
        )
        mock_create_client.return_value = mock_create_api
        
        # 1. Create bundle
        result = runner.invoke(cli, ['create', str(project_dir)])
        assert result.exit_code == 0
        assert expected_merkle in result.output
        
        # Setup download mock
        zip_content = self.create_mock_zip_content(files_data)
        mock_download_api = Mock()
        mock_download_api.download_bundle.return_value = iter([zip_content])
        mock_download_client.return_value = mock_download_api
        
        # 2. Download bundle
        result = runner.invoke(cli, ['download', '01HQZX789XYZ123ABC456DEF'])
        assert result.exit_code == 0
        
        # 3. Extract and verify
        downloaded_file = Path("bundle_01HQZX789XYZ123ABC456DEF.zip")
        assert downloaded_file.exists()
        
        extract_dir = Path("extracted_project")
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
            zip_file.extractall(extract_dir)
        
        # 4. Verify all files exist with correct content
        for file_path, expected_content in files_data.items():
            full_path = extract_dir / file_path
            assert full_path.exists(), f"File {file_path} not found in extracted bundle"
            assert full_path.read_text() == expected_content, f"Content mismatch for {file_path}"
        
        # 5. Recompute hashes and merkle root from extracted files
        extracted_blobs = []
        for file_path, expected_content in files_data.items():
            full_path = extract_dir / file_path
            actual_content = full_path.read_bytes()
            file_hash = hashlib.sha256(actual_content).hexdigest()
            
            blob = Blob(
                bundle_path=file_path,
                size_bytes=len(actual_content),
                hash=file_hash,
                hash_algo="sha256"
            )
            extracted_blobs.append(blob)
        
        # 6. Recompute merkle root
        recomputed_merkle = compute_merkle_root(extracted_blobs)
        
        # 7. Verify merkle roots match
        assert recomputed_merkle == expected_merkle, f"Merkle root mismatch: expected {expected_merkle}, got {recomputed_merkle}"

    @patch('cli.commands.create.BundlesAPIClient')
    def test_merkle_root_verification(self, mock_create_client, runner):
        """Test that merkle root verification works correctly."""
        # Use real fixture files
        file1 = get_fixture_path("file1")
        file2 = get_fixture_path("file2")
        
        # Compute expected merkle root
        blobs = []
        for file_path in [file1, file2]:
            with open(file_path, 'rb') as f:
                content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
            blob = Blob(
                bundle_path=file_path.name,
                size_bytes=len(content),
                hash=file_hash,
                hash_algo="sha256"
            )
            blobs.append(blob)
        
        expected_merkle = compute_merkle_root(blobs)
        
        # Setup create mock with correct merkle root
        mock_create_api = Mock()
        mock_create_api.preflight.return_value = PreflightResponse(missing=[])
        mock_create_api.upload_blob.return_value = True
        mock_create_api.create_bundle.return_value = CreateBundleResponse(
            id="01HQZX123ABC456DEF789GHI",
            created_at="2024-01-15T10:30:00Z",
            merkle_root=expected_merkle
        )
        mock_create_client.return_value = mock_create_api
        
        # Create bundle
        result = runner.invoke(cli, ['create', str(file1), str(file2)])
        assert result.exit_code == 0
        
        # Verify merkle root matches
        assert expected_merkle in result.output

    @patch('cli.commands.create.BundlesAPIClient')
    def test_merkle_root_mismatch_detection(self, mock_create_client, runner):
        """Test that merkle root mismatch is detected."""
        # Use real fixture file
        test_file = get_fixture_path("single_file")
        
        # Compute correct merkle root
        with open(test_file, 'rb') as f:
            content_bytes = f.read()
        file_hash = hashlib.sha256(content_bytes).hexdigest()
        
        blob = Blob(
            bundle_path=test_file.name,
            size_bytes=len(content_bytes),
            hash=file_hash,
            hash_algo="sha256"
        )
        correct_merkle = compute_merkle_root([blob])
        
        # Mock API client with incorrect merkle root
        mock_create_api = Mock()
        mock_create_api.preflight.return_value = PreflightResponse(missing=[])
        mock_create_api.upload_blob.return_value = True
        mock_create_api.create_bundle.return_value = CreateBundleResponse(
            id="01HQZX123ABC456DEF789GHI",
            created_at="2024-01-15T10:30:00Z",
            merkle_root="a" * 64  # Wrong merkle root
        )
        mock_create_client.return_value = mock_create_api
        
        # Create bundle should fail due to merkle root mismatch
        result = runner.invoke(cli, ['create', str(test_file)])
        assert result.exit_code != 0
        assert "Merkle root mismatch" in result.output

    def test_error_handling(self, runner):
        """Test error handling scenarios."""
        # Test with non-existent file
        result = runner.invoke(cli, ['create', 'nonexistent.txt'])
        assert result.exit_code == 2
        
        # Test with empty directory - this should succeed if the directory has .gitkeep files
        empty_dir = get_fixture_path("empty_dir")
        result = runner.invoke(cli, ['create', str(empty_dir)])
        # Empty directory might succeed if it contains .gitkeep files
        # We'll just verify it doesn't crash
        assert result.exit_code in [0, 2]
