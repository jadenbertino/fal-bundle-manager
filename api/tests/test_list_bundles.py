import requests
from pathlib import Path
from api.tests.helpers import BASE_URL, create_blob, create_bundle
from shared.config import get_data_dir


def test_list_bundles_empty():
    """Test listing bundles when none exist."""
    # Clean up bundles summaries directory
    summaries_dir = get_data_dir() / "bundles" / "summaries"
    if summaries_dir.exists():
        for bundle_file in summaries_dir.glob("*.json"):
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
    assert bundle["total_bytes"] == len(b"test content")
    assert bundle["merkle_root"] == bundle_data["merkle_root"]


def test_list_bundles_multiple():
    """Test listing multiple bundles."""
    # Create multiple bundles
    bundle1 = create_bundle([(b"file1", "f1.txt")])
    bundle2 = create_bundle([(b"file2", "f2.txt"), (b"file3", "f3.txt")])
    bundle3 = create_bundle([(b"file4" * 100, "f4.txt")])

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    assert "bundles" in data
    bundles = data["bundles"]

    # Find our bundles by checking that we have at least 3 bundles
    # (we can't predict the exact IDs since they're auto-generated)
    assert len(bundles) >= 3

    # Find bundles by their characteristics
    # Bundle 1: 1 file, 5 bytes
    b1 = next((b for b in bundles if b["file_count"] == 1 and b["total_bytes"] == 5), None)
    assert b1 is not None
    assert len(b1["merkle_root"]) == 64

    # Bundle 2: 2 files, 10 bytes
    b2 = next((b for b in bundles if b["file_count"] == 2 and b["total_bytes"] == 10), None)
    assert b2 is not None
    assert len(b2["merkle_root"]) == 64

    # Bundle 3: 1 file, 500 bytes
    b3 = next((b for b in bundles if b["file_count"] == 1 and b["total_bytes"] == 500), None)
    assert b3 is not None
    assert len(b3["merkle_root"]) == 64


def test_list_bundles_sorted_by_created_at():
    """Test that bundles are sorted by created_at descending (newest first)."""
    import time

    # Create bundles with small delays to ensure different timestamps
    bundle1 = create_bundle([(b"first", "1.txt")])
    time.sleep(0.1)
    bundle2 = create_bundle([(b"second", "2.txt")])
    time.sleep(0.1)
    bundle3 = create_bundle([(b"third", "3.txt")])

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    bundles = data["bundles"]

    # Find our test bundles by looking for bundles with 1 file and 5 bytes
    # (each of our test bundles has this characteristic)
    test_bundles = [b for b in bundles if b["file_count"] == 1 and b["total_bytes"] == 5]
    assert len(test_bundles) >= 3  # We created 3 bundles, but there might be others
    
    # Verify all test bundles have valid merkle roots
    for entry in test_bundles:
        assert len(entry["merkle_root"]) == 64

    # Verify sorting (newest first) - check that created_at timestamps are in descending order
    created_at_times = [b["created_at"] for b in test_bundles]
    assert created_at_times == sorted(created_at_times, reverse=True)


def test_list_bundles_response_schema():
    """Test that response matches BundleListResponse schema."""
    # Create a bundle
    create_bundle([(b"schema test", "test.txt")])

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    # Validate top-level structure
    assert "bundles" in data
    assert isinstance(data["bundles"], list)

    # Find our bundle by its characteristics (1 file, 11 bytes for "schema test")
    # We need to be more specific since there might be other bundles with same characteristics
    bundles_with_1_file_11_bytes = [b for b in data["bundles"] if b["file_count"] == 1 and b["total_bytes"] == 11]
    assert len(bundles_with_1_file_11_bytes) >= 1
    bundle = bundles_with_1_file_11_bytes[0]  # Use the first one we find

    # Validate BundleSummary fields
    required_fields = [
        "id",
        "created_at",
        "hash_algo",
        "file_count",
        "total_bytes",
        "merkle_root",
    ]
    for field in required_fields:
        assert field in bundle, f"Missing required field: {field}"

    # Validate types
    assert isinstance(bundle["id"], str)
    assert isinstance(bundle["created_at"], str)
    assert isinstance(bundle["hash_algo"], str)
    assert isinstance(bundle["file_count"], int)
    assert isinstance(bundle["total_bytes"], int)
    assert isinstance(bundle["merkle_root"], str)
    assert len(bundle["merkle_root"]) == 64

    # Should not include files list
    assert "files" not in bundle


def test_list_bundles_statistics_accuracy():
    """Test that file_count and bytes are accurate."""
    files_data = [
        (b"a" * 100, "file1.txt"),
        (b"b" * 250, "file2.txt"),
        (b"c" * 50, "file3.txt"),
    ]

    bundle_data = create_bundle(files_data)

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    # Find bundle by its characteristics (3 files, 400 bytes)
    bundle = next((b for b in data["bundles"] if b["file_count"] == 3 and b["total_bytes"] == 400), None)
    assert bundle is not None
    assert bundle["file_count"] == 3
    assert bundle["total_bytes"] == 400  # 100 + 250 + 50
    assert len(bundle["merkle_root"]) == 64


def test_list_bundles_empty_bundle():
    """Test listing includes bundles with no files."""
    create_bundle([])

    response = requests.get(f"{BASE_URL}/bundles")
    assert response.status_code == 200
    data = response.json()

    # Find empty bundle by its characteristics (0 files, 0 bytes)
    bundle = next((b for b in data["bundles"] if b["file_count"] == 0 and b["total_bytes"] == 0), None)
    assert bundle is not None
    assert bundle["file_count"] == 0
    assert bundle["total_bytes"] == 0
    assert len(bundle["merkle_root"]) == 64
