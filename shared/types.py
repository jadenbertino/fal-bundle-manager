from typing import Literal
from pydantic import BaseModel, Field, field_validator
from shared.validation import validate_sha256_hash, validate_relative_path


class Blob(BaseModel):
    """Represents a file with its content hash and metadata."""

    bundle_path: str = Field(..., description="Relative path within bundle. No '..' or leading '/'")
    size_bytes: int = Field(..., ge=0, description="File size in bytes. Non-negative integers only.")
    hash: str = Field(..., description="Content hash (64-character lowercase hex for SHA-256)")
    hash_algo: Literal["sha256"] = Field(..., description="Hash algorithm used (only sha256 supported)")

    @field_validator('hash')
    @classmethod
    def validate_hash(cls, v: str) -> str:
        return validate_sha256_hash(v)

    @field_validator('bundle_path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        return validate_relative_path(v)


class BundleSummary(BaseModel):
    """Core metadata for a bundle, excluding files list."""

    id: str = Field(..., description="Unique bundle identifier")
    created_at: str = Field(..., description="ISO 8601 timestamp (e.g., '2023-12-25T10:30:00Z')")
    hash_algo: Literal["sha256"] = Field(default="sha256", description="Hash algorithm used")
    file_count: int = Field(..., ge=0, description="Number of files in bundle")
    total_bytes: int = Field(..., ge=0, description="Total size of all files in bytes")


class BundleManifest(BundleSummary):
    """Complete bundle information including all files."""

    files: list[Blob] = Field(..., description="Array of files in the bundle")
