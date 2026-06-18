# Backend Migration Phases

## Phase 1

- Build FastAPI app bootstrap, config, database session management, auth, and core CRUD domains.
- Keep route handlers thin and move behavior into services and repositories.
- Mirror the current Next.js API surface gradually, starting with settings, conversations, customers, tickets, and knowledge.

## Phase 2

- Introduce domain events plus outbox publishing.
- Move webhook retries, campaign execution, SLA checks, follow-ups, and automation evaluation to async workers.
- Add Redis-backed task queue and idempotent workflow handlers.

## Phase 3

- Finalize provider and channel ports.
- Split read-heavy analytics/export logic into dedicated query services.
- Add adapter implementations for AI providers, Twilio, email, WhatsApp, Telegram, and future channels.
