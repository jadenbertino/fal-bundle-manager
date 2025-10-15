"""List command implementation.

Pseudo-code tests:
- test_list_bundles_success():
    GIVEN server returns list of 3 bundles
    WHEN user runs 'list' command
    THEN should display formatted table with ID, Files, Total Size, Created
    AND should exit with code 0

- test_list_bundles_empty():
    GIVEN server returns empty list
    WHEN user runs 'list' command
    THEN should display "No bundles found" message
    AND should exit with code 0

- test_list_bundles_network_error():
    GIVEN server is unreachable
    WHEN user runs 'list' command
    THEN should display connection error message
    AND should exit with code 4

- test_list_bundles_formats_sizes():
    GIVEN bundles with various sizes (bytes, KB, MB, GB)
    WHEN user runs 'list' command
    THEN should format sizes as human-readable (e.g., "12.3 KB", "45.6 MB")

- test_list_bundles_formats_dates():
    GIVEN bundles with ISO timestamps
    WHEN user runs 'list' command
    THEN should format dates as readable (e.g., "2023-12-25 10:30:00")

- test_list_bundles_sorted_by_date():
    GIVEN server returns bundles in mixed order
    WHEN user runs 'list' command
    THEN should display bundles sorted by created_at descending (newest first)
"""

import sys
import click
import requests
from cli.client import BundlesAPIClient
from shared.config import API_URL, API_TIMEOUT


@click.command()
@click.option('--api-url', default=API_URL, help='API server URL')
def list_cmd(api_url):
    """
    List all available bundles.

    Displays bundles in a table with ID, file count, total size, creation date, and Merkle root (first 10 chars).
    """
    try:
        # Initialize API client
        api_client = BundlesAPIClient(base_url=api_url, timeout=API_TIMEOUT)

        # Fetch bundle list
        response = api_client.list_bundles()

        # Handle empty state
        if not response.bundles:
            click.echo("No bundles found. Use 'create' command to add bundles.")
            sys.exit(0)

        # Format and display table
        header = f"{'ID':<28} | {'Files':>6} | {'Total Size':>12} | {'Created':<20}"
        click.echo(header)
        click.echo("-" * len(header))

        for bundle in response.bundles:
            size_str = format_size(bundle.total_bytes)
            date_str = format_timestamp(bundle.created_at)
            click.echo(
                f"{bundle.id:<28} | {bundle.file_count:>6} | {size_str:>12} | {date_str:<20}"
            )

        sys.exit(0)

    except requests.exceptions.ConnectionError:
        click.echo(f"Error: Failed to connect to API server at {api_url}", err=True)
        sys.exit(4)

    except requests.exceptions.Timeout:
        click.echo(f"Error: Request timed out", err=True)
        sys.exit(4)

    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Network error: {e}", err=True)
        sys.exit(4)

    except Exception as e:
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(4)


def format_size(bytes_count: int) -> str:
    """Format byte count as human-readable size."""
    if bytes_count < 1024:
        return f"{bytes_count:,} B"
    elif bytes_count < 1024 * 1024:
        kb = bytes_count / 1024
        return f"{kb:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        mb = bytes_count / (1024 * 1024)
        return f"{mb:.1f} MB"
    else:
        gb = bytes_count / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp as readable string."""
    # Simple format: "2023-12-25T10:30:00Z" -> "2023-12-25 10:30:00"
    return iso_timestamp.replace('T', ' ').replace('Z', '')

