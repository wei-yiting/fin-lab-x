## Scope
FastAPI HTTP/SSE routing layer. This directory handles the web interface of the application, including request validation, routing, and response formatting. It serves as a thin wrapper around the `agent_engine`, and MUST NOT contain any core AI or financial reasoning logic.

## Map
- `main.py`: The application factory and entry point. It handles environment variable loading, FastAPI app initialization, and the `lifespan` context manager.
- `routers/`: Subdirectory containing modular route handlers, such as the chat endpoint.

## Design Pattern
- **Dependency Injection**: Leverages FastAPI's `Depends` system to decouple route handlers from service implementations (e.g., injecting the `Orchestrator` into the chat endpoint).
- **Lifespan Pattern**: Uses an `asynccontextmanager` to manage the application lifecycle, ensuring that heavy singletons like the `Orchestrator` are initialized once on startup and stored in `app.state`.

## Extension Algorithm
1. **Create New Router**: Add a new Python module in the `routers/` directory (e.g., `routers/research.py`).
2. **Define Endpoints**: Initialize an `APIRouter` and define your path operations (GET, POST, etc.) with appropriate Pydantic request/response models.
3. **Inject Dependencies**: Use `Depends(get_orchestrator)` or other dependency functions to access shared services.
4. **Register with App**: Import the new router in `backend/api/main.py` and register it using `app.include_router(new_router.router)`.
