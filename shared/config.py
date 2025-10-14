"""Shared configuration for API and CLI."""

import os
from pathlib import Path

# Shared (API AND CLI)
PAGE_SIZE = 25

# ENV VARS - API
DATA_DIR = Path(os.getenv("DATA_DIR", "api/.data"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 1024 * 1024 * 1024)) # 1GB default

# ENV VARS - CLI
API_URL = os.getenv("FAL_BUNDLES_API_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("FAL_BUNDLES_TIMEOUT", "300"))

# CONFIG - API
BLOBS_DIR = DATA_DIR / "blobs"
BUNDLES_DIR = DATA_DIR / "bundles"
MANIFESTS_DIR = BUNDLES_DIR / "manifests"
SUMMARIES_DIR = BUNDLES_DIR / "summaries"
TMP_DIR = DATA_DIR / "tmp"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    DIRS = [BLOBS_DIR, MANIFESTS_DIR, SUMMARIES_DIR, TMP_DIR]
    for dir in DIRS:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)