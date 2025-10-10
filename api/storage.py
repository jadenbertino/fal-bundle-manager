"""Storage utility functions for blob operations."""

from pathlib import Path
from shared.config import BLOBS_DIR


def to_blob_path(hash_str: str) -> Path:
    """
    Get the file system path for a blob given its hash.
    """
    # Use fanout structure: .data/blobs/{aa}/{bb}/{full_hash}
    return BLOBS_DIR / hash_str[:2] / hash_str[2:4] / hash_str


def blob_exists(hash_str: str) -> bool:
    """
    Check if a blob exists in storage.
    """
    return to_blob_path(hash_str).exists()


