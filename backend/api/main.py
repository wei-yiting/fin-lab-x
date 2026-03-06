"""FastAPI main application for FinLab-X."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend.api.routers import chat

APP_VERSION = "0.1.0"

app = FastAPI(
    title="FinLab-X API",
    description="Financial Analysis AI System",
    version=APP_VERSION,
)

app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": APP_VERSION}
