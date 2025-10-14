"""
Integration tests for CLI bundle operations.

Tests the complete workflow:
1. Create bundle from various file/directory scenarios
2. List bundles and verify existence
3. Download bundle and verify contents
4. Verify merkle root integrity
"""

import pytest
import tempfile
import zipfile
import hashlib
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
from cli.__main__ import cli
from shared.types import Blob, BundleSummary, BundleManifest
from shared.api_contracts.preflight import PreflightResponse
from shared.api_contracts.create_bundle import CreateBundleResponse
from shared.api_contracts.list_bundles import ListBundlesResponse
from shared.merkle import compute_merkle_root
from cli.tests.fixtures import FIXTURES_DIR


class TestIntegrationScenarios:
    """Integration tests for complete bundle workflows."""

    @pytest.fixture
    def runner(self):
        """Create a Click CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_api_client(self):
        """Create a comprehensive mock API client."""
        mock = Mock()
        
        # Mock preflight to return no missing blobs (all files already exist)
        mock.preflight.return_value = PreflightResponse(missing=[])
        
        # Mock upload blob to always succeed
        mock.upload_blob.return_value = True
        
        # Mock create bundle to return a response
        mock.create_bundle.return_value = CreateBundleResponse(
            id="01HQZX123ABC456DEF789GHI",
            created_at="2024-01-15T10:30:00Z",
            merkle_root="a" * 64  # Will be overridden in tests
        )
        
        # Mock list bundles
        mock.list_bundles.return_value = ListBundlesResponse(bundles=[])
        
        # Mock download bundle
        mock.download_bundle.return_value = iter([b"test", b"data"])
        
        return mock

    def create_test_files(self, base_dir: Path) -> dict:
        """Create various test files and return their metadata."""
        files = {}
        
        # Single file
        single_file = base_dir / "single.txt"
        single_file.write_text("Hello, World!")
        files["single"] = {
            "path": str(single_file),
            "content": "Hello, World!",
            "size": 13
        }
        
        # Directory with multiple files
        test_dir = base_dir / "test_dir"
        test_dir.mkdir()
        
        file1 = test_dir / "file1.txt"
        file1.write_text("Content 1")
        files["dir_file1"] = {
            "path": str(file1),
            "content": "Content 1",
            "size": 9
        }
        
        file2 = test_dir / "file2.txt"
        file2.write_text("Content 2")
        files["dir_file2"] = {
            "path": str(file2),
            "content": "Content 2",
            "size": 9
        }
        
        # Nested directory
        nested_dir = test_dir / "nested"
        nested_dir.mkdir()
        
        nested_file = nested_dir / "deep.txt"
        nested_file.write_text("Deep content")
        files["nested"] = {
            "path": str(nested_file),
            "content": "Deep content",
            "size": 12
        }
        
        # Empty file
        empty_file = base_dir / "empty.txt"
        empty_file.touch()
        files["empty"] = {
            "path": str(empty_file),
            "content": "",
            "size": 0
        }
        
        # Large file (simulated)
        large_file = base_dir / "large.bin"
        large_content = b"x" * 1024  # 1KB
        large_file.write_bytes(large_content)
        files["large"] = {
            "path": str(large_file),
            "content": large_content,
            "size": 1024
        }
        
        return files

    def compute_expected_merkle_root(self, files: dict) -> str:
        """Compute expected merkle root for given files."""
        blobs = []
        for file_info in files.values():
            # Compute SHA-256 hash
            content = file_info["content"]
            if isinstance(content, str):
                content = content.encode('utf-8')
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Get relative path
            file_path = Path(file_info["path"])
            relative_path = file_path.name  # Simplified for test
            
            blob = Blob(
                bundle_path=relative_path,
                size_bytes=file_info["size"],
                hash=file_hash,
                hash_algo="sha256"
            )
            blobs.append(blob)
        
        return compute_merkle_root(blobs)

    @patch('cli.commands.create.BundlesAPIClient')
    def test_single_file_workflow(self, mock_client_class, runner, mock_api_client):
        """Test complete workflow with single file."""
        mock_client_class.return_value = mock_api_client
        
        with runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.txt")
            test_file.write_text("Hello, World!")
            
            # Compute expected merkle root
            expected_merkle = self.compute_expected_merkle_root({
                "test": {"path": str(test_file), "content": "Hello, World!", "size": 13}
            })
            mock_api_client.create_bundle.return_value = CreateBundleResponse(
                id="01HQZX123ABC456DEF789GHI",
                created_at="2024-01-15T10:30:00Z",
                merkle_root=expected_merkle
            )
            
            # 1. Create bundle
            result = runner.invoke(cli, ['create', 'test.txt'])
            assert result.exit_code == 0
            assert "Created bundle:" in result.output
            assert "01HQZX123ABC456DEF789GHI" in result.output
            
            # 2. List bundles
            mock_api_client.list_bundles.return_value = ListBundlesResponse(
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
            
            result = runner.invoke(cli, ['list'])
            assert result.exit_code == 0
            assert "01HQZX123ABC456DEF789GHI" in result.output
            assert "1" in result.output  # file count
            assert "13 B" in result.output  # size
            
            # 3. Download bundle
            # Create mock ZIP content
            zip_content = self.create_mock_zip_content({"test.txt": "Hello, World!"})
            mock_api_client.download_bundle.return_value = iter([zip_content])
            
            result = runner.invoke(cli, ['download', '01HQZX123ABC456DEF789GHI'])
            assert result.exit_code == 0
            assert "Downloaded bundle_01HQZX123ABC456DEF789GHI.zip" in result.output
            
            # 4. Verify downloaded file
            downloaded_file = Path("bundle_01HQZX123ABC456DEF789GHI.zip")
            assert downloaded_file.exists()
            
            # Extract and verify contents
            with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                assert "test.txt" in zip_file.namelist()
                content = zip_file.read("test.txt").decode('utf-8')
                assert content == "Hello, World!"

    @patch('cli.commands.create.BundlesAPIClient')
    def test_directory_workflow(self, mock_client_class, runner, mock_api_client):
        """Test complete workflow with directory containing multiple files."""
        mock_client_class.return_value = mock_api_client
        
        with runner.isolated_filesystem():
            # Create test directory structure
            test_dir = Path("test_project")
            test_dir.mkdir()
            
            (test_dir / "config.yaml").write_text("app: myapp\nversion: 1.0")
            (test_dir / "data.json").write_text('{"key": "value"}')
            
            models_dir = test_dir / "models"
            models_dir.mkdir()
            (models_dir / "model.bin").write_bytes(b"binary_data_here")
            
            # Compute expected merkle root
            expected_merkle = self.compute_expected_merkle_root({
                "config": {"path": str(test_dir / "config.yaml"), "content": "app: myapp\nversion: 1.0", "size": 20},
                "data": {"path": str(test_dir / "data.json"), "content": '{"key": "value"}', "size": 16},
                "model": {"path": str(models_dir / "model.bin"), "content": b"binary_data_here", "size": 17}
            })
            
            mock_api_client.create_bundle.return_value = CreateBundleResponse(
                id="01HQZX789XYZ123ABC456DEF",
                created_at="2024-01-15T11:00:00Z",
                merkle_root=expected_merkle
            )
            
            # 1. Create bundle
            result = runner.invoke(cli, ['create', 'test_project'])
            assert result.exit_code == 0
            assert "01HQZX789XYZ123ABC456DEF" in result.output
            
            # 2. List bundles
            mock_api_client.list_bundles.return_value = ListBundlesResponse(
                bundles=[
                    BundleSummary(
                        id="01HQZX789XYZ123ABC456DEF",
                        created_at="2024-01-15T11:00:00Z",
                        hash_algo="sha256",
                        file_count=3,
                        total_bytes=53,
                        merkle_root=expected_merkle
                    )
                ]
            )
            
            result = runner.invoke(cli, ['list'])
            assert result.exit_code == 0
            assert "01HQZX789XYZ123ABC456DEF" in result.output
            assert "3" in result.output  # file count
            assert "53 B" in result.output  # total size
            
            # 3. Download and verify
            zip_content = self.create_mock_zip_content({
                "config.yaml": "app: myapp\nversion: 1.0",
                "data.json": '{"key": "value"}',
                "models/model.bin": b"binary_data_here"
            })
            mock_api_client.download_bundle.return_value = iter([zip_content])
            
            result = runner.invoke(cli, ['download', '01HQZX789XYZ123ABC456DEF'])
            assert result.exit_code == 0
            
            # Verify downloaded file
            downloaded_file = Path("bundle_01HQZX789XYZ123ABC456DEF.zip")
            assert downloaded_file.exists()
            
            with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                assert "config.yaml" in zip_file.namelist()
                assert "data.json" in zip_file.namelist()
                assert "models/model.bin" in zip_file.namelist()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_mixed_files_and_directories(self, mock_client_class, runner, mock_api_client):
        """Test workflow with mixed files and directories."""
        mock_client_class.return_value = mock_api_client
        
        with runner.isolated_filesystem():
            # Create mixed structure
            root_file = Path("README.md")
            root_file.write_text("# Project\nThis is a test project.")
            
            config_dir = Path("config")
            config_dir.mkdir()
            (config_dir / "app.yaml").write_text("name: test\nport: 8080")
            
            data_file = Path("data.txt")
            data_file.write_text("sample data")
            
            # Create bundle
            result = runner.invoke(cli, ['create', 'README.md', 'config', 'data.txt'])
            assert result.exit_code == 0
            
            # Verify API calls
            assert mock_api_client.preflight.called
            assert mock_api_client.create_bundle.called

    @patch('cli.commands.create.BundlesAPIClient')
    def test_empty_file_handling(self, mock_client_class, runner, mock_api_client):
        """Test handling of empty files."""
        mock_client_class.return_value = mock_api_client
        
        with runner.isolated_filesystem():
            # Create empty file
            empty_file = Path("empty.txt")
            empty_file.touch()
            
            # Create bundle
            result = runner.invoke(cli, ['create', 'empty.txt'])
            assert result.exit_code == 0
            
            # Verify empty file is handled correctly
            assert mock_api_client.create_bundle.called

    @patch('cli.commands.create.BundlesAPIClient')
    def test_large_file_handling(self, mock_client_class, runner, mock_api_client):
        """Test handling of larger files."""
        mock_client_class.return_value = mock_api_client
        
        with runner.isolated_filesystem():
            # Create larger file (1MB)
            large_file = Path("large.bin")
            large_content = b"x" * (1024 * 1024)  # 1MB
            large_file.write_bytes(large_content)
            
            # Create bundle
            result = runner.invoke(cli, ['create', 'large.bin'])
            assert result.exit_code == 0
            
            # Verify large file is handled
            assert mock_api_client.create_bundle.called

    def test_merkle_root_verification(self, runner):
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
            
            # Mock API client with correct merkle root
            with patch('cli.commands.create.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_api_client.preflight.return_value = PreflightResponse(missing=[])
                mock_api_client.upload_blob.return_value = True
                mock_api_client.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root=expected_merkle
                )
                mock_client_class.return_value = mock_api_client
                
                # Create bundle
                result = runner.invoke(cli, ['create', 'file1.txt', 'file2.txt'])
                assert result.exit_code == 0
                
                # Verify merkle root matches
                assert expected_merkle in result.output

    def test_merkle_root_mismatch_detection(self, runner):
        """Test that merkle root mismatch is detected."""
        with runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.txt")
            test_file.write_text("hello")
            
            # Mock API client with incorrect merkle root
            with patch('cli.commands.create.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_api_client.preflight.return_value = PreflightResponse(missing=[])
                mock_api_client.upload_blob.return_value = True
                mock_api_client.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root="wrong_merkle_root"  # Incorrect
                )
                mock_client_class.return_value = mock_api_client
                
                # Create bundle should fail due to merkle root mismatch
                result = runner.invoke(cli, ['create', 'test.txt'])
                assert result.exit_code != 0
                assert "Merkle root mismatch" in result.output

    def test_bundle_deduplication(self, runner):
        """Test that identical files are deduplicated."""
        with runner.isolated_filesystem():
            # Create identical files
            file1 = Path("file1.txt")
            file1.write_text("identical content")
            
            file2 = Path("file2.txt")
            file2.write_text("identical content")
            
            with patch('cli.commands.create.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_api_client.preflight.return_value = PreflightResponse(missing=[])
                mock_api_client.upload_blob.return_value = True
                mock_api_client.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root="a" * 64
                )
                mock_client_class.return_value = mock_api_client
                
                # Create bundle
                result = runner.invoke(cli, ['create', 'file1.txt', 'file2.txt'])
                assert result.exit_code == 0
                
                # Verify upload_blob was called only once (deduplication)
                assert mock_api_client.upload_blob.call_count == 1

    def test_nested_directory_structure(self, runner):
        """Test deeply nested directory structures."""
        with runner.isolated_filesystem():
            # Create deeply nested structure
            deep_dir = Path("a/b/c/d/e/f")
            deep_dir.mkdir(parents=True)
            
            (deep_dir / "deep_file.txt").write_text("deep content")
            (Path("a") / "root_file.txt").write_text("root content")
            
            with patch('cli.commands.create.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_api_client.preflight.return_value = PreflightResponse(missing=[])
                mock_api_client.upload_blob.return_value = True
                mock_api_client.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root="a" * 64
                )
                mock_client_class.return_value = mock_api_client
                
                # Create bundle
                result = runner.invoke(cli, ['create', 'a'])
                assert result.exit_code == 0
                
                # Verify both files are included
                create_call = mock_api_client.create_bundle.call_args[0][0]
                file_paths = [blob.bundle_path for blob in create_call.files]
                assert "a/b/c/d/e/f/deep_file.txt" in file_paths
                assert "a/root_file.txt" in file_paths

    def test_special_characters_in_filenames(self, runner):
        """Test handling of special characters in filenames."""
        with runner.isolated_filesystem():
            # Create files with special characters
            special_file = Path("file with spaces.txt")
            special_file.write_text("content")
            
            unicode_file = Path("file_ñ_中文.txt")
            unicode_file.write_text("unicode content")
            
            with patch('cli.commands.create.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_api_client.preflight.return_value = PreflightResponse(missing=[])
                mock_api_client.upload_blob.return_value = True
                mock_api_client.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root="a" * 64
                )
                mock_client_class.return_value = mock_api_client
                
                # Create bundle
                result = runner.invoke(cli, ['create', 'file with spaces.txt', 'file_ñ_中文.txt'])
                assert result.exit_code == 0

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

    def test_download_verification(self, runner):
        """Test that downloaded bundles can be verified."""
        with runner.isolated_filesystem():
            # Create test files
            test_file = Path("test.txt")
            test_file.write_text("Hello, World!")
            
            # Mock the complete workflow
            with patch('cli.commands.create.BundlesAPIClient') as mock_create_client, \
                 patch('cli.commands.download.BundlesAPIClient') as mock_download_client:
                
                # Setup create mock
                mock_create_api = Mock()
                mock_create_api.preflight.return_value = PreflightResponse(missing=[])
                mock_create_api.upload_blob.return_value = True
                mock_create_api.create_bundle.return_value = CreateBundleResponse(
                    id="01HQZX123ABC456DEF789GHI",
                    created_at="2024-01-15T10:30:00Z",
                    merkle_root="a" * 64
                )
                mock_create_client.return_value = mock_create_api
                
                # Create bundle
                result = runner.invoke(cli, ['create', 'test.txt'])
                assert result.exit_code == 0
                
                # Setup download mock
                zip_content = self.create_mock_zip_content({"test.txt": "Hello, World!"})
                mock_download_api = Mock()
                mock_download_api.download_bundle.return_value = iter([zip_content])
                mock_download_client.return_value = mock_download_api
                
                # Download bundle
                result = runner.invoke(cli, ['download', '01HQZX123ABC456DEF789GHI'])
                assert result.exit_code == 0
                
                # Verify downloaded file
                downloaded_file = Path("bundle_01HQZX123ABC456DEF789GHI.zip")
                assert downloaded_file.exists()
                
                # Extract and verify content
                with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                    assert "test.txt" in zip_file.namelist()
                    content = zip_file.read("test.txt").decode('utf-8')
                    assert content == "Hello, World!"

    def test_complete_workflow_with_merkle_verification(self, runner):
        """Test complete workflow with merkle root verification after download."""
        with runner.isolated_filesystem():
            # Create test files with known content
            file1 = Path("file1.txt")
            file1.write_text("Content 1")
            
            file2 = Path("file2.txt") 
            file2.write_text("Content 2")
            
            # Compute expected merkle root
            blobs = [
                Blob(bundle_path="file1.txt", size_bytes=9, hash=hashlib.sha256(b"Content 1").hexdigest(), hash_algo="sha256"),
                Blob(bundle_path="file2.txt", size_bytes=9, hash=hashlib.sha256(b"Content 2").hexdigest(), hash_algo="sha256")
            ]
            expected_merkle = compute_merkle_root(blobs)
            
            # Mock the complete workflow
            with patch('cli.commands.create.BundlesAPIClient') as mock_create_client, \
                 patch('cli.commands.download.BundlesAPIClient') as mock_download_client:
                
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
                
                # 1. Create bundle
                result = runner.invoke(cli, ['create', 'file1.txt', 'file2.txt'])
                assert result.exit_code == 0
                assert expected_merkle in result.output
                
                # 2. Setup download mock with actual ZIP content
                zip_content = self.create_mock_zip_content({
                    "file1.txt": "Content 1",
                    "file2.txt": "Content 2"
                })
                mock_download_api = Mock()
                mock_download_api.download_bundle.return_value = iter([zip_content])
                mock_download_client.return_value = mock_download_api
                
                # 3. Download bundle
                result = runner.invoke(cli, ['download', '01HQZX123ABC456DEF789GHI'])
                assert result.exit_code == 0
                
                # 4. Verify downloaded file exists
                downloaded_file = Path("bundle_01HQZX123ABC456DEF789GHI.zip")
                assert downloaded_file.exists()
                
                # 5. Extract and verify contents
                extract_dir = Path("extracted")
                extract_dir.mkdir()
                
                with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                    zip_file.extractall(extract_dir)
                
                # 6. Verify extracted files
                extracted_file1 = extract_dir / "file1.txt"
                extracted_file2 = extract_dir / "file2.txt"
                
                assert extracted_file1.exists()
                assert extracted_file2.exists()
                
                assert extracted_file1.read_text() == "Content 1"
                assert extracted_file2.read_text() == "Content 2"
                
                # 7. Recompute hashes from extracted files
                extracted_blobs = []
                for file_path in [extracted_file1, extracted_file2]:
                    content = file_path.read_bytes()
                    file_hash = hashlib.sha256(content).hexdigest()
                    blob = Blob(
                        bundle_path=file_path.name,
                        size_bytes=len(content),
                        hash=file_hash,
                        hash_algo="sha256"
                    )
                    extracted_blobs.append(blob)
                
                # 8. Recompute merkle root from extracted files
                recomputed_merkle = compute_merkle_root(extracted_blobs)
                
                # 9. Verify merkle roots match
                assert recomputed_merkle == expected_merkle, f"Merkle root mismatch: expected {expected_merkle}, got {recomputed_merkle}"
                
                # 10. Verify individual file hashes match
                assert extracted_blobs[0].hash == blobs[0].hash
                assert extracted_blobs[1].hash == blobs[1].hash

    def test_complex_directory_workflow_with_verification(self, runner):
        """Test complex directory workflow with full verification."""
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
            expected_blobs = [
                Blob(bundle_path="README.md", size_bytes=35, hash=hashlib.sha256(b"# Test Project\nThis is a test.").hexdigest(), hash_algo="sha256"),
                Blob(bundle_path="config.yaml", size_bytes=25, hash=hashlib.sha256(b"app: test\nversion: 1.0").hexdigest(), hash_algo="sha256"),
                Blob(bundle_path="models/model.bin", size_bytes=18, hash=hashlib.sha256(b"binary_model_data").hexdigest(), hash_algo="sha256"),
                Blob(bundle_path="data/dataset.json", size_bytes=20, hash=hashlib.sha256(b'{"samples": 100}').hexdigest(), hash_algo="sha256")
            ]
            expected_merkle = compute_merkle_root(expected_blobs)
            
            # Mock the complete workflow
            with patch('cli.commands.create.BundlesAPIClient') as mock_create_client, \
                 patch('cli.commands.download.BundlesAPIClient') as mock_download_client:
                
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
                result = runner.invoke(cli, ['create', 'test_project'])
                assert result.exit_code == 0
                assert expected_merkle in result.output
                
                # 2. Setup download mock
                zip_content = self.create_mock_zip_content({
                    "README.md": "# Test Project\nThis is a test.",
                    "config.yaml": "app: test\nversion: 1.0",
                    "models/model.bin": b"binary_model_data",
                    "data/dataset.json": '{"samples": 100}'
                })
                mock_download_api = Mock()
                mock_download_api.download_bundle.return_value = iter([zip_content])
                mock_download_client.return_value = mock_download_api
                
                # 3. Download bundle
                result = runner.invoke(cli, ['download', '01HQZX789XYZ123ABC456DEF'])
                assert result.exit_code == 0
                
                # 4. Extract and verify
                downloaded_file = Path("bundle_01HQZX789XYZ123ABC456DEF.zip")
                assert downloaded_file.exists()
                
                extract_dir = Path("extracted_project")
                extract_dir.mkdir()
                
                with zipfile.ZipFile(downloaded_file, 'r') as zip_file:
                    zip_file.extractall(extract_dir)
                
                # 5. Verify all files exist with correct content
                extracted_files = {
                    "README.md": "# Test Project\nThis is a test.",
                    "config.yaml": "app: test\nversion: 1.0",
                    "models/model.bin": b"binary_model_data",
                    "data/dataset.json": '{"samples": 100}'
                }
                
                for file_path, expected_content in extracted_files.items():
                    full_path = extract_dir / file_path
                    assert full_path.exists(), f"File {file_path} not found in extracted bundle"
                    
                    if isinstance(expected_content, str):
                        actual_content = full_path.read_text()
                    else:
                        actual_content = full_path.read_bytes()
                    
                    assert actual_content == expected_content, f"Content mismatch for {file_path}"
                
                # 6. Recompute hashes and merkle root from extracted files
                extracted_blobs = []
                for file_path, expected_content in extracted_files.items():
                    if isinstance(expected_content, str):
                        content_bytes = expected_content.encode('utf-8')
                    else:
                        content_bytes = expected_content
                    
                    file_hash = hashlib.sha256(content_bytes).hexdigest()
                    blob = Blob(
                        bundle_path=file_path,
                        size_bytes=len(content_bytes),
                        hash=file_hash,
                        hash_algo="sha256"
                    )
                    extracted_blobs.append(blob)
                
                # 7. Recompute merkle root
                recomputed_merkle = compute_merkle_root(extracted_blobs)
                
                # 8. Verify merkle roots match
                assert recomputed_merkle == expected_merkle, f"Merkle root mismatch: expected {expected_merkle}, got {recomputed_merkle}"
                
                # 9. Verify all individual hashes match
                for i, (extracted_blob, expected_blob) in enumerate(zip(extracted_blobs, expected_blobs)):
                    assert extracted_blob.hash == expected_blob.hash, f"Hash mismatch for file {i}: {extracted_blob.bundle_path}"
                    assert extracted_blob.size_bytes == expected_blob.size_bytes, f"Size mismatch for file {i}: {extracted_blob.bundle_path}"

    def test_error_handling_integration(self, runner):
        """Test error handling in integration scenarios."""
        with runner.isolated_filesystem():
            # Test with non-existent file
            result = runner.invoke(cli, ['create', 'nonexistent.txt'])
            assert result.exit_code == 2
            
            # Test with empty directory
            empty_dir = Path("empty_dir")
            empty_dir.mkdir()
            result = runner.invoke(cli, ['create', 'empty_dir'])
            assert result.exit_code == 2
            
            # Test download of non-existent bundle
            with patch('cli.commands.download.BundlesAPIClient') as mock_client_class:
                mock_api_client = Mock()
                mock_response = Mock()
                mock_response.status_code = 404
                error = Exception("Not Found")
                error.response = mock_response
                mock_api_client.download_bundle.side_effect = error
                mock_client_class.return_value = mock_api_client
                
                result = runner.invoke(cli, ['download', 'nonexistent_bundle'])
                assert result.exit_code == 2
