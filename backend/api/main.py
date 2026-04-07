"""FastAPI main application for FinLab-X."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables BEFORE importing application modules.
# Tools and tracing may read env vars (OPENAI_API_KEY, LANGCHAIN_TRACING_V2, etc.)
# at initialization time, so .env must be loaded first.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver  # noqa: E402

from backend.agent_engine.agents.base import Orchestrator  # noqa: E402
from backend.agent_engine.agents.config_loader import VersionConfigLoader  # noqa: E402
from backend.api.routers import chat, chat_invoke  # noqa: E402

logger = logging.getLogger(__name__)

APP_VERSION = "0.1.0"
DEFAULT_WORKFLOW_VERSION = "v1_baseline"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application-level singletons on startup."""
    config = VersionConfigLoader(DEFAULT_WORKFLOW_VERSION).load()

    db_path = os.environ.get("CHECKPOINT_DB_PATH", "data/checkpoints.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        app.state.orchestrator = Orchestrator(config, checkpointer=checkpointer)
        logger.info(
            "Orchestrator initialized: version=%s, model=%s, checkpointer=AsyncSqliteSaver(%s)",
            config.version,
            config.model.name,
            db_path,
        )
        yield


app = FastAPI(
    title="FinLab-X API",
    description="Financial Analysis AI System",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(chat_invoke.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": APP_VERSION}
