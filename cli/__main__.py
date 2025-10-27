"""CLI entry point."""

import click

from cli.commands.create import create
from cli.commands.download import download
from cli.commands.list import list_cmd


@click.group()
def cli():
    """fal-bundles CLI - Manage resource bundles."""
    pass


# Register commands
cli.add_command(create)
cli.add_command(list_cmd, name="list")
cli.add_command(download)


if __name__ == "__main__":
    cli()
