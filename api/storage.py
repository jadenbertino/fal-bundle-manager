"""Storage utility functions for blob operations."""

import hashlib
from pathlib import Path
from shared.config import get_blobs_dir


def to_blob_path(hash_str: str) -> Path:
    """
    Get the file system path for a blob given its hash.
    """
    # Use fanout structure: .data/blobs/{aa}/{bb}/{full_hash}
    return get_blobs_dir() / hash_str[:2] / hash_str[2:4] / hash_str


def blob_exists(hash_str: str) -> bool:
    """
    Check if a blob exists in storage.
    """
    return to_blob_path(hash_str).exists()


def calculate_sha256(content: bytes) -> str:
    """
    Calculate SHA-256 hash of content.

    Use this for small in-memory content (tests, CLI).

    For large files or streaming I/O
    (e.g. receiving a file from a HTTP request),
    use incremental hashing with hasher.update() instead.
    """
    return hashlib.sha256(content).hexdigest()
