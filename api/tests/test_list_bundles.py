import requests
from pathlib import Path
from api.tests.helpers import BASE_URL, create_blob, create_bundle


def test_list_bundles_empty():
    """Test listing bundles when none exist."""
    # Clean up bundles directory
    bundles_dir = Path(".data") / "bundles"
    if bundles_dir.exists():
        for bundle_file in bundles_dir.glob("*.json"):
            bundle_file.unlink()

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()
    assert "bundles" in data
    assert data["bundles"] == []


def test_list_bundles_single():
    """Test listing bundles with a single bundle."""
    # Create one bundle
    bundle_data = create_bundle([(b"test content", "file.txt")])

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    assert "bundles" in data
    assert len(data["bundles"]) >= 1

    # Find our bundle
    bundle = next((b for b in data["bundles"] if b["id"] == bundle_data["id"]), None)
    assert bundle is not None
    assert bundle["id"] == bundle_data["id"]
    assert bundle["created_at"] == bundle_data["created_at"]
    assert bundle["hash_algo"] == "sha256"
    assert bundle["file_count"] == 1
    assert bundle["bytes"] == len(b"test content")


def test_list_bundles_multiple():
    """Test listing multiple bundles."""
    # Create multiple bundles
    bundle1 = create_bundle([(b"file1", "f1.txt")], "bundle-list-test-1")
    bundle2 = create_bundle([(b"file2", "f2.txt"), (b"file3", "f3.txt")], "bundle-list-test-2")
    bundle3 = create_bundle([(b"file4" * 100, "f4.txt")], "bundle-list-test-3")

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    assert "bundles" in data
    bundles = data["bundles"]

    # Find our bundles
    ids = [b["id"] for b in bundles]
    assert "bundle-list-test-1" in ids
    assert "bundle-list-test-2" in ids
    assert "bundle-list-test-3" in ids

    # Verify bundle 1
    b1 = next(b for b in bundles if b["id"] == "bundle-list-test-1")
    assert b1["file_count"] == 1
    assert b1["bytes"] == 5

    # Verify bundle 2
    b2 = next(b for b in bundles if b["id"] == "bundle-list-test-2")
    assert b2["file_count"] == 2
    assert b2["bytes"] == 10

    # Verify bundle 3
    b3 = next(b for b in bundles if b["id"] == "bundle-list-test-3")
    assert b3["file_count"] == 1
    assert b3["bytes"] == 500


def test_list_bundles_sorted_by_created_at():
    """Test that bundles are sorted by created_at descending (newest first)."""
    import time

    # Create bundles with small delays to ensure different timestamps
    bundle1 = create_bundle([(b"first", "1.txt")], "bundle-sort-1")
    time.sleep(0.1)
    bundle2 = create_bundle([(b"second", "2.txt")], "bundle-sort-2")
    time.sleep(0.1)
    bundle3 = create_bundle([(b"third", "3.txt")], "bundle-sort-3")

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    bundles = data["bundles"]

    # Find our test bundles
    test_bundles = [b for b in bundles if b["id"].startswith("bundle-sort-")]
    assert len(test_bundles) == 3

    # Verify sorting (newest first)
    ids = [b["id"] for b in test_bundles]
    assert ids[0] == "bundle-sort-3"  # Newest
    assert ids[1] == "bundle-sort-2"
    assert ids[2] == "bundle-sort-1"  # Oldest


def test_list_bundles_response_schema():
    """Test that response matches BundleListResponse schema."""
    # Create a bundle
    create_bundle([(b"schema test", "test.txt")], "bundle-schema-test")

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    # Validate top-level structure
    assert "bundles" in data
    assert isinstance(data["bundles"], list)

    # Find our bundle and validate structure
    bundle = next((b for b in data["bundles"] if b["id"] == "bundle-schema-test"), None)
    assert bundle is not None

    # Validate BundleSummary fields
    required_fields = ["id", "created_at", "hash_algo", "file_count", "bytes"]
    for field in required_fields:
        assert field in bundle, f"Missing required field: {field}"

    # Validate types
    assert isinstance(bundle["id"], str)
    assert isinstance(bundle["created_at"], str)
    assert isinstance(bundle["hash_algo"], str)
    assert isinstance(bundle["file_count"], int)
    assert isinstance(bundle["bytes"], int)

    # Should not include files list
    assert "files" not in bundle


def test_list_bundles_statistics_accuracy():
    """Test that file_count and bytes are accurate."""
    files_data = [
        (b"a" * 100, "file1.txt"),
        (b"b" * 250, "file2.txt"),
        (b"c" * 50, "file3.txt"),
    ]

    bundle_data = create_bundle(files_data, "bundle-stats-test")

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    bundle = next((b for b in data["bundles"] if b["id"] == "bundle-stats-test"), None)
    assert bundle is not None
    assert bundle["file_count"] == 3
    assert bundle["bytes"] == 400  # 100 + 250 + 50


def test_list_bundles_empty_bundle():
    """Test listing includes bundles with no files."""
    create_bundle([], "bundle-empty-test")

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    bundle = next((b for b in data["bundles"] if b["id"] == "bundle-empty-test"), None)
    assert bundle is not None
    assert bundle["file_count"] == 0
    assert bundle["bytes"] == 0
