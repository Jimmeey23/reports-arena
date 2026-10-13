# Hosting

The production UI is https://reports-arena.vercel.app. Vercel serves the current
frontend from `studio-app/static` and proxies `/api/*` to
https://reports-arena-production.up.railway.app. Upload headers, JSON bodies,
report downloads and polling stay on the Vercel origin in the browser.

## Vercel

Import the repository with the root directory left at the repository root.
`vercel.json` runs `node scripts/build-vercel.cjs` and serves `vercel-public`.
The output contains only frontend assets; no report data or API keys are bundled.
The backend hostname is public configuration in the rewrite destination.

## Railway

Deploy the repository root using `Dockerfile`. The image installs the pinned
Python dependencies and starts `studio-app/server.py`. Set `PORT=8080`, matching
the public domain's target port. The process binds to `0.0.0.0`.

Attach the service's persistent volume at `/data`. The server detects
`RAILWAY_VOLUME_MOUNT_PATH` and stores uploads, SQLite databases and generated
reports beneath it. `P57_STORAGE_DIR` can override that storage location. Missing
bundled reports are copied into a fresh volume. To publish a revised bundled
report under its existing dashboard entry, increment its `bundle_revision` in the
manifest; startup refreshes that run in place only when the bundled revision is
newer. Deploy/restart the Railway backend to apply this update; a frontend-only
Vercel deploy does not update the persistent report volume. Deleted reports stay
deleted. Use one backend instance: generation jobs and progress are currently
in memory.

Server variables:

- `P57_ACCESS_CODE`: **required.** Shared access code for the sign-in page at
  `/api/login`. Every `/api/*` route except `/api/health` needs the session
  cookie it issues. Without it the API answers loopback requests only, so a
  deployment that is missing it stays closed. Changing the code signs everyone out.
- `OPENAI_API_KEY`: enables the OpenAI-compatible AI client.
- `P57_AI_MODEL`: optional model override.
- `P57_AI_BASE`: optional provider endpoint override (environment only; the app
  never accepts an endpoint from a request, because the key is sent to it).
- `SUPABASE_URL` and `SUPABASE_KEY`: optional Supabase persistence.

Run `studio-app/sql/supabase-schema.sql` in Supabase before enabling that backend.
Supabase stores metadata, edits, chat history and configuration; report HTML and
record files remain on the Railway volume. Keep secrets on Railway, outside Git
and outside the frontend output.

## Verification

Check `/api/state`, `/api/ai/status` and a saved `/api/report/<run>/report` through
the Vercel domain. Then upload a fresh CSV, generate a review, poll its job and
open the generated report. A static `/api/state.json` snapshot is no longer used.
