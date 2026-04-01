# Repository Guidelines

## Project Structure & Module Organization
This repository has a Flask backend and a Vue 3 frontend.

- `backend/api/app.py`: backend entrypoint.
- `backend/core/`: shared config and PostgreSQL helpers.
- `backend/business_logic/`: punctuality and speed calculations.
- `backend/data_acquisition/`: GTFS download and import tools.
- `backend/services/` and `backend/scripts/`: long-running collectors and utility scripts.
- `backend/database/`: base schema and feature SQL files.
- `backend/tests/`: script-style verification tools.
- `frontend/src/views`, `frontend/src/components`, `frontend/src/stores`, `frontend/src/api`: UI pages, reusable components, Pinia stores, and API clients.
- `gtfs_data/`: local GTFS ZIP files; keep out of Git.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt`: set up backend dependencies.
- `cd frontend && npm install`: install frontend packages.
- `./start.sh start`: start frontend and backend together; use `stop`, `status`, or `restart` as needed.
- `cd backend && PORT=5001 python3 -m api.app`: run only the API.
- `cd frontend && npm run dev`: run only the Vite app.
- `cd frontend && npm run build && npm run preview`: build and preview the production frontend.

## Coding Style & Naming Conventions
Use 4-space indentation in Python and follow PEP 8. Add type hints in new or modified Python code. Use 2-space indentation in Vue and JavaScript, prefer single quotes, and follow the existing Composition API patterns. Name Vue components with `PascalCase` such as `RouteCard.vue`; use `camelCase` for stores and utility modules such as `routeStore.js`.

## Testing Guidelines
Testing is integration-oriented rather than a strict unit-test suite. Run `cd backend && python3 tests/test_api_quick.py` for a basic API smoke test and `cd backend && python3 tests/test_punctuality.py` for punctuality validation. Ensure PostgreSQL is running and the backend is available at `http://localhost:5001` before executing these scripts.

## Commit & Pull Request Guidelines
Recent history favors short, scope-first Chinese commit subjects such as `路线准点率` or `用户管理`, with occasional typed prefixes like `fix:` and `docs:`. Keep commits focused and descriptive. Pull requests should include a concise summary, database or API impact, screenshots for UI changes, and the exact verification commands you ran.

## Security & Configuration Tips
Do not commit real credentials, generated GTFS data, logs, or frontend build output. Use environment variables such as `SF_511_API_KEY`, `MTA_API_KEY`, and `TFNSW_API_KEY`, or keep local secrets in `backend/config.local.json`.
