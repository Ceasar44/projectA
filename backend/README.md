# Owly FastAPI Backend

This directory contains the modular-monolith FastAPI backend that mirrors and gradually replaces the current Next.js API routes.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

The backend now starts in development without extra secrets:

- `DATABASE_URL` defaults to `postgresql://postgres:postgres@localhost:5432/owly`
- `JWT_SECRET` defaults to `dev-secret-change-me`

You can still override both in `backend/.env`.

`AUTO_CREATE_SCHEMA` now defaults to `false`. Use Alembic migrations instead of relying on runtime schema creation.

## Replace the current Next.js API

The frontend still calls relative `/api/...` paths. To point those calls at FastAPI without rewriting every page:

1. Start FastAPI on `http://localhost:8000`
2. Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in the repo root `.env`
3. Start the Next.js frontend as usual

When `NEXT_PUBLIC_API_BASE_URL` is set, client-side `fetch("/api/...")` calls are transparently forwarded to FastAPI instead of the local `app/api` handlers.

The frontend shim also forces `credentials: "include"` for those API calls so auth cookies keep working across `localhost:3000` -> `localhost:8000`.

## Docker

```bash
cd backend
docker compose up --build
```

This starts:

- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `backend` on `localhost:8000`

## Current phases

- Phase 1: API foundation, database layer, auth, core domains
- Phase 2: domain events, outbox, Redis task queue ports, async workflows
- Phase 3: provider/channel adapters, richer query services, extensibility seams
