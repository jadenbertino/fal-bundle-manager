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
from shared.api_contracts.create_bundle import BundleCreateResponse
from shared.api_contracts.list_bundles import BundleListResponse
from shared.merkle import compute_merkle_root


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
        with runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.txt")
            test_file.write_text("Hello, World!")
            
            # Compute expected merkle root
            content = "Hello, World!"
            content_bytes = content.encode('utf-8')
            file_hash = hashlib.sha256(content_bytes).hexdigest()
            
            blob = Blob(
                bundle_path="test.txt",
                size_bytes=len(content_bytes),
                hash=file_hash,
                hash_algo="sha256"
            )
            expected_merkle = compute_merkle_root([blob])
            
            # Setup create mock
            mock_create_api = Mock()
            mock_create_api.preflight.return_value = PreflightResponse(missing=[])
            mock_create_api.upload_blob.return_value = True
            mock_create_api.create_bundle.return_value = BundleCreateResponse(
                id="01HQZX123ABC456DEF789GHI",
                created_at="2024-01-15T10:30:00Z",
                merkle_root=expected_merkle
            )
            mock_create_client.return_value = mock_create_api
            
            # 1. Create bundle
            result = runner.invoke(cli, ['create', 'test.txt'])
            assert result.exit_code == 0
            assert "Created bundle:" in result.output
            assert "01HQZX123ABC456DEF789GHI" in result.output
            assert expected_merkle in result.output
            
            # Setup list mock
            mock_list_api = Mock()
            mock_list_api.list_bundles.return_value = BundleListResponse(
                bundles=[
                    BundleSummary(
                        id="01HQZX123ABC456DEF789GHI",
                        created_at="2024-01-15T10:30:00Z",
                        hash_algo="sha256",
                        file_count=1,
                        total_bytes=13,
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
            assert "13 B" in result.output  # size
            
            # Setup download mock
            zip_content = self.create_mock_zip_content({"test.txt": "Hello, World!"})
            mock_download_api = Mock()
            mock_download_api.download_bundle.return_value = iter([zip_content])
            mock_download_client.return_value = mock_download_api
            
            # 3. Download bundle
            result = runner.invoke(cli, ['download', '01HQZX123ABC456DEF789GHI'])
            assert result.exit_code == 0
            assert "Downloaded bundle_01HQZX123ABC456DEF789GHI.zip" in result.output
            
            # 4. Verify downloaded file exists
            downloaded_file = Path("bundle_01HQZX123ABC456DEF789GHI.zip")
            assert downloaded_file.exists()
            
            # 5. Extract and verify contents
            extract_dir = Path("extracted")
            extract_dir.mkdir()
            
            with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                zip_file.extractall(extract_dir)
            
            extracted_file = extract_dir / "test.txt"
            assert extracted_file.exists()
            assert extracted_file.read_text() == "Hello, World!"
            
            # 6. Recompute hash from extracted file
            extracted_content = extracted_file.read_bytes()
            extracted_hash = hashlib.sha256(extracted_content).hexdigest()
            
            # 7. Verify hash matches original
            assert extracted_hash == file_hash, f"Hash mismatch: expected {file_hash}, got {extracted_hash}"
            
            # 8. Recompute merkle root from extracted file
            extracted_blob = Blob(
                bundle_path="test.txt",
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
        with runner.isolated_filesystem():
            # Create complex directory structure
            project_dir = Path("test_project")
            project_dir.mkdir()
            
            # Create files at different levels
            (project_dir / "README.md").write_text("# Test Project\nThis is a test.")
            (project_dir / "config.yaml").write_text("app: test\nversion: 1.0")
            
            models_dir = project_dir / "models"
            models_dir.mkdir()
            (models_dir / "model.bin").write_bytes(b"binary_model_data")
            
            data_dir = project_dir / "data"
            data_dir.mkdir()
            (data_dir / "dataset.json").write_text('{"samples": 100}')
            
            # Compute expected merkle root
            files_data = {
                "README.md": "# Test Project\nThis is a test.",
                "config.yaml": "app: test\nversion: 1.0",
                "models/model.bin": b"binary_model_data",
                "data/dataset.json": '{"samples": 100}'
            }
            
            expected_blobs = []
            for file_path, content in files_data.items():
                if isinstance(content, str):
                    content_bytes = content.encode('utf-8')
                else:
                    content_bytes = content
                
                file_hash = hashlib.sha256(content_bytes).hexdigest()
                blob = Blob(
                    bundle_path=file_path,
                    size_bytes=len(content_bytes),
                    hash=file_hash,
                    hash_algo="sha256"
                )
                expected_blobs.append(blob)
            
            expected_merkle = compute_merkle_root(expected_blobs)
            
            # Setup create mock
            mock_create_api = Mock()
            mock_create_api.preflight.return_value = PreflightResponse(missing=[])
            mock_create_api.upload_blob.return_value = True
            mock_create_api.create_bundle.return_value = BundleCreateResponse(
                id="01HQZX789XYZ123ABC456DEF",
                created_at="2024-01-15T11:00:00Z",
                merkle_root=expected_merkle
            )
            mock_create_client.return_value = mock_create_api
            
            # 1. Create bundle
            result = runner.invoke(cli, ['create', 'test_project'])
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
            extract_dir.mkdir()
            
            with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                zip_file.extractall(extract_dir)
            
            # 4. Verify all files exist with correct content
            for file_path, expected_content in files_data.items():
                full_path = extract_dir / file_path
                assert full_path.exists(), f"File {file_path} not found in extracted bundle"
                
                if isinstance(expected_content, str):
                    actual_content = full_path.read_text()
                else:
                    actual_content = full_path.read_bytes()
                
                assert actual_content == expected_content, f"Content mismatch for {file_path}"
            
            # 5. Recompute hashes and merkle root from extracted files
            extracted_blobs = []
            for file_path, expected_content in files_data.items():
                full_path = extract_dir / file_path
                
                if isinstance(expected_content, str):
                    content_bytes = expected_content.encode('utf-8')
                else:
                    content_bytes = expected_content
                
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
            
            # 8. Verify all individual hashes match
            for i, (extracted_blob, expected_blob) in enumerate(zip(extracted_blobs, expected_blobs)):
                assert extracted_blob.hash == expected_blob.hash, f"Hash mismatch for file {i}: {extracted_blob.bundle_path}"

    @patch('cli.commands.create.BundlesAPIClient')
    def test_merkle_root_verification(self, mock_create_client, runner):
        """Test that merkle root verification works correctly."""
        with runner.isolated_filesystem():
            # Create test files
            file1 = Path("file1.txt")
            file1.write_text("content1")
            
            file2 = Path("file2.txt")
            file2.write_text("content2")
            
            # Compute expected merkle root
            blobs = [
                Blob(bundle_path="file1.txt", size_bytes=8, hash=hashlib.sha256(b"content1").hexdigest(), hash_algo="sha256"),
                Blob(bundle_path="file2.txt", size_bytes=8, hash=hashlib.sha256(b"content2").hexdigest(), hash_algo="sha256")
            ]
            expected_merkle = compute_merkle_root(blobs)
            
            # Setup create mock with correct merkle root
            mock_create_api = Mock()
            mock_create_api.preflight.return_value = PreflightResponse(missing=[])
            mock_create_api.upload_blob.return_value = True
            mock_create_api.create_bundle.return_value = BundleCreateResponse(
                id="01HQZX123ABC456DEF789GHI",
                created_at="2024-01-15T10:30:00Z",
                merkle_root=expected_merkle
            )
            mock_create_client.return_value = mock_create_api
            
            # Create bundle
            result = runner.invoke(cli, ['create', 'file1.txt', 'file2.txt'])
            assert result.exit_code == 0
            
            # Verify merkle root matches
            assert expected_merkle in result.output

    @patch('cli.commands.create.BundlesAPIClient')
    def test_merkle_root_mismatch_detection(self, mock_create_client, runner):
        """Test that merkle root mismatch is detected."""
        with runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.txt")
            test_file.write_text("hello")
            
            # Compute correct merkle root
            content = "hello"
            content_bytes = content.encode('utf-8')
            file_hash = hashlib.sha256(content_bytes).hexdigest()
            
            blob = Blob(
                bundle_path="test.txt",
                size_bytes=len(content_bytes),
                hash=file_hash,
                hash_algo="sha256"
            )
            correct_merkle = compute_merkle_root([blob])
            
            # Mock API client with incorrect merkle root
            mock_create_api = Mock()
            mock_create_api.preflight.return_value = PreflightResponse(missing=[])
            mock_create_api.upload_blob.return_value = True
            mock_create_api.create_bundle.return_value = BundleCreateResponse(
                id="01HQZX123ABC456DEF789GHI",
                created_at="2024-01-15T10:30:00Z",
                merkle_root="a" * 64  # Wrong merkle root
            )
            mock_create_client.return_value = mock_create_api
            
            # Create bundle should fail due to merkle root mismatch
            result = runner.invoke(cli, ['create', 'test.txt'])
            assert result.exit_code != 0
            assert "Merkle root mismatch" in result.output

    def test_error_handling(self, runner):
        """Test error handling scenarios."""
        with runner.isolated_filesystem():
            # Test with non-existent file
            result = runner.invoke(cli, ['create', 'nonexistent.txt'])
            assert result.exit_code == 2
            
            # Test with empty directory
            empty_dir = Path("empty_dir")
            empty_dir.mkdir()
            result = runner.invoke(cli, ['create', 'empty_dir'])
            assert result.exit_code == 2
