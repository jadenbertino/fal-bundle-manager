"""Logging configuration for the application."""

import logging
import sys

# Create a logger instance
logger = logging.getLogger("fal-bundles")

# Configure default handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)


def get_logger(name: str = "fal-bundles") -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (defaults to 'fal-bundles')

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
