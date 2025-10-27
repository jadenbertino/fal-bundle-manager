import hashlib
import requests
import json
from pathlib import Path
from api.tests.helpers import BASE_URL, create_blob
from shared.merkle import compute_merkle_root
from shared.types import Blob


def test_create_bundle_simple():
    """Test creating a simple bundle with one file."""
    # Use real fixture file content
    from pathlib import Path

    fixture_file = Path("fixtures/test_data/single_file.txt")
    with open(fixture_file, "rb") as f:
        content = f.read()
    hash_val = create_blob(content)

    # Create blob object for merkle root computation
    blob = Blob(
        bundle_path="single_file.txt",
        size_bytes=len(content),
        hash=hash_val,
        hash_algo="sha256",
    )
    merkle_root = compute_merkle_root([blob])

    # Create bundle
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "single_file.txt",
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
            "merkle_root": merkle_root,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "created_at" in data
    assert "merkle_root" in data

    # Verify manifest and summary files exist
    bundle_id = data["id"]
    manifest_path = Path("api/.data") / "bundles" / "manifests" / f"{bundle_id}.json"
    summary_path = Path("api/.data") / "bundles" / "summaries" / f"{bundle_id}.json"
    assert manifest_path.exists()
    assert summary_path.exists()

    expected_root = compute_merkle_root(
        [
            Blob(
                bundle_path="single_file.txt",
                size_bytes=len(content),
                hash=hash_val,
                hash_algo="sha256",
            )
        ]
    )
    assert data["merkle_root"] == expected_root

    # Verify manifest content (includes files)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["id"] == bundle_id
    assert manifest["hash_algo"] == "sha256"
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["hash"] == hash_val
    assert manifest["file_count"] == 1
    assert manifest["total_bytes"] == len(content)
    assert manifest["merkle_root"] == expected_root

    # Verify summary content (does NOT include files)
    summary = json.loads(summary_path.read_text())
    assert summary["id"] == bundle_id
    assert summary["hash_algo"] == "sha256"
    assert "files" not in summary
    assert summary["file_count"] == 1
    assert summary["total_bytes"] == len(content)
    assert summary["merkle_root"] == expected_root


def test_create_bundle_multiple_files():
    """Test creating a bundle with multiple files."""
    # Create multiple blobs
    files_data = [
        (b"file 1 content", "file1.txt"),
        (b"file 2 content with more data", "dir/file2.txt"),
        (b"file 3", "dir/subdir/file3.txt"),
    ]

    files_payload = []
    blobs = []
    total_bytes = 0
    for content, path in files_data:
        hash_val = create_blob(content)
        files_payload.append(
            {
                "bundle_path": path,
                "size_bytes": len(content),
                "hash": hash_val,
                "hash_algo": "sha256",
            }
        )
        blobs.append(
            Blob(
                bundle_path=path,
                size_bytes=len(content),
                hash=hash_val,
                hash_algo="sha256",
            )
        )
        total_bytes += len(content)

    # Compute merkle root
    merkle_root = compute_merkle_root(blobs)

    # Create bundle
    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": files_payload,
            "hash_algo": "sha256",
            "merkle_root": merkle_root,
        },
    )
    assert response.status_code == 201
    data = response.json()
    expected_root = compute_merkle_root(blobs)
    assert data["merkle_root"] == expected_root

    # Verify manifest and summary
    manifest_path = Path("api/.data") / "bundles" / "manifests" / f"{data['id']}.json"
    summary_path = Path("api/.data") / "bundles" / "summaries" / f"{data['id']}.json"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 3
    assert manifest["total_bytes"] == total_bytes
    assert manifest["merkle_root"] == expected_root

    summary = json.loads(summary_path.read_text())
    assert summary["file_count"] == 3
    assert summary["total_bytes"] == total_bytes
    assert "files" not in summary
    assert summary["merkle_root"] == expected_root


def test_create_bundle_missing_blob():
    """Test that referencing non-existent blob returns 409."""
    fake_hash = "a" * 64

    # Create blob object for merkle root computation (even though blob doesn't exist)
    blob = Blob(
        bundle_path="file.txt", size_bytes=100, hash=fake_hash, hash_algo="sha256"
    )
    merkle_root = compute_merkle_root([blob])

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": [
                {
                    "bundle_path": "file.txt",
                    "size_bytes": 100,
                    "hash": fake_hash,
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
            "merkle_root": merkle_root,
        },
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
                    "hash_algo": "sha256",
                },
                {
                    "bundle_path": "same.txt",  # Duplicate
                    "size_bytes": len(content),
                    "hash": hash_val,
                    "hash_algo": "sha256",
                },
            ],
            "hash_algo": "sha256",
        },
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
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
        },
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
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
        },
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
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
        },
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
                    "hash_algo": "sha256",
                }
            ],
            "hash_algo": "sha256",
        },
    )
    assert response.status_code == 422


