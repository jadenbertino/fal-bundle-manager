"""File discovery logic for bundle creation."""

import os
from pathlib import Path
from typing import NamedTuple


class DiscoveredFile(NamedTuple):
    """Represents a discovered file with its metadata."""

    absolute_path: Path
    relative_path: str  # Relative path to use in bundle
    size_bytes: int


def discover_files(
    input_paths: list[str], base_dir: str | None = None
) -> list[DiscoveredFile]:
    """
    Discover all files from the given input paths.

    Args:
        input_paths: List of file or directory paths (relative or absolute)
        base_dir: Base directory for calculating relative paths (defaults to common parent)

    Returns:
        List of discovered files with absolute paths and relative paths for bundle

    Raises:
        FileNotFoundError: If any input path doesn't exist
        ValueError: If no files are discovered
    """
    discovered = []

    # Convert to absolute paths
    abs_paths = [Path(p).resolve() for p in input_paths]

    # Validate all paths exist
    for path in abs_paths:
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

    # Determine base directory if not provided
    if base_dir is None:
        if len(abs_paths) == 1 and abs_paths[0].is_file():
            # Single file: use parent directory as base
            base_dir_path = abs_paths[0].parent
        elif len(abs_paths) == 1 and abs_paths[0].is_dir():
            # Single directory: use parent directory as base to preserve dir name in paths
            base_dir_path = abs_paths[0].parent
        else:
            # Multiple paths or directories: use common parent
            base_dir_path = _find_common_parent(abs_paths)
    else:
        base_dir_path = Path(base_dir).resolve()

    # Walk through each input path
    for path in abs_paths:
        if path.is_file():
            discovered.append(_create_discovered_file(path, base_dir_path))
        elif path.is_dir():
            # Recursively walk directory
            for root, _, files in os.walk(path):
                for filename in files:
                    file_path = Path(root) / filename
                    # Skip symlinks for now (design decision)
                    if not file_path.is_symlink():
                        discovered.append(
                            _create_discovered_file(file_path, base_dir_path)
                        )

    if not discovered:
        raise ValueError("No files discovered from input paths")

    return discovered


def _find_common_parent(paths: list[Path]) -> Path:
    """Find the common parent directory of multiple paths."""
    if len(paths) == 1:
        path = paths[0]
        return path.parent if path.is_file() else path

    # Get all parent parts for each path
    all_parts = [list(p.parents)[::-1] + [p] for p in paths]

    # Find common prefix
    common = []
    for parts in zip(*all_parts, strict=False):
        if len(set(parts)) == 1:
            common.append(parts[0])
        else:
            break

    return common[-1] if common else Path("/")


def _create_discovered_file(file_path: Path, base_dir: Path) -> DiscoveredFile:
    """Create a DiscoveredFile from a file path and base directory."""
    # Calculate relative path from base_dir
    try:
        rel_path = file_path.relative_to(base_dir)
    except ValueError:
        # file_path is not relative to base_dir, use just the filename
        rel_path = Path(file_path.name)

    # Convert to POSIX-style path (forward slashes) for cross-platform compatibility
    bundle_path = rel_path.as_posix()

    # Get file size
    size_bytes = file_path.stat().st_size

    return DiscoveredFile(
        absolute_path=file_path, relative_path=bundle_path, size_bytes=size_bytes
    )
