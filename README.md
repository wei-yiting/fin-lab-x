# FinLab-X

Modular, multi-agent AI system for Just-in-Time (JIT) intelligence on US growth stocks.

## Architecture Overview
FinLab-X is built with a decoupled architecture:
- **Backend**: Python-based AI Agent Engine using LangGraph and FastAPI.
- **Frontend**: TypeScript-based Next.js Generative UI.
For detailed architecture, see [docs/agent_architecture.md](docs/agent_architecture.md).

## Quick Start
### Backend
```bash
uv sync
uv run uvicorn backend.api.main:app --reload
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Versioned Workflow Profiles
The system supports multiple analysis profiles:
- **v1_baseline**: Standard RAG financial analysis.
- **v2_reader**: Long-context document synthesis.
- **v3_quant**: Numerical reasoning and modeling.
- **v4_graph**: Knowledge graph-based analysis.
- **v5_analyst**: Comprehensive investment research.

## Development
- **Linting**: `ruff check backend/`, `npm run lint`
- **Testing**: `pytest backend/tests/`, `npm run test`
- **Formatting**: `ruff format backend/`, `npx prettier --write "frontend/src/**/*.{ts,tsx}"`
