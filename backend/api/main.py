"""FastAPI main application for FinLab-X."""

from fastapi import FastAPI
from backend.api.routers import chat

app = FastAPI(
    title="FinLab-X API", description="Financial Analysis AI System", version="0.1.0"
)

app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
