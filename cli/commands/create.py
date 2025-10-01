"""Create command implementation."""

import sys
import click
import requests
from pathlib import Path
from cli.client import BundlesAPIClient
from cli.core.bundler import create_bundle
from shared.config import API_URL, API_TIMEOUT


@click.command()
@click.argument('paths', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--api-url', default=API_URL, help='API server URL')
def create(paths, api_url):
    """
    Create a bundle from local files and directories.

    PATHS: One or more file or directory paths to include in the bundle.
    """
    try:
        # Convert paths to strings
        path_strings = [str(p) for p in paths]

        # Initialize API client
        api_client = BundlesAPIClient(base_url=api_url, timeout=API_TIMEOUT)

        # Create bundle
        response = create_bundle(path_strings, api_client)

        # Output success
        click.echo(f"Created bundle: {response.id}")
        sys.exit(0)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

    except requests.exceptions.ConnectionError as e:
        click.echo(f"Error: Failed to connect to API server at {api_url}", err=True)
        sys.exit(4)

    except requests.exceptions.Timeout as e:
        click.echo(f"Error: Request timed out", err=True)
        sys.exit(4)

    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Network error: {e}", err=True)
        sys.exit(4)

    except Exception as e:
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(4)
