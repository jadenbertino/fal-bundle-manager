"""Storage utility functions for blob operations."""

from pathlib import Path
from api.config import get_blobs_dir


def get_blob_path(hash_str: str) -> Path:
    """
    Get the file system path for a blob given its hash.

    Args:
        hash_str: The SHA-256 hash (64-char lowercase hex)

    Returns:
        Path to the blob file
    """
    # Use fanout structure: .data/blobs/{aa}/{bb}/{full_hash}
    return get_blobs_dir() / hash_str[:2] / hash_str[2:4] / hash_str


def blob_exists(hash_str: str) -> bool:
    """
    Check if a blob exists in storage.

    Args:
        hash_str: The SHA-256 hash

    Returns:
        True if blob exists, False otherwise
    """
    return get_blob_path(hash_str).exists()
