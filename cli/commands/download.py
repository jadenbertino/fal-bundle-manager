"""Download command implementation."""

import sys
import os
import tempfile
import click
import requests
from pathlib import Path
from typing import Iterator
from pydantic import ValidationError
from cli.client import BundlesAPIClient
from shared.config import API_URL, API_TIMEOUT
from shared.api_contracts.download_bundle import DownloadBundleRequest

@click.command()
@click.argument('bundle_id', required=True)
@click.option('--format', default='zip', help='Archive format (default: zip)')
@click.option('--api-url', default=API_URL, help='API server URL')
def download(bundle_id, format, api_url):
    """
    Download a bundle as an archive file.

    BUNDLE_ID: The ID of the bundle to download.
    """
    try:
        # Validate format before making any requests
        validate_format(format)

        # Generate output filename
        filename = generate_filename(bundle_id, format)
        output_path = Path.cwd() / filename
        final_path = handle_file_conflict(output_path)
        if final_path != output_path:
            click.echo(f"File {output_path.name} exists, saving as {final_path.name}", err=True)

        # Create temporary file for atomic write
        temp_fd, temp_path = tempfile.mkstemp(
            dir=final_path.parent,
            prefix=f".{final_path.name}.",
            suffix=".tmp"
        )
        os.close(temp_fd)  # Close the file descriptor, we'll open it properly later
        temp_path = Path(temp_path)

        try:
            # Download bundle with streaming
            api_client = BundlesAPIClient(base_url=api_url, timeout=API_TIMEOUT)
            chunks = api_client.download_bundle(bundle_id, format)
            total_bytes = download_with_progress(chunks, temp_path, show_progress=True)
            temp_path.rename(final_path)
            click.echo(f"Downloaded {final_path.name}")
            sys.exit(0)

        except Exception:
            # Clean up temporary file on any error
            if temp_path.exists():
                temp_path.unlink()
            raise

    except ValueError as e:
        # Format validation error
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            click.echo(f"Error: Bundle {bundle_id} not found", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: HTTP error: {e}", err=True)
            sys.exit(4)

    except requests.exceptions.ConnectionError:
        click.echo(f"Error: Failed to connect to API server at {api_url}", err=True)
        sys.exit(4)

    except requests.exceptions.Timeout:
        click.echo(f"Error: Request timed out", err=True)
        sys.exit(4)

    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Network error: {e}", err=True)
        sys.exit(4)

    except IOError as e:
        click.echo(f"Error: Failed to write file: {e}", err=True)
        sys.exit(4)

    except Exception as e:
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(4)



def generate_filename(bundle_id: str, format: str) -> str:
    """Generate output filename for downloaded bundle."""
    ext = get_file_extension(format)
    return f"bundle_{bundle_id}.{ext}"

def get_file_extension(format: str) -> str:
    """Get file extension for archive format."""
    format_map = {
        "zip": "zip",
    }
    return format_map.get(format, format)



def handle_file_conflict(filepath: Path) -> Path:
    """
    Handle file conflicts by auto-renaming.
    """
    if not filepath.exists():
        return filepath

    # Auto-rename: bundle_id.zip -> bundle_id.1.zip -> bundle_id.2.zip, etc.
    base = filepath.stem
    ext = filepath.suffix
    parent = filepath.parent

    counter = 1
    while True:
        new_path = parent / f"{base}.{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1


def download_with_progress(chunks: Iterator[bytes], output_path: Path, show_progress: bool = True) -> int:
    """
    Download streaming chunks to file with progress indication.

    Args:
        chunks: Iterator of byte chunks
        output_path: Path to write the file
        show_progress: Whether to show progress indication

    Returns:
        Total bytes downloaded

    Raises:
        IOError: If write fails (disk full, permissions, etc.)
    """
    total_bytes = 0

    try:
        with open(output_path, 'wb') as f:
            for chunk in chunks:
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
                    total_bytes += len(chunk)

                    if show_progress and total_bytes % (1024 * 1024) == 0:  # Update every MB
                        mb = total_bytes / (1024 * 1024)
                        click.echo(f"\rDownloading... {mb:.1f} MB", nl=False, err=True)

        if show_progress and total_bytes > 0:
            click.echo(err=True)  # Clear progress line

        return total_bytes

    except IOError as e:
        # Clean up partial file on error
        if output_path.exists():
            output_path.unlink()
        raise


def validate_format(format: str) -> None:
    """
    Validate archive format.

    Args:
        format: Archive format string

    Raises:
        ValueError: If format is unsupported
    """
    try:
        DownloadBundleRequest(format=format)
    except ValidationError:
        raise ValueError(f"Unsupported format: {format}")

