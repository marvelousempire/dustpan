Status: shipped (commit pending merge, v0.20.0)

# Plan 0006 — Docker stack + AI engine + habit learning (v0.20.0)

## Context

**Why now.** v0.19.9 adds the AI Settings panel (API keys stored in
`localStorage`) and the horizontal space-usage bar chart. Those are the UI
shells. The features that give them meaning — AI summaries, habit-based
recommendations, usage history, and Ollama — all require:

1. **Persistent state across sessions** (habit records, run history, API key
   vault). `localStorage` is fragile, per-browser, unencrypted, and can't be
   queried for trends. A proper database is required.

2. **Server-side AI calls.** The Python backend needs to call OpenAI / Anthropic
   / Ollama. Keys must never leave the server — exposing them to the browser JS
   bundle is a security anti-pattern.

3. **Ollama.** Self-hosted local models are the killer feature for privacy-first
   users. Ollama is most cleanly run as a Docker service alongside the app
   so the whole stack is `./go`-launchable.

**Binary rule (plan 0004):** Dustpan needs persistent state → Docker stack. The
canonical template (`ai-skills-library/templates/docker-stack/`) is ready.

**User's intent (verbatim):** *"with Docker we can be running the Ollama stuff
through that so it's all self-contained… that's when we go ahead and implement
the whole database part… and they're gonna need Docker for that too."*

## Approach

### A — Stack topology

```
docker-compose.yml services:
  app      built (Dockerfile:runner — the existing Python server)
  db       pgvector/pgvector:pg16 (usage history, keys vault, habit records)
  caddy    caddy:2-alpine          (HTTPS, reverse proxy)
  ollama   ollama/ollama:latest    (local LLM, GPU-aware, optional — add when user wants it)
```

Ollama ships as an **optional service** — commented out in the base
`docker-compose.yml`, activated with `docker compose --profile ollama up`.

### B — Database schema (PostgreSQL)

**`api_keys`** — encrypted key vault (never sent to the browser)
```sql
id          serial primary key,
provider    text not null,          -- 'openai' | 'anthropic' | 'perplexity' | 'groq' | 'gemini' | 'ollama'
key_enc     bytea not null,         -- AES-256-GCM encrypted, key = DUSTPAN_MASTER_KEY env var
created_at  timestamptz default now(),
updated_at  timestamptz default now()
```

**`runs`** — every scan + clean operation
```sql
id          serial primary key,
ts          timestamptz default now(),
mode        text not null,          -- 'scan' | 'clean'
category    text,                   -- NULL = all-categories op
tier        text,                   -- 'safe' | 'probably_safe' | NULL
freed_gb    numeric(10,3),
duration_ms int,
disk_before_gb numeric(10,1),
disk_after_gb  numeric(10,1)
```

**`category_snapshots`** — periodic space readings (drives the habit engine)
```sql
id          serial primary key,
ts          timestamptz default now(),
category    text not null,
safe_gb     numeric(10,3),
optin_gb    numeric(10,3),
caution_gb  numeric(10,3)
```

**`habits`** — derived from snapshots (computed, cached)
```sql
id          serial primary key,
category    text not null,
computed_at timestamptz default now(),
growth_gb_per_week  numeric(8,4),   -- rolling 4-week slope
days_to_threshold   int,            -- estimated days until threshold
threshold_gb        numeric(8,2),   -- user-configurable, default per category
recommendation      text            -- AI-generated or rule-based
```

### C — New Python endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/settings/keys` | Save encrypted API key for a provider |
| `GET /api/settings/keys` | Return providers that have keys (no key content) |
| `DELETE /api/settings/keys/{provider}` | Delete a key |
| `GET /api/settings/ollama` | Return configured Ollama URL + model |
| `POST /api/settings/ollama` | Update Ollama settings |
| `GET /api/habits` | Return computed habit records |
| `GET /api/runs` | Return run history (paginated) |
| `POST /api/ai/summary` | Generate AI summary of the last scan (calls the configured provider) |
| `POST /api/ai/recommend` | AI recommendation for a category based on habit data |

### D — AI summary feature

After every scan completes, the backend can optionally call the configured AI
provider with a structured prompt:

```
You are Dustpan's disk cleanup assistant. Here is the current scan summary:

Category: Xcode
  Safe to delete: 14.2 GB (DerivedData, DeviceSupport)
  Opt-in: 3.1 GB (SwiftPM caches)
  Caution: 0.8 GB (review manually)

Growth trend: +2.1 GB/week for the past 4 weeks.
Last cleaned: 18 days ago.

Give a 2-sentence plain-English recommendation.
```

