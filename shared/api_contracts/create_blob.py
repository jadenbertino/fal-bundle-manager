"""API contracts for blob upload endpoint."""

from pydantic import BaseModel, field_validator
from shared.validation import validate_sha256_hash


class CreateBlobRequest(BaseModel):
    """Request schema for blob upload."""

    hash: str
    size_bytes: int

    @field_validator('hash')
    @classmethod
    def validate_hash(cls, v: str) -> str:
        validate_sha256_hash(v)
        return v

    @field_validator('size_bytes')
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v < 0:
            raise ValueError("size_bytes must be non-negative")
        return v


class CreateBlobResponse(BaseModel):
    """Response schema for blob upload."""

    status: str  # "created" or "exists"
    hash: str
