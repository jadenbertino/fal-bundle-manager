"""File hashing utilities."""

import hashlib
from pathlib import Path


def hash_file_sha256(file_path: Path, chunk_size: int = 65536) -> str:
    """
    Calculate SHA-256 hash of a file using streaming to support large files.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 64KB)

    Returns:
        Lowercase hexadecimal SHA-256 hash (64 characters)
    """
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()
