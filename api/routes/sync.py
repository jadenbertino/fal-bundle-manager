import io
import json
import zipfile

from fastapi import APIRouter, HTTPException

from api.storage import get_blob_path
from shared.api_contracts.sync import SyncRequest, SyncResponse
from shared.config import get_bundle_manifests_dir
from shared.types import Blob, BundleManifest

router = APIRouter()


@router.post("/bundles/sync")
async def preflight(request: SyncRequest):
    blobs = request.blobs
    bundle_id = request.bundle_id

    # get bundle for bundle id (reuse function probably)
    bundle_path = get_bundle_manifests_dir() / f"{bundle_id}.json"
    if not bundle_path.exists():
        raise HTTPException(
            status_code=400, detail=f"Bundle {bundle_id} does not exist"
        )

    # parse bundle details
    with open(bundle_path) as f:
        file_content = json.load(f)
        bundle = BundleManifest.model_validate(file_content)
    bundle_files_by_filepath = {f.bundle_path: f for f in bundle.files}
    request_files_by_filepath = {f.bundle_path: f for f in blobs}

    # create diffs array
    to_create: list[Blob] = []
    for filepath in bundle_files_by_filepath:
        bundle_file = bundle_files_by_filepath[filepath]
        request_file = request_files_by_filepath.get(filepath)

        # if bundle path is missing from request.blobs -> add it
        # find blob from request.blobs -> if hash is different (diff file content) -> add it
        if not request_file or request_file.hash != bundle_file.hash:
            to_create.append(bundle_file)

    # create to_delete array (list of filepaths (str))
    to_delete = []

    # create zip of all files in to_create
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for blob in to_create:
            blob_filepath = get_blob_path(blob.hash)
            if not blob_filepath.exists():
                raise FileNotFoundError(f"Blob {blob.hash} does not exst")

            # Read blob content and add to ZIP with bundle path
            zf.write(blob_filepath, arcname=bundle_path)
    zip_buffer.seek(0)  # Seek to beginning for streaming

    # return zip + to_delete array
    return SyncResponse(to_create=to_create)
