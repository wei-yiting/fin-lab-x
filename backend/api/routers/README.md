## Scope
API route handler modules. This directory contains the implementation of specific API endpoints, organized by domain. Each module is responsible for defining its own request/response schemas and handling the logic for its respective routes.

## Map
- `chat.py`: Implements the core financial analysis chat endpoint (`POST /api/v1/chat`). It handles the conversion of web requests into agent execution calls and formats the resulting tool outputs for the frontend.
- `__init__.py`: Standard Python package initialization file.

## Design Pattern
- **FastAPI Router Pattern**: Each file defines an `APIRouter` instance, allowing for modular endpoint organization, automatic documentation tagging, and clean path prefixing.
- **Dependency Injection**: Route handlers use FastAPI's `Depends` mechanism to retrieve the `Orchestrator` singleton from the application state, ensuring that the API layer remains decoupled from the agent's initialization logic.

## Extension Algorithm
1. **Create Route Module**: Create a new Python file in this directory (e.g., `user_profile.py`).
2. **Initialize APIRouter**: Define a router instance: `router = APIRouter(prefix="/api/v1/user", tags=["user"])`.
3. **Define Pydantic Models**: Create `BaseModel` classes for the request body and the expected response structure.
4. **Implement Route Handler**: Write an `async` function decorated with `@router.post()` or `@router.get()`. Use `Depends(get_orchestrator)` to access the agent engine if needed.
5. **Register Router**: Import the new router in `backend/api/main.py` and include it in the main FastAPI application.
