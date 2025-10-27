from pathlib import Path

import requests

from cli.core.file_discovery import discover_files
from cli.core.hashing import hash_file_sha256
from shared.api_contracts.sync import SyncResponse
from shared.config import API_URL
from shared.types import Blob


def sync_bundle_to_dir(dir_path: Path, bundle_id: str):
    # walk dir -> identify list of file paths
    local_files = discover_files([str(dir_path)])
    print(local_files)

    # # hash each file -> represent file content
    local_blobs = [
        Blob(
            bundle_path=file.relative_path,
            size_bytes=1,
            hash=hash_file_sha256(file.absolute_path),
            hash_algo="sha256",
        ).model_dump(mode="json")
        for file in local_files
    ][:3]
    # print(local_blobs)

    # send paths + hashes to api
    r = requests.post(
        f"{API_URL}/bundles/sync",
        json={
            "blobs": local_blobs,
            "bundle_id": bundle_id,
        },
    )
    response_data = SyncResponse.model_validate(r.json())
    print(response_data)

    # get zip + to_cleanup from api
    # unzip zip + delete any paths in to_cleanup
    pass


sync_bundle_to_dir(Path("tmp3"), "01K8KRBHVJC3R9JTD8ZHDAJF3T")
