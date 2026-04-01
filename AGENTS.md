# Repository Guidelines

## Project Structure & Module Organization
This repository is split into a Flask backend and a Vue 3 frontend. Use `backend/api/` for HTTP routes, `backend/core/` for config and PostgreSQL helpers, `backend/business_logic/` for calculations, `backend/data_acquisition/` for GTFS fetch/import flows, `backend/services/` and `backend/scripts/` for collectors and utilities, and `backend/database/` for schema SQL. Frontend code lives in `frontend/src/`: `views/` for pages, `components/` for shared UI, `stores/` for Pinia state, `api/` for Axios clients, `router/` for navigation, and `i18n/` for locale strings. Keep local GTFS ZIPs in `gtfs_data/`; do not commit them.

## Build, Test, and Development Commands
- `pip3 install -r backend/requirements.txt`: install backend dependencies.
- `cd frontend && npm install`: install frontend dependencies.
- `./start.sh start|stop|status|restart`: manage both apps locally; backend runs on `:5001`, frontend on `:5173`.
- `cd backend && python3 -m api.app`: run only the API.
- `cd frontend && npm run dev`: run the Vite dev server.
- `cd frontend && npm run build && npm run preview`: build and preview the production frontend.
- `createdb gtfs_db && psql gtfs_db -f backend/database/schema.sql`: initialize the base database schema.

## Coding Style & Naming Conventions
Follow PEP 8 in Python with 4-space indentation, `snake_case` modules, and type hints in new or changed code. Frontend files follow Vue 3 Composition API with `<script setup>`, 2-space indentation, single quotes, and no semicolons. Name components and view files in `PascalCase` such as `RouteDetail.vue`; keep stores in `camelCase` with the `xxxStore.js` suffix. Existing code uses Chinese comments and labels; keep new inline comments brief and consistent.

## Testing Guidelines
Testing is script-based, not a formal `pytest` suite. Run `cd backend && python3 tests/test_api_quick.py` for API smoke coverage and `cd backend && python3 tests/test_punctuality.py` for punctuality logic and endpoint checks. Use `check_db.py` or `check_data_detail.py` when changing schema or generated data. Start PostgreSQL and the backend first.

## Commit & Pull Request Guidelines
Recent commits use short Chinese change summaries such as `数据回放` and `操作记录+显示`. Keep commit subjects concise, specific, and focused on one change. For pull requests, include a short summary, affected modules, any SQL or config changes, frontend screenshots for UI updates, and the exact commands you ran to verify the change.

## Security & Configuration Tips
Copy `backend/config.example.json` to a local `backend/config.json` and never commit secrets. `backend/core/config.py` also supports environment-variable overrides such as `SF_511_API_KEY` and `TFNSW_API_KEY`. Do not commit GTFS archives, local logs, or generated frontend build output.
