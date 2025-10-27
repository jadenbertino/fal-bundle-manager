from pydantic import BaseModel

from shared.types import Blob


class SyncRequest(BaseModel):
    blobs: list[Blob]
    bundle_id: str

class SyncResponse(BaseModel):
    to_create: list[Blob]