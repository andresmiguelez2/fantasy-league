# AGENTS.md

## Architecture

- Docker Compose app with five containers: `backend_app` (python, FastAPI), `frontend_app`
  (Vite + React + TS + shadcn/Tailwind), `postgres_db`, `mongo_db`, `pgadmin`.
  Everything runs through Docker; there is no local-only dev path.
- Backend imports are rooted at the **repo root**, not `backend/`
  (`import backend.app...`, `PYTHONPATH=/workspace`). The FastAPI instance
  `server_app` lives in `backend/app/api/routers/server_requests.py`;
  `backend/main.py` only imports it.
- Postgres holds game data via raw SQL (psycopg2); Mongo stores additional state.
  Idempotent startup migrations (`ALTER TABLE ... IF NOT EXISTS`) run in the
  `server_requests.py` lifespan on every boot.
- A background polling loop (`backend/app/tasks.py`) starts with the app; set env
  `ENABLE_BACKGROUND_TASKS=false` to disable it during development.
- Frontend calls the backend at `${VITE_BACKEND_URL:-<hostname>:8000}`
  (`frontend/src/lib/api.ts`).

## Commands

- Start the full stack: `docker compose -f 'docker-compose.yml' up -d --build`
- Backend tests are pure unit tests (DB connections mocked with `unittest.mock`;
  no services needed). Run inside the container:
  - All: `docker exec backend_app python -m unittest discover -s tests -v`
    (container workdir is `/workspace/backend`)
  - Single module: `docker exec backend_app python -m unittest tests.test_market_router`
- Running backend code on the host requires `pip install -r backend/requirements.txt`
  (container uses Python 3.13; host may differ).
- Backend format check: `docker exec backend_app black --check .` (config in root
  `pyproject.toml`).
- Frontend (in `frontend/`): `npm run lint`, `npm run build`,
  `npm run format` / `npm run format:check`. Use npm — the Dockerfile installs with
  npm even though a stale `bun.lockb` also exists. No frontend test suite exists;
  frontend deps must be installed inside the container (`node_modules` is a Docker
  volume, so host installs don't reach it).

## Conventions

- Use **British English** in names, comments, and UI copy (`colour`, `centre`,
  `initialise`); framework/library keywords and APIs keep their native spelling.
- Verification loop: **format → lint → test**:
  - Backend: `docker exec backend_app black --check .` then
    `python -m unittest discover -s tests`
  - Frontend: `npm run format:check` then `npm run lint`
- Pylint is deliberately disabled (`.pylintrc` disables all); Black + Prettier
  enforce style. Note: `npm run lint` currently reports pre-existing errors in
  `.vite/deps/` caches and some `no-explicit-any` usages — compare against baseline
  rather than expecting zero output.
- Commits follow Conventional Commits, often with gitmoji (`feat:`, `fix: 🐛 ...`).
