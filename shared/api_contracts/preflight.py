"""API contracts for preflight endpoint."""

from pydantic import BaseModel, field_validator

from shared.types import Blob


class PreflightRequest(BaseModel):
    """Request schema for preflight check."""

    files: list[Blob]

    @field_validator("files")
    @classmethod
    def validate_no_duplicate_paths(cls, files: list[Blob]) -> list[Blob]:
        """Ensure no duplicate paths in the request."""
        paths = [f.bundle_path for f in files]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate paths found in request")
        return files


class PreflightResponse(BaseModel):
    """Response schema for preflight check."""

    missing: list[
        str
    ]  # Array of SHA-256 hashes (64-char lowercase hex) that don't exist
