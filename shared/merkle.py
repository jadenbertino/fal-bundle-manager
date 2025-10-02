"""Merkle tree utilities shared across components."""

from __future__ import annotations

import hashlib
from typing import Iterable, Protocol, runtime_checkable


@runtime_checkable
class _BlobLike(Protocol):
    """Protocol for the minimal fields required from a blob."""

    bundle_path: str
    hash: str


def _normalize_blob(blob: _BlobLike | dict) -> tuple[str, str]:
    """Extract path and hash from blob-like inputs."""

    if isinstance(blob, dict):
        return blob["bundle_path"], blob["hash"]
    return blob.bundle_path, blob.hash


def compute_merkle_root(blobs: Iterable[_BlobLike | dict]) -> str:
    """Compute a deterministic Merkle root for bundle files.

    Leaves are created by hashing the bundle path and content hash together.
    The tree is built by pairing adjacent leaves (duplicating the final leaf
    when necessary) and hashing their concatenated digests until a single root
    remains. For empty collections, the root is the SHA-256 of an empty byte
    string.
    """

    leaf_digests: list[bytes] = []
    for bundle_path, hash_str in sorted(
        (_normalize_blob(blob) for blob in blobs), key=lambda item: item[0]
    ):
        leaf_input = f"{bundle_path}:{hash_str}".encode("utf-8")
        leaf_digests.append(hashlib.sha256(leaf_input).digest())

    if not leaf_digests:
        return hashlib.sha256(b"").hexdigest()

    while len(leaf_digests) > 1:
        if len(leaf_digests) % 2 == 1:
            leaf_digests.append(leaf_digests[-1])

        leaf_digests = [
            hashlib.sha256(leaf_digests[i] + leaf_digests[i + 1]).digest()
            for i in range(0, len(leaf_digests), 2)
        ]

    return leaf_digests[0].hex()
