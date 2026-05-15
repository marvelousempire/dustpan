# Plan 0027 — Disk Growth Watch — sliding 3m/9m/20m deltas to diagnose sudden fill-ups

**Status:** shipped (implementation landed — replace with `commit <sha>` when tagged)

## Context
The current app only shows aggregate free_gb via /api/status and /api/live. When the disk hits 100% full, users see the alarm but have no visibility into *what* grew in the last few minutes. The complaint: "as the memory fills up nothing is showing why we are 100% maxed out." We need per-directory change tracking over short sliding windows (3 min, 9 min, 20 min) so the UI can surface "DerivedData grew +4.2 GB (+38%) in the last 3 min" or "Containers/… jumped 12% in 9 min". This turns the "why am I full?" question into actionable, time-bounded data. It complements SADPA, Emergency panel, and Space Survey by adding a temporal "growth rate" dimension.

## Approach
Add an in-memory GrowthTracker singleton in the Python backend that:
- Maintains a fixed set of watch paths (key ones from cleaners: DerivedData, iOS DeviceSupport, mediaanalysisd/Data, DocumentationIndex, ~/Library/Containers/* top-level, ~/Library/Developer, Docker VM files, etc.).
- Every 30 seconds runs parallel `du -sk` (or `docker system df` for Docker) and records (timestamp, size_kb) per path in a ring buffer sized for ~20 min (40 samples).
- On query, computes for each path the delta GB and % change over the closest sample to -3min, -9min, -20min (or oldest available).
- Exposes `GET /api/growth` returning {paths: [{id, label, current_gb, deltas: {m3: {gb, pct}, m9:..., m20:...}}], ts: now}.
- The /api/live SSE gains an optional "growth" event frame every minute (throttled) so the UI can update live without polling.
- Frontend: new "Growth Watch" sub-section (or dedicated tab if volume grows) in Overview or a lightweight panel that shows top-5 fastest growers with color-coded % (red for >10%/3min). Uses existing fmt + motion for the list. No new heavy UI; re-uses MetricCell / Card patterns.
- No DB persistence needed (session-only, resets on restart); survives the "disk at zero" case because sampling is lightweight and non-blocking.
- Paths are static list in cleaners.py under a new "growth_watch_paths" key for easy extension.

This is the single chosen approach: lightweight ring-buffer + periodic sampler + one new endpoint + small UI delta badges. Alternatives (full filesystem watcher like fsevents, per-file history, long-term DB) are out of scope.

## Critical files
- plans/0027-disk-growth-watch-3m-9m-20m-deltas.md (this file)
- web/cleaners.py — add growth_watch_paths list + labels
- web/server.py — GrowthTracker class, estimate_growth(), new /api/growth route, live SSE growth frame
- apps/web/src/lib/api.ts — new growth() fetch + GrowthDelta types
- apps/web/src/lib/types.ts — GrowthSnapshot, PathDelta interfaces
- apps/web/src/components/OverviewPanel.tsx or new GrowthWatch.tsx — render the delta list (or embed in Overview hero)
- apps/web/src/state/DashboardContext.tsx — optional: expose growth state if live-updated

## Verification
Run `make ui`, open Overview (or new Growth tab), trigger a large build or Docker pull, watch the 3m/9m deltas climb in real time. Command to verify backend: `curl -s http://127.0.0.1:8765/api/growth | python3 -m json.tool` shows non-zero deltas after activity. UI shows red badges for rapid growers within 20s of change. No >2% CPU impact from sampler (confirmed via `top` during test). Plan is complete when the three time windows are populated and the UI surfaces at least the top 3 changing paths with % and GB.

## Out of scope
- Long-term historical storage or charts beyond current session
- Watching every directory on disk
- Automatic cleanup triggers based on growth rate (future plan)
- Mobile / Shortcut surface for this data
