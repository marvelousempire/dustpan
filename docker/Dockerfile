# ── Stage 1: Build React UI ──────────────────────────────────────────────────
FROM node:20-slim AS builder
RUN npm install -g pnpm@9

WORKDIR /dustpan
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/ apps/

RUN pnpm install --frozen-lockfile
RUN pnpm --filter @cleanup-hub/web build

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /dustpan

# System deps (psycopg2 binary needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY web/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# App source
COPY web/ web/

# Copy built React app from builder stage — server.py looks here:
#   REACT_DIST_CANDIDATES = [APPS_DIR / "web" / "dist", ...]
#   APPS_DIR = REPO_DIR / "apps"  →  /dustpan/apps
COPY --from=builder /dustpan/apps/web/dist apps/web/dist

EXPOSE 8765

CMD ["python", "web/server.py"]
