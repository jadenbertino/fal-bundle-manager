"""Shared configuration for API and CLI."""

import os
from pathlib import Path

# ============================================================================
# API Server Configuration
# ============================================================================


def get_data_dir() -> Path:
    """Get the data directory path (dynamically reads from env)."""
    return Path(os.getenv("DATA_DIR", "api/.data"))


def get_blobs_dir() -> Path:
    """Get the blobs directory path."""
    return get_data_dir() / "blobs"


def get_bundles_dir() -> Path:
    """Get the bundles directory path."""
    return get_data_dir() / "bundles"


def get_bundle_manifests_dir() -> Path:
    """Get the bundle manifests directory path."""
    return get_bundles_dir() / "manifests"


def get_bundle_summaries_dir() -> Path:
    """Get the bundle summaries directory path."""
    return get_bundles_dir() / "summaries"


def get_tmp_dir() -> Path:
    """Get the temp directory path."""
    return get_data_dir() / "tmp"


def ensure_directories():
    """Create necessary directories if they don't exist."""
    paths = [
        get_blobs_dir(),
        get_bundle_manifests_dir(),
        get_bundle_summaries_dir(),
        get_tmp_dir(),
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


# Maximum upload size
ONE_GB = 1024 * 1024 * 1024
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", ONE_GB))


# ============================================================================
# CLI Configuration
# ============================================================================

API_URL = os.getenv("FAL_BUNDLES_API_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("FAL_BUNDLES_TIMEOUT", "300"))
