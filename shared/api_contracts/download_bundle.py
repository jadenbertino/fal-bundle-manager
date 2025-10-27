"""API contracts for download bundle endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class DownloadBundleParams(BaseModel):
    """Query parameters for downloading a bundle."""

    format: Literal["zip"] = Field(
        default="zip", description="Archive format (only 'zip' currently supported)"
    )
