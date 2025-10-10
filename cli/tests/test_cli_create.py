"""
Tests for CLI create command using CliRunner.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import requests
from cli.__main__ import cli
from shared.api_contracts.preflight import PreflightResponse
from shared.api_contracts.create_bundle import CreateBundleResponse
from cli.tests.fixtures import get_fixture_path
from shared.merkle import compute_merkle_root
from shared.types import Blob
from cli.core.file_discovery import discover_files
from cli.core.hashing import hash_file_sha256
import hashlib


DEFAULT_BUNDLE_ID = "test-bundle-123"
DEFAULT_CREATED_AT = "2024-01-01T00:00:00Z"
DEFAULT_MERKLE = "d" * 64


def expected_create_output(
    bundle_id: str = DEFAULT_BUNDLE_ID,
    created_at: str = DEFAULT_CREATED_AT,
    merkle: str = DEFAULT_MERKLE,
) -> str:
    """Construct the expected multi-line success message."""
    return (
        "Created bundle:\n"
        f"- ID: {bundle_id}\n"
        f"- Created: {created_at}\n"
        f"- Merkle: {merkle}"
    )


@pytest.fixture
def runner():
    """Create a CliRunner instance."""
    return CliRunner()


def compute_real_merkle_root(input_paths):
    """Compute the real merkle root for given input paths using actual file discovery."""
    discovered = discover_files([str(p) for p in input_paths])
    blobs = []
    for file in discovered:
        file_hash = hash_file_sha256(file.absolute_path)
        blob = Blob(
            bundle_path=file.relative_path,
            size_bytes=file.size_bytes,
            hash=file_hash,
            hash_algo="sha256"
        )
        blobs.append(blob)
    return compute_merkle_root(blobs)

@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    mock = Mock()
    mock.preflight.return_value = PreflightResponse(missing=[])
    mock.upload_blob.return_value = True
    # We'll set the merkle root dynamically based on real files
    mock.create_bundle.return_value = CreateBundleResponse(
        id=DEFAULT_BUNDLE_ID,
        created_at=DEFAULT_CREATED_AT,
        merkle_root=DEFAULT_MERKLE,  # Will be overridden
    )
    return mock


# ============================================================================
# 1. SUCCESS CASES
# ============================================================================

class TestCreateSuccess:
    """Test successful create command scenarios."""

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_single_file(self, mock_client_class, runner, mock_api_client):
        """Test create with a single file."""
        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        
        # Compute real merkle root
        real_merkle = compute_real_merkle_root([fixture_file])
        mock_api_client.create_bundle.return_value = CreateBundleResponse(
            id=DEFAULT_BUNDLE_ID,
            created_at=DEFAULT_CREATED_AT,
            merkle_root=real_merkle,
        )
        mock_client_class.return_value = mock_api_client

        # Run command with real fixture file
        result = runner.invoke(cli, ['create', str(fixture_file)])

        # Assertions
        assert result.exit_code == 0
        expected = expected_create_output(merkle=real_merkle)
        assert result.output.strip() == expected
        assert mock_api_client.preflight.called
        assert mock_api_client.create_bundle.called

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_single_directory(self, mock_client_class, runner, mock_api_client):
        """Test create with a directory."""
        # Use real fixture directory
        fixture_dir = get_fixture_path("test_dir")

        # Compute real merkle root using the same logic as the CLI
        real_merkle = compute_real_merkle_root([fixture_dir])
        mock_api_client.create_bundle.return_value = CreateBundleResponse(
            id=DEFAULT_BUNDLE_ID,
            created_at=DEFAULT_CREATED_AT,
            merkle_root=real_merkle,
        )
        mock_client_class.return_value = mock_api_client

        # Run command with real fixture directory
        result = runner.invoke(cli, ['create', str(fixture_dir)])

        # Assertions
        assert result.exit_code == 0
        expected = expected_create_output(merkle=real_merkle)
        assert result.output.strip() == expected

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_multiple_paths(self, mock_client_class, runner, mock_api_client):
        """Test create with multiple paths (files and directories)."""
        # Use real fixture files
        file1 = get_fixture_path("file1")
        file2 = get_fixture_path("file2")
        configs_dir = get_fixture_path("configs")

        # Compute real merkle root using the same logic as the CLI
        real_merkle = compute_real_merkle_root([file1, configs_dir, file2])
        mock_api_client.create_bundle.return_value = CreateBundleResponse(
            id=DEFAULT_BUNDLE_ID,
            created_at=DEFAULT_CREATED_AT,
            merkle_root=real_merkle,
        )
        mock_client_class.return_value = mock_api_client

        # Run command with real fixture files
        result = runner.invoke(cli, ['create', str(file1), str(configs_dir), str(file2)])

        # Assertions
        assert result.exit_code == 0
        expected = expected_create_output(merkle=real_merkle)
        assert result.output.strip() == expected

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_outputs_bundle_id(self, mock_client_class, runner, mock_api_client):
        """Test that create outputs the bundle ID."""
        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        
        # Compute real merkle root
        real_merkle = compute_real_merkle_root([fixture_file])
        mock_api_client.create_bundle.return_value = CreateBundleResponse(
            id=DEFAULT_BUNDLE_ID,
            created_at=DEFAULT_CREATED_AT,
            merkle_root=real_merkle,
        )
        mock_client_class.return_value = mock_api_client

        result = runner.invoke(cli, ['create', str(fixture_file)])

        # Check output format
        expected = expected_create_output(merkle=real_merkle)
        assert result.output.strip() == expected


# ============================================================================
# 2. ERROR CASES - EXIT CODE 2 (Invalid/Missing Paths)
# ============================================================================

class TestCreateErrors:
    """Test error scenarios for create command."""

    def test_create_with_nonexistent_path(self, runner):
        """Test create with a non-existent path."""
        result = runner.invoke(cli, ['create', 'nonexistent.txt'])

        # Click validates path existence before calling function
        assert result.exit_code == 2
        assert 'does not exist' in result.output.lower() or 'nonexistent' in result.output.lower()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_empty_directory(self, mock_client_class, runner, mock_api_client):
        """Test create with an empty directory."""
        # Use real empty directory fixture
        empty_dir = get_fixture_path("empty_dir")
        mock_client_class.return_value = mock_api_client

        result = runner.invoke(cli, ['create', str(empty_dir)])

        # Should fail with exit code 2
        assert result.exit_code == 2
        assert 'no files' in result.output.lower() or 'error' in result.output.lower()

    def test_create_with_no_arguments(self, runner):
        """Test create with no arguments."""
        result = runner.invoke(cli, ['create'])

        # Should show error about missing arguments
        assert result.exit_code == 2
        assert 'missing argument' in result.output.lower() or 'required' in result.output.lower()


# ============================================================================
# 3. ERROR CASES - EXIT CODE 4 (Network/IO Errors)
# ============================================================================

class TestCreateNetworkErrors:
    """Test network error scenarios."""

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_connection_error(self, mock_client_class, runner):
        """Test create with connection error."""
        mock_client = Mock()
        mock_client.preflight.side_effect = requests.exceptions.ConnectionError("Connection failed")
        mock_client_class.return_value = mock_client

        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        result = runner.invoke(cli, ['create', str(fixture_file)])

        assert result.exit_code == 4
        assert 'failed to connect' in result.output.lower() or 'connection' in result.output.lower()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_timeout_error(self, mock_client_class, runner):
        """Test create with timeout error."""
        mock_client = Mock()
        mock_client.preflight.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_client_class.return_value = mock_client

        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        result = runner.invoke(cli, ['create', str(fixture_file)])

        assert result.exit_code == 4
        assert 'timeout' in result.output.lower() or 'timed out' in result.output.lower()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_http_error(self, mock_client_class, runner):
        """Test create with HTTP error."""
        mock_client = Mock()
        mock_client.preflight.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_client_class.return_value = mock_client

        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        result = runner.invoke(cli, ['create', str(fixture_file)])

        assert result.exit_code == 4
        assert 'error' in result.output.lower()


# ============================================================================
# 4. OUTPUT FORMAT TESTS
# ============================================================================

class TestCreateOutputFormat:
    """Test output formatting."""

    @patch('cli.commands.create.BundlesAPIClient')
    def test_success_message_format(self, mock_client_class, runner, mock_api_client):
        """Test that success message has correct format."""
        # Use real fixture file
        fixture_file = get_fixture_path("single_file")
        
        # Compute real merkle root
        real_merkle = compute_real_merkle_root([fixture_file])
        mock_api_client.create_bundle.return_value = CreateBundleResponse(
            id=DEFAULT_BUNDLE_ID,
            created_at=DEFAULT_CREATED_AT,
            merkle_root=real_merkle,
        )
        mock_client_class.return_value = mock_api_client

        result = runner.invoke(cli, ['create', str(fixture_file)])

        # Check exact format
        assert result.exit_code == 0
        expected = expected_create_output(merkle=real_merkle)
        assert result.output.strip() == expected


# ============================================================================
# 5. HELP/USAGE TESTS
# ============================================================================

class TestCreateHelp:
    """Test help and usage information."""

    def test_create_help_flag(self, runner):
        """Test --help flag."""
        result = runner.invoke(cli, ['create', '--help'])

        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'PATHS' in result.output or 'paths' in result.output

    def test_help_describes_parameters(self, runner):
        """Test that help describes parameters correctly."""
        result = runner.invoke(cli, ['create', '--help'])

        # Should mention paths and their purpose
        assert 'paths' in result.output.lower()
        assert 'file' in result.output.lower() or 'director' in result.output.lower()
