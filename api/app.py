from fastapi import FastAPI
from api.config import ensure_directories

app = FastAPI()

# Ensure data directories exist
ensure_directories()


@app.get("/status")
async def status():
    return {"status": "ok"}
