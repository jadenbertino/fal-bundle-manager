from fastapi import FastAPI
from api.config import ensure_directories
from api.routes import preflight, create_blob

app = FastAPI()

# Ensure data directories exist
ensure_directories()

# Include routers
app.include_router(preflight.router)
app.include_router(create_blob.router)


@app.get("/status")
async def status():
    return {"status": "ok"}
