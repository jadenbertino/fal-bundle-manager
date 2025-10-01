"""API contracts for create bundle endpoint."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from shared.types import Blob


class BundleManifestDraft(BaseModel):
    """Request schema for creating a bundle."""

    id: Optional[str] = Field(None, description="Optional client-provided bundle ID")
    files: list[Blob] = Field(..., description="Array of Blob objects")
    hash_algo: Literal["sha256"] = Field(..., description="Hash algorithm (must be sha256)")

    @field_validator('files')
    @classmethod
    def validate_no_duplicate_paths(cls, files: list[Blob]) -> list[Blob]:
        """Ensure no duplicate paths in the request."""
        paths = [f.bundle_path for f in files]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate paths found in request")
        return files


class BundleCreateResponse(BaseModel):
    """Response schema for bundle creation."""

    id: str = Field(..., description="Unique bundle identifier (ULID if auto-generated)")
    created_at: str = Field(..., description="ISO 8601 timestamp (e.g., '2023-12-25T10:30:00Z')")
