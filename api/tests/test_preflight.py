import requests
from pathlib import Path


BASE_URL = "http://localhost:8000"


def test_preflight_empty_files():
    """Test preflight with empty files array."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={"files": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["missing"] == []


def test_preflight_all_missing():
    """Test preflight when all blobs are missing."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file1.txt",
                    "size_bytes": 100,
                    "hash": "a" * 64,
                    "hash_algo": "sha256"
                },
                {
                    "bundle_path": "file2.txt",
                    "size_bytes": 200,
                    "hash": "b" * 64,
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["missing"]) == 2
    assert "a" * 64 in data["missing"]
    assert "b" * 64 in data["missing"]


def test_preflight_invalid_hash_length():
    """Test preflight with invalid hash length."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file1.txt",
                    "size_bytes": 100,
                    "hash": "abc123",  # Too short
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422  # Validation error


def test_preflight_invalid_hash_chars():
    """Test preflight with invalid hash characters."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file1.txt",
                    "size_bytes": 100,
                    "hash": "Z" * 64,  # Invalid char
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_uppercase_hash():
    """Test preflight rejects uppercase hash."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file1.txt",
                    "size_bytes": 100,
                    "hash": "A" * 64,  # Uppercase
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_negative_size():
    """Test preflight with negative file size."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file1.txt",
                    "size_bytes": -100,
                    "hash": "a" * 64,
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_absolute_path():
    """Test preflight with absolute path."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "/absolute/path.txt",
                    "size_bytes": 100,
                    "hash": "a" * 64,
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_path_with_dotdot():
    """Test preflight with path containing '..'."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "../etc/passwd",
                    "size_bytes": 100,
                    "hash": "a" * 64,
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_duplicate_paths():
    """Test preflight with duplicate paths."""
    response = requests.post(
        f"{BASE_URL}/bundles/preflight",
        json={
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": 100,
                    "hash": "a" * 64,
                    "hash_algo": "sha256"
                },
                {
                    "bundle_path": "file.txt",  # Duplicate
                    "size_bytes": 200,
                    "hash": "b" * 64,
                    "hash_algo": "sha256"
                }
            ]
        }
    )
    assert response.status_code == 422


def test_preflight_some_existing():
    """Test preflight when some blobs exist."""
    # Create one blob that exists in the server's data directory
    existing_hash = "c" * 64
    data_dir = Path(".data")
    blob_path = data_dir / "blobs" / "cc" / "cc" / existing_hash
    blob_path.parent.mkdir(parents=True, exist_ok=True)
    blob_path.write_text("test content")

    try:
        response = requests.post(
            f"{BASE_URL}/bundles/preflight",
            json={
                "files": [
                    {
                        "bundle_path": "existing.txt",
                        "size_bytes": 100,
                        "hash": existing_hash,
                        "hash_algo": "sha256"
                    },
                    {
                        "bundle_path": "missing.txt",
                        "size_bytes": 200,
                        "hash": "d" * 64,
                        "hash_algo": "sha256"
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["missing"]) == 1
        assert "d" * 64 in data["missing"]
        assert existing_hash not in data["missing"]
    finally:
        # Cleanup
        if blob_path.exists():
            blob_path.unlink()
