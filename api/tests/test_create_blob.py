import requests
from pathlib import Path
from api.storage import calculate_sha256
from api.tests.helpers import BASE_URL
from shared.config import get_blobs_dir


def test_create_blob_new():
    """Test creating a new blob."""
    import time
    content = f"test content for new blob {time.time()}".encode()
    hash_val = calculate_sha256(content)

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["hash"] == hash_val

    # Verify blob exists in storage
    blob_path = get_blobs_dir() / hash_val[:2] / hash_val[2:4] / hash_val
    assert blob_path.exists()
    assert blob_path.read_bytes() == content

    # Cleanup
    blob_path.unlink()


def test_create_blob_idempotent():
    """Test that uploading same blob twice is idempotent."""
    import time
    content = f"idempotent test content {time.time()}".encode()
    hash_val = calculate_sha256(content)

    # First upload
    response1 = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response1.status_code == 201

    # Second upload - should return 200 (already exists)
    response2 = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response2.status_code == 200
    data = response2.json()
    assert data["status"] == "exists"
    assert data["hash"] == hash_val

    # Cleanup
    blob_path = get_blobs_dir() / hash_val[:2] / hash_val[2:4] / hash_val
    blob_path.unlink()


def test_create_blob_hash_mismatch():
    """Test that hash mismatch returns 409."""
    content = b"actual content"
    wrong_hash = "a" * 64  # Wrong hash

    response = requests.put(
        f"{BASE_URL}/blobs/{wrong_hash}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 409

    # Verify blob was not stored
    blob_path = get_blobs_dir() / wrong_hash[:2] / wrong_hash[2:4] / wrong_hash
    assert not blob_path.exists()


def test_create_blob_invalid_hash_length():
    """Test that invalid hash length returns 400."""
    content = b"test content"
    invalid_hash = "abc123"  # Too short

    response = requests.put(
        f"{BASE_URL}/blobs/{invalid_hash}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 422  # FastAPI validation error


def test_create_blob_invalid_hash_chars():
    """Test that invalid hash characters returns 400."""
    content = b"test content"
    invalid_hash = "Z" * 64  # Invalid characters

    response = requests.put(
        f"{BASE_URL}/blobs/{invalid_hash}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 422


def test_create_blob_uppercase_hash():
    """Test that uppercase hash is rejected."""
    content = b"test content"
    hash_val = calculate_sha256(content).upper()  # Uppercase

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 422


def test_create_blob_negative_size():
    """Test that negative size returns 422."""
    content = b"test content"
    hash_val = calculate_sha256(content)

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": -100},
        data=content
    )
    assert response.status_code == 422


def test_create_blob_exceeds_max_size():
    """Test that file exceeding max size returns 413."""
    content = b"test content"
    hash_val = calculate_sha256(content)

    # Set size_bytes to exceed 1GB limit
    too_large = 2 * 1024 * 1024 * 1024  # 2GB

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": too_large},
        data=content
    )
    assert response.status_code == 413


def test_create_blob_empty_file():
    """Test uploading empty file."""
    content = b""
    hash_val = calculate_sha256(content)

    # Delete blob if it exists from previous test
    blob_path = get_blobs_dir() / hash_val[:2] / hash_val[2:4] / hash_val
    if blob_path.exists():
        blob_path.unlink()

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": 0},
        data=content
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["hash"] == hash_val

    # Cleanup
    assert blob_path.exists()
    blob_path.unlink()


def test_create_blob_large_file():
    """Test uploading a larger file (streaming test)."""
    # Create 1MB content
    content = b"x" * (1024 * 1024)
    hash_val = calculate_sha256(content)

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["hash"] == hash_val

    # Verify content is correct
    blob_path = get_blobs_dir() / hash_val[:2] / hash_val[2:4] / hash_val
    assert blob_path.exists()
    assert blob_path.read_bytes() == content

    # Cleanup
    blob_path.unlink()


def test_create_blob_fanout_structure():
    """Test that blobs are stored with proper fanout directory structure."""
    content = b"fanout test"
    hash_val = calculate_sha256(content)

    response = requests.put(
        f"{BASE_URL}/blobs/{hash_val}",
        params={"size_bytes": len(content)},
        data=content
    )
    assert response.status_code == 201

    # Verify fanout structure: data/blobs/{aa}/{bb}/{full_hash}
    expected_path = get_blobs_dir() / hash_val[:2] / hash_val[2:4] / hash_val
    assert expected_path.exists()
    assert expected_path.parent.parent.name == hash_val[:2]
    assert expected_path.parent.name == hash_val[2:4]

    # Cleanup
    expected_path.unlink()
