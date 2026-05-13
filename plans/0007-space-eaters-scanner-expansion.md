Status: shipped (commit pending merge, v0.20.1)

# Plan 0007 — Space Eaters: scanner expansion + path fixes + iCloud Drive (v0.20.1)

## Context

**Why this change.** Most categories reported 0 GB when there is real recoverable
space. The user called this out directly:

> *"Browsers can't be zero — there is a cache. Telegram has cache. We need to really
> study the Application Support stuff too. We even need to know that just because we
> don't keep Mobile Documents from iCloud Drive on our device, they still live on
> iCloud and we can make sure that says that and it is true and we can then reclaim
> that space SAFELY from iCloud Drive too!"*

Three root causes:
1. **Stale macOS paths.** Safari moved to a container in macOS Ventura+;
   the old `~/Library/Caches/com.apple.Safari` path is now empty.
   `~/Library/WebKit` (offline storage, 1–3 GB) was never tracked.
   Chrome's per-profile cache is in `Application Support`, not just `Caches`.
2. **Missing apps.** Telegram (5–20 GB group container), WhatsApp,
   Signal attachments, VS Code workspace state, and per-app `Code Cache/`
   directories were never added.
3. **Never-surfaced space eaters.** iOS device backups
   (`~/Library/Application Support/MobileSync/Backup`, routinely 10–80 GB),
   developer caches (npm, pip, cargo, gradle), and the iCloud Drive local
   cache were completely invisible to Dustpan.

**"Space Eaters"** is the new name for the category that exposes the biggest
space hoarders that don't fit neatly into the existing categories.

## Approach

### A — Fix existing paths that silently return 0

| Category | Old path (broken) | New/additional path |
|---|---|---|
| Browsers | `~/Library/Caches/com.apple.Safari` (empty in Ventura+) | Add `~/Library/Containers/com.apple.Safari/Data/Library/Caches` |
| Browsers | (missing) | Add `~/Library/WebKit` — offline storage, often 1–3 GB |
| Browsers | Chrome only had `Caches/Google/Chrome` | Also add Application Support profile root for subdir cache |
| Apps | Slack only had Service Worker | Add `~/Library/Application Support/Slack/Cache` + `Code Cache` |
| Apps | Discord only had `discord/Cache` | Add `blob_storage`, `Code Cache`, capital-D `Discord` variant |
| Apps | Spotify had `Caches/com.spotify.client` | Add `Application Support/Spotify/PersistentCache` + `Storage` |

### B — Add missing apps to the Apps category

| App | Path | Typical size |
|---|---|---|
| Telegram (iOS-based) | `~/Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram` | 2–20 GB |
| Telegram Desktop | `~/Library/Application Support/Telegram Desktop` | 1–5 GB |
| WhatsApp | `~/Library/Application Support/WhatsApp` | 0.5–5 GB |
| Signal attachments | `~/Library/Application Support/Signal/attachments.noindex` | 0.5–10 GB |
| VS Code cache | `~/Library/Application Support/Code/Cache` + `CachedData` | 0.5–3 GB |
| VS Code workspace | `~/Library/Application Support/Code/User/workspaceStorage` | 0.2–2 GB |
| Figma | `~/Library/Application Support/Figma` | 0.5–3 GB |

### C — New "Space Eaters" category

The category catches the biggest space consumers that aren't caches — they're
real user data or build artifacts the user may not know they're keeping.

**`caution` tier (surface-only — never auto-delete):**
- iOS device backups: `~/Library/Application Support/MobileSync/Backup` — easily
  10–80 GB per device. Cannot be auto-cleaned; user must review in Finder.
- Photos library: `~/Pictures/Photos Library.photoslibrary` — informational only.
- Steam game data: `~/Library/Application Support/Steam/steamapps` — games.

**`probably_safe` tier (caches that can be rebuilt):**
- npm cache: `~/.npm`
- pip cache: `~/Library/Caches/pip`
- Cargo registry: `~/.cargo/registry`
- Gradle caches: `~/.gradle/caches`
- Go module cache: `~/go/pkg/mod/cache`
- Yarn cache: `~/.yarn/cache`
- pnpm store: `~/.pnpm-store`
- Ruby gems cache: `~/.gem`

**Actions:**
- Show iOS backup sizes (informational, sorted)
- Clean npm/pip/cargo/gradle caches (with explicit cost notes)
- Show top-25 largest files in ~/Documents, ~/Desktop

### D — New "iCloud Drive" category

This is special: `~/Library/Mobile Documents` holds the local copy of every
file synced by iCloud Drive. Even when "Optimize Mac Storage" is off, files
that haven't been accessed recently may already be stubs (`.icloud` extension).

**Key insight for users:** Clearing this space is completely safe because
**all files remain on iCloud**. macOS re-downloads them the next time you
open them. This is exactly what "Optimize Mac Storage" does automatically.

**Groups (measurement only — no `rm -rf`):**
- `safe` tier: `~/Library/Mobile Documents` (total local iCloud cache)
- `safe` tier: `~/Library/CloudStorage` (newer iCloud Drive format, Monterey+)

**Actions (use `brctl evict`, not `rm -rf`):**
- Show local iCloud Drive footprint broken down by app container
- "Evict iCloud Drive cache" — finds all non-stub locally-cached files and
  runs `brctl evict <file>` on each. Files are NOT deleted — they become stubs
  (`*.icloud`) and re-download on demand. Completely reversible.
- Show `.icloud` stubs vs locally-present files
- Link to macOS "Optimize Mac Storage" setting as the permanent fix

### E — Sidebar updates

Add two new tabs:
- `{"id": "space-eaters", "label": "Space Eaters", "category": "space-eaters"}` (Flame icon)
- `{"id": "icloud", "label": "iCloud Drive", "category": "icloud"}` (Cloud icon)

## Critical files

| File | Change |
|---|---|
| `web/cleaners.py` | Fix browser paths; expand apps; add `space-eaters` + `icloud` categories; update TABS |
| `apps/web/src/components/icons.tsx` | Add `Flame`, `Cloud`, `HardDriveDownload` icons |
| `xcode-cleanup.applescript` | kVersion 0.20.0 → 0.20.1 |
| `docs/CHANGELOG.md` | New `[0.20.1]` entry |
| `plans/0007-space-eaters-scanner-expansion.md` | This plan |
| `plans/README.md` | Index row for 0007 |

## Verification

1. `make check` passes.
2. After `make ui` + scan: browsers show non-zero GB (Chrome cache, Safari container,
   WebKit storage each contribute).
3. Apps shows Telegram GB (if Telegram installed).
4. "Space Eaters" tab shows iOS backup size (if any backups exist in MobileSync).
5. "iCloud Drive" tab shows local footprint from `~/Library/Mobile Documents`.
6. `POST /api/category/icloud/scan` returns totals > 0 if user has any iCloud Drive content.
7. The `brctl evict` action output shows "Evicted: path/to/file" lines and ends with a summary.
