# Repository Guidelines

## Project Structure & Module Organization
This repository is split into a Python backend and a Vue frontend.

- `backend/`: Flask API and data pipeline code.
- `backend/api/app.py`: API entrypoint.
- `backend/core/`: shared config and database helpers.
- `backend/business_logic/`: punctuality and speed calculations.
- `backend/data_acquisition/`: GTFS fetch/import tools.
- `backend/services/`: long-running data collection services.
- `backend/database/*.sql`: base schema and feature schemas/migrations.
- `backend/tests/`: script-style verification tools.
- `frontend/`: Vue 3 + Vite application (`src/views`, `src/components`, `src/stores`, `src/api`).
- `gtfs_data/`: local GTFS files (ignored by Git), `start.sh`: local process manager.

## Build, Test, and Development Commands
- Backend setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt`
- Frontend setup: `cd frontend && npm install`
- Start full stack (recommended): `./start.sh start` (`stop|status|restart` also supported)
- Run backend only: `cd backend && PORT=5001 python3 -m api.app`
- Run frontend only: `cd frontend && npm run dev`
- Build/preview frontend: `cd frontend && npm run build && npm run preview`

## Coding Style & Naming Conventions
- Python: follow PEP 8, 4-space indentation, `snake_case` for functions/files, `PascalCase` for classes, and add type hints in new/changed code.
- Vue/JS: use 2-space indentation and single quotes.
- Naming: Vue component files use `PascalCase` (for example, `RouteCard.vue`); stores/util modules use `camelCase` (for example, `routeStore.js`).
- Keep API client code grouped by domain in `frontend/src/api/`; keep SQL changes in `backend/database/`.

## Testing Guidelines
Tests are currently script-based integration checks rather than a strict unit-test suite.

- Quick API smoke test: `cd backend && python3 tests/test_api_quick.py`
- Punctuality test workflow: `cd backend && python3 tests/test_punctuality.py`

Before running these, ensure PostgreSQL is running and the backend is available at `http://localhost:5001`.

## Commit & Pull Request Guidelines
- Recent commits favor short, scope-first subjects in Chinese (for example, `路线准点率`, `用户管理`) with occasional typed prefixes (`fix: ...`, `docs: ...`).
- Prefer concise subjects describing module + outcome.
- PRs should include:
1. Change summary and reason.
2. API/database impact (endpoints, SQL files, migrations).
3. Screenshots for UI changes.
4. Exact verification commands and results.

## Security & Configuration Tips
- Do not commit real API keys or credentials.
- Use environment variables (`SF_511_API_KEY`, `MTA_API_KEY`, `TFNSW_API_KEY`) or local-only `backend/config.local.json`.
- Keep generated data/log files out of commits (`gtfs_data/`, `frontend/dist/`, logs).
