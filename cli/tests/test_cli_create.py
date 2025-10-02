"""
Tests for CLI create command using CliRunner.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import requests
from cli.__main__ import cli
from shared.api_contracts.preflight import PreflightResponse
from shared.api_contracts.create_bundle import BundleCreateResponse


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


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    mock = Mock()
    mock.preflight.return_value = PreflightResponse(missing=[])
    mock.upload_blob.return_value = True
    mock.create_bundle.return_value = BundleCreateResponse(
        id=DEFAULT_BUNDLE_ID,
        created_at=DEFAULT_CREATED_AT,
        merkle_root=DEFAULT_MERKLE,
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
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            # Create test file
            with open('test.txt', 'w') as f:
                f.write('hello world')

            # Run command
            result = runner.invoke(cli, ['create', 'test.txt'])

            # Assertions
            assert result.exit_code == 0
            expected = expected_create_output()
            assert result.output.strip() == expected
            assert mock_api_client.preflight.called
            assert mock_api_client.create_bundle.called

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_single_directory(self, mock_client_class, runner, mock_api_client):
        """Test create with a directory."""
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            # Create directory with files
            import os
            os.mkdir('my_dir')
            with open('my_dir/file1.txt', 'w') as f:
                f.write('content1')
            with open('my_dir/file2.txt', 'w') as f:
                f.write('content2')

            # Run command
            result = runner.invoke(cli, ['create', 'my_dir'])

            # Assertions
            assert result.exit_code == 0
            expected = expected_create_output()
            assert result.output.strip() == expected

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_multiple_paths(self, mock_client_class, runner, mock_api_client):
        """Test create with multiple paths (files and directories)."""
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            # Create files and directory
            with open('file1.txt', 'w') as f:
                f.write('content1')
            with open('file2.txt', 'w') as f:
                f.write('content2')
            import os
            os.mkdir('dir1')
            with open('dir1/file3.txt', 'w') as f:
                f.write('content3')

            # Run command
            result = runner.invoke(cli, ['create', 'file1.txt', 'dir1', 'file2.txt'])

            # Assertions
            assert result.exit_code == 0
            expected = expected_create_output()
            assert result.output.strip() == expected

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_outputs_bundle_id(self, mock_client_class, runner, mock_api_client):
        """Test that create outputs the bundle ID."""
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')

            result = runner.invoke(cli, ['create', 'test.txt'])

            # Check output format
            expected = expected_create_output()
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
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            import os
            os.mkdir('empty_dir')

            result = runner.invoke(cli, ['create', 'empty_dir'])

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

        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')

            result = runner.invoke(cli, ['create', 'test.txt'])

            assert result.exit_code == 4
            assert 'failed to connect' in result.output.lower() or 'connection' in result.output.lower()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_timeout_error(self, mock_client_class, runner):
        """Test create with timeout error."""
        mock_client = Mock()
        mock_client.preflight.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_client_class.return_value = mock_client

        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')

            result = runner.invoke(cli, ['create', 'test.txt'])

            assert result.exit_code == 4
            assert 'timeout' in result.output.lower() or 'timed out' in result.output.lower()

    @patch('cli.commands.create.BundlesAPIClient')
    def test_create_with_http_error(self, mock_client_class, runner):
        """Test create with HTTP error."""
        mock_client = Mock()
        mock_client.preflight.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_client_class.return_value = mock_client

        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')

            result = runner.invoke(cli, ['create', 'test.txt'])

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
        mock_client_class.return_value = mock_api_client

        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')

            result = runner.invoke(cli, ['create', 'test.txt'])

            # Check exact format
            assert result.exit_code == 0
            expected = expected_create_output()
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
