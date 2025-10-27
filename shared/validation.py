"""Shared validation logic for paths and hashes."""


def validate_sha256_hash(hash_str: str) -> str:
    """
    Validate that a string is a valid SHA-256 hash.

    Args:
        hash_str: The hash string to validate

    Returns:
        The validated hash string (potentially modified in future)

    Raises:
        ValueError: If hash is not a valid 64-character lowercase hex string
    """
    if len(hash_str) != 64:
        raise ValueError(
            f"SHA-256 hash must be exactly 64 characters, got {len(hash_str)}"
        )

    if not all(c in "0123456789abcdef" for c in hash_str):
        raise ValueError("Hash must be lowercase hexadecimal (0-9, a-f)")

    return hash_str


def validate_relative_path(path: str) -> str:
    """
    Validate that a path is relative and safe.

    Args:
        path: The path to validate

    Returns:
        The validated path (potentially normalized in future)

    Raises:
        ValueError: If path is not relative or contains directory traversal
    """
    if path.startswith("/"):
        raise ValueError("Path must be relative (no leading '/')")

    if ".." in path.split("/"):
        raise ValueError("Path cannot contain '..' (directory traversal)")

    if not path:
        raise ValueError("Path cannot be empty")

    return path