The summary is stored in `habits.recommendation` and surfaced in the UI
as a chip below each category card on the Overview page.

### E — Habit learning engine

A background job (runs after every scan, invoked by the `POST /api/category/<id>/scan`
handler) writes a row to `category_snapshots`. A weekly-ish aggregation job
computes `growth_gb_per_week` using a simple linear regression over the last
4 weeks of snapshots. When `days_to_threshold <= 14`, the UI surfaces a
"⚠ Time to clean Xcode — it's been growing 2.1 GB/week" banner.

**No ML required.** The first version uses a linear slope + threshold rule.
AI is used only for the human-friendly recommendation text, not for the
prediction itself. The prediction is math.

### F — Ollama integration

When the user configures Ollama (Docker service or external URL), the
`/api/ai/summary` and `/api/ai/recommend` endpoints use the OpenAI-compatible
API that Ollama exposes (`POST http://ollama:11434/v1/chat/completions`).
Model name is configurable (default: `llama3.2`). This makes Ollama a first-class
provider — no special code path beyond a different base URL.

### G — Migration path for existing users (no Docker)

The Docker stack is **opt-in**. Existing `make ui` users are unaffected. The
`/api/settings/keys` endpoint returns 501 when no DB is configured, and the
UI shows a banner: *"Enable Docker mode for secure key storage and AI features."*
API keys typed into the Settings panel fall back to `localStorage` with a
warning. Habit tracking simply doesn't run in non-Docker mode.

### H — `./go` bootstrap

Copy the `templates/docker-stack/` template, rename services, add the
`ollama` optional profile, add the `DUSTPAN_MASTER_KEY` env var to
`.env.example`. The five-minute setup is:

```sh
cp -r ~/Developer/ai-skills-library/.../templates/docker-stack/* ./docker/
./docker/go
```

Dustpan's existing `make ui` path stays — the server.py Python process can run
with or without a DB.

## Critical files

| File | Change |
|---|---|
| `docker/docker-compose.yml` | app + db + caddy + ollama (optional profile) |
| `docker/Dockerfile` | Python runner (from template) |
| `docker/Caddyfile` | HTTPS reverse proxy |
| `docker/.env.example` | `POSTGRES_*`, `CADDY_HOST`, `DUSTPAN_MASTER_KEY`, `OLLAMA_MODEL` |
| `docker/go` | one-shot bootstrap |
| `web/server.py` | new endpoints (settings/keys, habits, runs, ai/*); DB connection pool (psycopg2); optional — no DB = graceful 501 |
| `web/db.py` | new module — connection pool, migration runner, schema DDL |
| `web/ai.py` | new module — provider dispatch (OpenAI SDK + Ollama OpenAI-compat) |
| `apps/web/src/components/AISettingsPanel.tsx` | add "keys saved on server" state once Docker mode detected; migrate from localStorage |
| `apps/web/src/components/HabitBanner.tsx` | new — per-category banner shown when `days_to_threshold <= 14` |
| `apps/web/src/components/OverviewPanel.tsx` | wire AI summary chip below category cards; wire HabitBanner |
| `plans/0006-docker-ai-habits-engine.md` | this plan |
| `plans/README.md` | index row |
| `docs/CHANGELOG.md` | v0.20.0 entry |
| `xcode-cleanup.applescript` | kVersion 0.19.9 → 0.20.0 |

## Verification

1. `./docker/go` brings the stack up at `https://localhost` with Caddy HTTPS.
2. `POST /api/settings/keys` with `{"provider":"openai","key":"sk-…"}` returns 200; key is NOT visible in `GET /api/settings/keys` response.
3. After running a scan, `/api/habits` returns growth slope data.
4. `POST /api/ai/summary` with an OpenAI key returns a 2-sentence recommendation.
5. Ollama path: start `ollama serve` or `docker compose --profile ollama up`, set model to `llama3.2`, same `/api/ai/summary` endpoint works.
6. No-Docker path: `make ui` still works, `/api/settings/keys` returns `{"error":"no_db","message":"Enable Docker mode..."}`, Settings panel shows the fallback warning.
7. After 2+ weeks of usage, `habits.days_to_threshold <= 14` triggers the HabitBanner in the UI for the relevant category.
