import requests
import json
from pathlib import Path
from api.tests.helpers import BASE_URL, create_blob


def test_create_bundle_simple():
    """Test creating a simple bundle with one file."""
    # Create a blob
    content = b"test file content"
    hash_val = create_blob(content)

    # Create bundle
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "test.txt",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "created_at" in data

    # Verify manifest file exists
    bundle_id = data["id"]
    manifest_path = Path(".data") / "bundles" / f"{bundle_id}.json"
    assert manifest_path.exists()

    # Verify manifest content
    manifest = json.loads(manifest_path.read_text())
    assert manifest["id"] == bundle_id
    assert manifest["hash_algo"] == "sha256"
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["hash"] == hash_val
    assert manifest["file_count"] == 1
    assert manifest["bytes"] == len(content)


def test_create_bundle_multiple_files():
    """Test creating a bundle with multiple files."""
    # Create multiple blobs
    files_data = [
        (b"file 1 content", "file1.txt"),
        (b"file 2 content with more data", "dir/file2.txt"),
        (b"file 3", "dir/subdir/file3.txt"),
    ]

    files_payload = []
    total_bytes = 0
    for content, path in files_data:
        hash_val = create_blob(content)
        files_payload.append({
            "bundle_path": path,
            "size_bytes": len(content),
            "hash": hash_val,
            "hash_algo": "sha256"
        })
        total_bytes += len(content)

    # Create bundle
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={"files": files_payload, "hash_algo": "sha256"}
    )
    assert response.status_code == 201
    data = response.json()

    # Verify manifest
    manifest_path = Path(".data") / "bundles" / f"{data['id']}.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 3
    assert manifest["bytes"] == total_bytes


def test_create_bundle_with_client_id():
    """Test creating a bundle with client-provided ID."""
    content = b"test content"
    hash_val = create_blob(content)

    client_id = "my-custom-bundle-id"
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "id": client_id,
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == client_id

    # Verify manifest exists with custom ID
    manifest_path = Path(".data") / "bundles" / f"{client_id}.json"
    assert manifest_path.exists()


def test_create_bundle_duplicate_id_conflict():
    """Test that duplicate client-provided ID returns 409."""
    content = b"test content"
    hash_val = create_blob(content)

    client_id = "duplicate-test-id"
    payload = {
        "id": client_id,
        "files": [
            {
                "bundle_path": "file.txt",
                "size_bytes": len(content),
                "hash": hash_val,
                "hash_algo": "sha256"
            }
        ],
        "hash_algo": "sha256"
    }

    # First creation should succeed
    response1 = requests.post(f"{BASE_URL}/bundles", json=payload)
    assert response1.status_code == 201

    # Second creation with same ID should fail
    response2 = requests.post(f"{BASE_URL}/bundles", json=payload)
    assert response2.status_code == 409


def test_create_bundle_missing_blob():
    """Test that referencing non-existent blob returns 409."""
    fake_hash = "a" * 64

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": 100,
                    "hash": fake_hash,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 409


def test_create_bundle_duplicate_paths():
    """Test that duplicate paths in bundle returns 422."""
    content = b"test content"
    hash_val = create_blob(content)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "same.txt",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                },
                {
                    "bundle_path": "same.txt",  # Duplicate
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 422


def test_create_bundle_invalid_path_absolute():
    """Test that absolute path returns 422."""
    content = b"test content"
    hash_val = create_blob(content)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "/absolute/path.txt",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 422


def test_create_bundle_invalid_path_dotdot():
    """Test that path with '..' returns 422."""
    content = b"test content"
    hash_val = create_blob(content)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "../etc/passwd",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 422


def test_create_bundle_invalid_hash():
    """Test that invalid hash format returns 422."""
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": 100,
                    "hash": "invalid",  # Too short
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 422


def test_create_bundle_negative_size():
    """Test that negative size_bytes returns 422."""
    content = b"test content"
    hash_val = create_blob(content)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": -100,
                    "hash": hash_val,
                    "hash_algo": "sha256"
                }
            ],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 422


def test_create_bundle_empty_files():
    """Test creating a bundle with no files."""
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [],
            "hash_algo": "sha256"
        }
    )
    assert response.status_code == 201
    data = response.json()

    # Verify manifest
    manifest_path = Path(".data") / "bundles" / f"{data['id']}.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 0
    assert manifest["bytes"] == 0


def test_create_bundle_statistics():
    """Test that bundle statistics are calculated correctly."""
    files_data = [
        (b"a" * 100, "file1.txt"),
        (b"b" * 250, "file2.txt"),
        (b"c" * 50, "file3.txt"),
    ]

    files_payload = []
    expected_total = 0
    for content, path in files_data:
        hash_val = create_blob(content)
        files_payload.append({
            "bundle_path": path,
            "size_bytes": len(content),
            "hash": hash_val,
            "hash_algo": "sha256"
        })
        expected_total += len(content)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={"files": files_payload, "hash_algo": "sha256"}
    )
    assert response.status_code == 201

    # Verify statistics
    manifest_path = Path(".data") / "bundles" / f"{response.json()['id']}.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 3
    assert manifest["bytes"] == expected_total
    assert manifest["bytes"] == 400  # 100 + 250 + 50
