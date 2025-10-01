"""API configuration."""

import os
from pathlib import Path


def get_data_dir() -> Path:
    """Get the data directory path (dynamically reads from env)."""
    return Path(os.getenv("DATA_DIR", ".data"))


def get_blobs_dir() -> Path:
    """Get the blobs directory path."""
    return get_data_dir() / "blobs"


def get_bundles_dir() -> Path:
    """Get the bundles directory path."""
    return get_data_dir() / "bundles"


def get_tmp_dir() -> Path:
    """Get the temp directory path."""
    return get_data_dir() / "tmp"


# Maximum upload size
ONE_GB = 1024 * 1024 * 1024
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", ONE_GB))


def ensure_directories():
    """Create necessary directories if they don't exist."""
    get_blobs_dir().mkdir(parents=True, exist_ok=True)
    get_bundles_dir().mkdir(parents=True, exist_ok=True)
    get_tmp_dir().mkdir(parents=True, exist_ok=True)
