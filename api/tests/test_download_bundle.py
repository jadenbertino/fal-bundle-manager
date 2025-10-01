import requests
import zipfile
import io
from pathlib import Path
from api.tests.helpers import BASE_URL, create_blob, create_bundle


def test_download_bundle_simple():
    """Test downloading a simple bundle with one file."""
    # Create a bundle
    content = b"test file content"
    bundle_data = create_bundle([(content, "test.txt")], "download-test-simple")

    # Download the bundle
    response = requests.get(f"{BASE_URL}/bundles/download-test-simple/download")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "bundle_download-test-simple.zip" in response.headers["Content-Disposition"]

    # Verify ZIP content
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        assert "test.txt" in zf.namelist()
        assert zf.read("test.txt") == content


def test_download_bundle_multiple_files():
    """Test downloading a bundle with multiple files and directories."""
    files_data = [
        (b"file1 content", "file1.txt"),
        (b"file2 content", "dir/file2.txt"),
        (b"file3 content", "dir/subdir/file3.txt"),
    ]
    bundle_data = create_bundle(files_data, "download-test-multiple")

    # Download the bundle
    response = requests.get(f"{BASE_URL}/bundles/download-test-multiple/download")
    assert response.status_code == 200

    # Verify ZIP content
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        namelist = zf.namelist()
        assert "file1.txt" in namelist
        assert "dir/file2.txt" in namelist
        assert "dir/subdir/file3.txt" in namelist

        # Verify content
        assert zf.read("file1.txt") == b"file1 content"
        assert zf.read("dir/file2.txt") == b"file2 content"
        assert zf.read("dir/subdir/file3.txt") == b"file3 content"


def test_download_bundle_not_found():
    """Test downloading non-existent bundle returns 404."""
    response = requests.get(f"{BASE_URL}/bundles/nonexistent-bundle-id/download")
    assert response.status_code == 404


def test_download_bundle_empty():
    """Test downloading an empty bundle."""
    bundle_data = create_bundle([], "download-test-empty")

    response = requests.get(f"{BASE_URL}/bundles/download-test-empty/download")
    assert response.status_code == 200

    # Verify ZIP is valid but empty
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        assert len(zf.namelist()) == 0


def test_download_bundle_default_format():
    """Test that default format is zip."""
    bundle_data = create_bundle([(b"test", "file.txt")], "download-test-default")

    # Without format parameter
    response = requests.get(f"{BASE_URL}/bundles/download-test-default/download")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"


def test_download_bundle_explicit_zip_format():
    """Test downloading with explicit zip format parameter."""
    bundle_data = create_bundle([(b"test", "file.txt")], "download-test-explicit-zip")

    response = requests.get(
        f"{BASE_URL}/bundles/download-test-explicit-zip/download",
        params={"format": "zip"}
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"


def test_download_bundle_unsupported_format():
    """Test that unsupported format returns 415."""
    bundle_data = create_bundle([(b"test", "file.txt")], "download-test-unsupported")

    response = requests.get(
        f"{BASE_URL}/bundles/download-test-unsupported/download",
        params={"format": "tar"}
    )
    assert response.status_code == 415


def test_download_bundle_large_files():
    """Test downloading bundle with larger files."""
    # Create bundle with larger files
    large_content = b"x" * (1024 * 100)  # 100KB
    files_data = [
        (large_content, "large1.bin"),
        (large_content, "large2.bin"),
    ]
    bundle_data = create_bundle(files_data, "download-test-large")

    response = requests.get(f"{BASE_URL}/bundles/download-test-large/download")
    assert response.status_code == 200

    # Verify ZIP content
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        assert zf.read("large1.bin") == large_content
        assert zf.read("large2.bin") == large_content


def test_download_bundle_preserves_paths():
    """Test that bundle download preserves original file paths."""
    files_data = [
        (b"root", "root.txt"),
        (b"nested1", "a/b/c/file1.txt"),
        (b"nested2", "x/y/file2.txt"),
    ]
    bundle_data = create_bundle(files_data, "download-test-paths")

    response = requests.get(f"{BASE_URL}/bundles/download-test-paths/download")
    assert response.status_code == 200

    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        namelist = zf.namelist()
        assert "root.txt" in namelist
        assert "a/b/c/file1.txt" in namelist
        assert "x/y/file2.txt" in namelist


def test_download_bundle_deduplication():
    """Test that bundles with shared blobs work correctly."""
    # Create two bundles that share a blob
    shared_content = b"shared content"

    bundle1 = create_bundle([(shared_content, "file1.txt")], "download-dedup-1")
    bundle2 = create_bundle([(shared_content, "file2.txt")], "download-dedup-2")

    # Download both bundles
    response1 = requests.get(f"{BASE_URL}/bundles/download-dedup-1/download")
    response2 = requests.get(f"{BASE_URL}/bundles/download-dedup-2/download")

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Verify both have correct content
    zip1 = io.BytesIO(response1.content)
    zip2 = io.BytesIO(response2.content)

    with zipfile.ZipFile(zip1, "r") as zf1:
        assert zf1.read("file1.txt") == shared_content

    with zipfile.ZipFile(zip2, "r") as zf2:
        assert zf2.read("file2.txt") == shared_content


def test_download_bundle_special_characters_in_filename():
    """Test downloading bundle with special characters in filenames."""
    files_data = [
        (b"content1", "file with spaces.txt"),
        (b"content2", "file-with-dashes.txt"),
        (b"content3", "file_with_underscores.txt"),
    ]
    bundle_data = create_bundle(files_data, "download-test-special")

    response = requests.get(f"{BASE_URL}/bundles/download-test-special/download")
    assert response.status_code == 200

    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, "r") as zf:
        assert "file with spaces.txt" in zf.namelist()
        assert "file-with-dashes.txt" in zf.namelist()
        assert "file_with_underscores.txt" in zf.namelist()
