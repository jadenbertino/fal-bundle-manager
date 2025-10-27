from fastapi import FastAPI

from api.routes import (
    create_blob,
    create_bundle,
    download_bundle,
    list_bundles,
    preflight,
)
from shared.config import ensure_directories

app = FastAPI()

# Ensure data directories exist
ensure_directories()

# Include routers
app.include_router(preflight.router)
app.include_router(create_blob.router)
app.include_router(create_bundle.router)
app.include_router(list_bundles.router)
app.include_router(download_bundle.router)


@app.get("/status")
async def status():
    return {"status": "ok"}
