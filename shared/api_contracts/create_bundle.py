"""API contracts for create bundle endpoint."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from shared.types import Blob
from shared.validation import validate_sha256_hash


class BundleManifestDraft(BaseModel):
    """Request schema for creating a bundle."""

    files: list[Blob] = Field(..., description="Array of Blob objects")
    hash_algo: Literal["sha256"] = Field(
        ..., description="Hash algorithm (must be sha256)"
    )
    merkle_root: str = Field(..., description="Merkle root over bundle files")

    @field_validator("merkle_root")
    @classmethod
    def validate_merkle_root(cls, v: str) -> str:
        return validate_sha256_hash(v)

    @field_validator("files")
    @classmethod
    def validate_no_duplicate_paths(cls, files: list[Blob]) -> list[Blob]:
        """Ensure no duplicate paths in the request."""
        paths = [f.bundle_path for f in files]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate paths found in request")
        return files


class BundleCreateResponse(BaseModel):
    """Response schema for bundle creation."""

    id: str = Field(
        ..., description="Unique bundle identifier (ULID if auto-generated)"
    )
    created_at: str = Field(
        ..., description="ISO 8601 timestamp (e.g., '2023-12-25T10:30:00Z')"
    )
    merkle_root: str = Field(..., description="Merkle root over bundle files")

    @field_validator("merkle_root")
    @classmethod
    def validate_merkle_root(cls, v: str) -> str:
        return validate_sha256_hash(v)
