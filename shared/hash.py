"""Hash utility functions for content and file operations."""

import hashlib
from pathlib import Path


def hash_bytes(content: bytes) -> str:
    """
    Calculate SHA-256 hash of content.

    Use this for small in-memory content (tests, CLI).

    For large files or streaming I/O
    (e.g. receiving a file from a HTTP request),
    use incremental hashing with hasher.update() instead.
    """
    return hashlib.sha256(content).hexdigest()


def hash_file_content(file_path: Path, chunk_size: int = 65536) -> str:
    """
    Calculate SHA-256 hash of a file using streaming to support large files.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 64KB)

    Returns:
        Lowercase hexadecimal SHA-256 hash (64 characters)
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()
