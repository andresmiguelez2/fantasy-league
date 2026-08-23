# AGENTS.md

## Architecture

- Docker Compose app with five containers: `backend_app` (FastAPI), `frontend_app`
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
  (`frontend/src/lib/api.ts`); backend CORS allows only `localhost:5173` and
  `127.0.0.1:5173`.

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
- First-time database setup (schema restore from `resources/database_schema`, seed
  scripts): follow `docs/SETUP.md`.

## First-run setup

- Create `secrets/db.env`, `secrets/mongo.env`, `secrets/pgadmin.env` from the
  templates in `docs/SETUP.md` before `docker compose up`; keep `DB_NAME`,
  `POSTGRES_DB` and `DATABASE_URL` consistent with each other.
- Postgres starts empty: restore the dump in `resources/database_schema` via pgAdmin
  (:5050) per `docs/SETUP.md`, then create the `unaccent` extension.
- Seed data once ever: `docker exec backend_app python scripts/insert_fixtures.py`
  plus `insert_team_crests.py` and `insert_footballers.py`.
- Set `JWT_SECRET_KEY` or auth falls back to an insecure default key (see
  `docs/AUTHENTICATION.md`).

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
- Feature work convention (see `.opencode/agents/code-developer.md`): cut a
  `feature/<kebab-name>` branch off the active branch, commit incrementally, open a
  PR rather than merging directly; run the `frontend-qa` subagent after UI changes.
  `.github/agents/consistency-antagonism-review.agent.md` reviews paired/inverse
  logic for drift.
- No CI workflows exist — verification is manual via the commands above.
