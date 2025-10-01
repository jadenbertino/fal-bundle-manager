"""CLI entry point."""

import click
from cli.commands.create import create


@click.group()
def cli():
    """fal-bundles CLI - Manage resource bundles."""
    pass


# Register commands
cli.add_command(create)


if __name__ == '__main__':
    cli()
