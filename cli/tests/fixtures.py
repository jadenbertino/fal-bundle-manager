"""Test fixtures helper module."""

from pathlib import Path

# Path to test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "test_data"

# Commonly used fixture files
FIXTURE_FILES = {
    "file1": FIXTURES_DIR / "file1.txt",
    "file2": FIXTURES_DIR / "file2.txt",
    "empty": FIXTURES_DIR / "empty.txt",
    "large": FIXTURES_DIR / "large.bin",
    "readme": FIXTURES_DIR / "README.txt",
    "single_file": FIXTURES_DIR / "single_file.txt",
}

# Directories
FIXTURE_DIRS = {
    "configs": FIXTURES_DIR / "configs",
    "models": FIXTURES_DIR / "models",
    "nested": FIXTURES_DIR / "nested",
    "empty_dir": FIXTURES_DIR / "empty_dir",
    "test_dir": FIXTURES_DIR / "test_dir",
    "root": FIXTURES_DIR,
}


def get_fixture_path(name: str) -> Path:
    """Get path to a fixture file by name."""
    if name in FIXTURE_FILES:
        return FIXTURE_FILES[name]
    elif name in FIXTURE_DIRS:
        return FIXTURE_DIRS[name]
    else:
        return FIXTURES_DIR / name
