Status: implemented in working tree (pending commit, v0.28.3)

# Plan 0034 — Disk Activity and Server Bottom Density

## Context

The Server Performance page now has strong live monitoring, but the lower panels still spend too much vertical space for the amount of information shown. The Disk/Overview page also needs a live, user-readable section showing the latest files added, the likely application source, and the application that can open or run them.

The intended outcome is a richer, more immersive dashboard without making cleanup more dangerous: monitoring stays read-only, cleanup stays approval-gated, and every new section uses compact live meters, charts, and plain-English labels.

## Tasks (precise todos)

1. **Compress the bottom Server Performance layout**
   - **Literal what-to-do** — Rework the lower `ServerPerformancePanel` overview area so Services, Top Processes, Network Monitor, and DustBench use denser cards/tables and show more information above the fold. Add progress meters where a row has status, load, reachability, count, or benchmark score.
   - **Files touched** — `apps/web/src/components/ServerPerformancePanel.tsx`, `apps/web/src/components/performance/ServiceGrid.tsx`, `apps/web/src/components/performance/ProcessLeaderboard.tsx`, `apps/web/src/components/performance/NetworkFlowTable.tsx`, `apps/web/src/components/performance/BenchmarkCard.tsx`
   - **Dependencies** — None.
   - **Owner-agent** — frontend dashboard engineer.

2. **Add read-only latest-file activity backend**
   - **Literal what-to-do** — Add a stdlib-only backend probe that samples recent files from safe user-facing locations such as `~/Downloads`, `~/Desktop`, `~/Documents`, and selected development folders. Return filename, path, size, modified/created timestamp when available, extension, inferred source app, inferred opener/runner app, confidence, and a safe meter score. Do not crawl the full disk.
   - **Files touched** — `web/server.py`, optionally `web/performance/activity_files.py`
   - **Dependencies** — None.
   - **Owner-agent** — backend/platform probe engineer.

3. **Expose latest-file activity through typed API**
   - **Literal what-to-do** — Add `GET /api/disk/latest-files` or fold the payload into an existing Overview-safe endpoint, then add TypeScript types and an API client method.
   - **Files touched** — `web/server.py`, `apps/web/src/lib/api.ts`, `apps/web/src/lib/types.ts`
   - **Dependencies** — Task 2.
   - **Owner-agent** — API integration engineer.

4. **Add Disk page latest-file section**
   - **Literal what-to-do** — Add a distinct colored section to `OverviewPanel` for "Latest Files Added" with live meters, compact charts, and row labels for file, likely source application, and likely application that opens/runs it. Use a different background color from the surrounding cards so it reads as a new live activity zone.
   - **Files touched** — `apps/web/src/components/OverviewPanel.tsx`, new component under `apps/web/src/components/` if useful.
   - **Dependencies** — Task 3.
   - **Owner-agent** — frontend dashboard engineer.

5. **Release discipline**
   - **Literal what-to-do** — Bump DustPan to the next patch version, add a top changelog record, update `docs/Feature Ledger.md`, and update the Tech Stack modal if a new backend probe/component class is introduced.
   - **Files touched** — `package.json`, `apps/web/package.json`, `apps/web-next/package.json`, `dustpan.applescript`, `docs/CHANGELOG.md`, `docs/Feature Ledger.md`, possibly `apps/web/src/components/ChangelogModal.tsx`
   - **Dependencies** — Tasks 1-4.
   - **Owner-agent** — release steward.

## Critical files

- `web/server.py`
- `web/performance/activity_files.py` if the probe is split out
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/types.ts`
- `apps/web/src/components/OverviewPanel.tsx`
- `apps/web/src/components/ServerPerformancePanel.tsx`
- `apps/web/src/components/performance/ServiceGrid.tsx`
- `apps/web/src/components/performance/ProcessLeaderboard.tsx`
- `apps/web/src/components/performance/NetworkFlowTable.tsx`
- `apps/web/src/components/performance/BenchmarkCard.tsx`
- `apps/web/src/components/ChangelogModal.tsx` if Tech Stack needs a new row
- `package.json`
- `apps/web/package.json`
- `apps/web-next/package.json`
- `dustpan.applescript`
- `docs/CHANGELOG.md`
- `docs/Feature Ledger.md`

## Verification

1. **TypeScript**
   - **Literal command** — `pnpm --dir apps/web exec tsc --noEmit --pretty false`
   - **Expected output** — exits `0` with no TypeScript errors.

2. **Python syntax**
   - **Literal command** — `python3 -m py_compile web/server.py web/performance/activity_files.py`
   - **Expected output** — exits `0`; if `activity_files.py` is not created, compile `web/server.py` only.

3. **Whitespace**
   - **Literal command** — `git diff --check`
   - **Expected output** — exits `0`.

4. **Browser smoke**
   - **Literal command** — `make ui`
   - **Expected output** — DustPan opens, Server Performance lower panels are denser, and the Disk/Overview page shows Latest Files Added with colored background, charts, and live meters.

5. **API smoke**
   - **Literal command** — `curl -fsS http://127.0.0.1:8765/api/disk/latest-files | python3 -m json.tool`
   - **Expected output** — JSON includes a bounded list of recent files with source/open/run app inference fields.

## Out of scope

- No destructive file action from the latest-file section.
- No full-disk crawl.
- No background daemon or persistent file watcher.
- No kernel-level file provenance claims; app/source labels are best-effort inference from location, extension, and metadata available without special permissions.
