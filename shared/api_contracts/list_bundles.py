"""API contracts for list bundles endpoint."""

from pydantic import BaseModel, Field

from shared.types import BundleSummary


class BundleListResponse(BaseModel):
    """Response schema for listing bundles."""

    bundles: list[BundleSummary] = Field(
        ..., description="Array of bundle summaries, sorted by created_at descending"
    )
