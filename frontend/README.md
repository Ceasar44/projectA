# Owly Frontend

This directory contains the standalone Next.js frontend migrated from the original TypeScript app. It is configured to talk directly to the FastAPI backend in `../backend`.

## Run

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create `.env.local` from `.env.example` and point `NEXT_PUBLIC_API_BASE_URL` to the FastAPI server.

3. Start the frontend:

```bash
npm run dev
```

## Notes

- Client-side `/api/...` fetch calls are rewritten to `NEXT_PUBLIC_API_BASE_URL` in `src/components/providers.tsx`.
- Auth-protected pages are guarded by `src/middleware.ts` using the `owly-token` cookie set by the backend.
- The dashboard homepage was converted to client-side data loading so the frontend no longer depends on Prisma or the original TS API routes.