def test_create_bundle_empty_files():
    """Test creating a bundle with no files."""
    # Compute merkle root for empty files
    merkle_root = compute_merkle_root([])

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={"files": [], "hash_algo": "sha256", "merkle_root": merkle_root},
    )
    assert response.status_code == 201
    data = response.json()
    assert "merkle_root" in data
    expected_root = compute_merkle_root([])
    assert data["merkle_root"] == expected_root

    # Verify manifest and summary
    bundle_id = data["id"]
    manifest_path = Path("api/.data") / "bundles" / "manifests" / f"{bundle_id}.json"
    summary_path = Path("api/.data") / "bundles" / "summaries" / f"{bundle_id}.json"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 0
    assert manifest["total_bytes"] == 0
    assert manifest["merkle_root"] == expected_root

    summary = json.loads(summary_path.read_text())
    assert summary["file_count"] == 0
    assert summary["total_bytes"] == 0
    assert "files" not in summary
    assert summary["merkle_root"] == expected_root


def test_create_bundle_statistics():
    """Test that bundle statistics are calculated correctly."""
    files_data = [
        (b"a" * 100, "file1.txt"),
        (b"b" * 250, "file2.txt"),
        (b"c" * 50, "file3.txt"),
    ]

    files_payload = []
    blobs = []
    expected_total = 0
    for content, path in files_data:
        hash_val = create_blob(content)
        files_payload.append(
            {
                "bundle_path": path,
                "size_bytes": len(content),
                "hash": hash_val,
                "hash_algo": "sha256",
            }
        )
        expected_total += len(content)
        blobs.append(
            Blob(
                bundle_path=path,
                size_bytes=len(content),
                hash=hash_val,
                hash_algo="sha256",
            )
        )

    # Compute merkle root
    merkle_root = compute_merkle_root(blobs)

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": files_payload,
            "hash_algo": "sha256",
            "merkle_root": merkle_root,
        },
    )
    assert response.status_code == 201

    # Verify statistics
    bundle_id = response.json()["id"]
    expected_root = compute_merkle_root(blobs)
    manifest_path = Path("api/.data") / "bundles" / "manifests" / f"{bundle_id}.json"
    summary_path = Path("api/.data") / "bundles" / "summaries" / f"{bundle_id}.json"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["file_count"] == 3
    assert manifest["total_bytes"] == expected_total
    assert manifest["total_bytes"] == 400  # 100 + 250 + 50
    assert manifest["merkle_root"] == expected_root

    summary = json.loads(summary_path.read_text())
    assert summary["file_count"] == 3
    assert summary["total_bytes"] == expected_total
    assert "files" not in summary
    assert summary["merkle_root"] == expected_root


def test_compute_merkle_root_manual_calculation():
    """Manually compute the Merkle root to validate the helper implementation."""

    blobs = [
        Blob(bundle_path="a.txt", size_bytes=1, hash="a" * 64, hash_algo="sha256"),
        Blob(bundle_path="b.txt", size_bytes=1, hash="b" * 64, hash_algo="sha256"),
        Blob(bundle_path="c.txt", size_bytes=1, hash="c" * 64, hash_algo="sha256"),
    ]

    result = compute_merkle_root(blobs)

    leaf_a = hashlib.sha256(f"a.txt:{'a' * 64}".encode()).digest()
    leaf_b = hashlib.sha256(f"b.txt:{'b' * 64}".encode()).digest()
    leaf_c = hashlib.sha256(f"c.txt:{'c' * 64}".encode()).digest()

    level_left = hashlib.sha256(leaf_a + leaf_b).digest()
    level_right = hashlib.sha256(leaf_c + leaf_c).digest()
    expected_root = hashlib.sha256(level_left + level_right).hexdigest()

    assert result == expected_root
    assert len(result) == 64


def test_create_bundle_response_merkle_root_matches_manual():
    """Ensure create bundle response returns the Merkle root computed on the client."""

    files = [
        (b"alpha", "dir/a.txt"),
        (b"beta", "dir/b.txt"),
    ]

    payload_files = []
    for content, path in files:
        hash_val = create_blob(content)
        payload_files.append(
            {
                "bundle_path": path,
                "size_bytes": len(content),
                "hash": hash_val,
                "hash_algo": "sha256",
            }
        )

    manual_leaves = []
    for path, hash_val in sorted((f["bundle_path"], f["hash"]) for f in payload_files):
        manual_leaves.append(hashlib.sha256(f"{path}:{hash_val}".encode()).digest())

    manual_root = hashlib.sha256(manual_leaves[0] + manual_leaves[1]).hexdigest()

    response = requests.post(
        f"{BASE_URL}/bundles",
        json={
            "files": payload_files,
            "hash_algo": "sha256",
            "merkle_root": manual_root,
        },
    )
    assert response.status_code == 201
    data = response.json()

    assert data["merkle_root"] == manual_root

    summary_path = Path("api/.data") / "bundles" / "summaries" / f"{data['id']}.json"
    summary = json.loads(summary_path.read_text())
    assert summary["merkle_root"] == manual_root
