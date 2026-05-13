Status: in progress

# Plan 0009 — Disk Doctor: active diagnosis + Quick Wins + Rescue Mode (v0.20.6)

## Context

**The core problem.** The app is passive. It waits for the user to navigate to a
category, scan it, interpret the numbers, and decide what to clean. Meanwhile the
actual disk diagnosis — running `du` surveys, finding which subdirectory is the
culprit, understanding which items are safe to delete right now — had to be done
manually outside the app.

Specific failures surfaced in this session:
1. `~/Library/Developer/Xcode/DocumentationIndex` (1–5 GB) was not in cleaners.py
   at all — the app couldn't even see it.
2. `~/Library/Developer/Xcode/iOS DeviceSupport` existed and was large but the app
   never said "this is your biggest recoverable item right now."
3. When the disk hit 200 MB free, the app showed nothing urgent. An engineer had to
   manually diagnose the problem from the terminal.
4. The biggest safe items across ALL categories were never surfaced in one place —
   the user had to know to look in each tab individually.

**The fix.** Three new capabilities, no AI required:

1. **Quick Wins** — after any scan, aggregate every safe-tier path from every
   category, rank by size descending, show the top 10 as a ready-to-clean list.
   One click per item. No category navigation needed.

2. **Rescue Mode** — when free disk < configurable threshold (default 10 GB),
   surface a prominent alert at the top of Overview with the specific large
   paths that can be cleaned right now, before the user even scans. Rule-based.
   Fires on startup. No scan needed.

3. **Smarter Xcode scanning** — add every Xcode subfolder individually so the
   scan shows per-item sizes (DerivedData, iOS DeviceSupport, watchOS DeviceSupport,
   tvOS DeviceSupport, DocumentationIndex, DeviceLogs, UserData temp).

## Approach

### A — Missing Xcode paths (cleaners.py)

Add to Xcode `safe` tier:
```python
("Xcode DocumentationIndex",      "~/Library/Developer/Xcode/DocumentationIndex"),
("Xcode DeviceLogs",              "~/Library/Developer/Xcode/DeviceLogs"),
("Xcode UserData temp",           "~/Library/Developer/Xcode/UserData"),
```

`DocumentationIndex` is the key gap — can be 1–5 GB on an active dev Mac. Xcode
rebuilds it from documentation bundles the next time you open the docs viewer.

### B — Quick Wins component (`QuickWins.tsx`)

After scanning, pull every path from every category's `safe` tier, sort by
`size_gb` descending, show the top 10 with:
- Path label + category badge
- Size in GB
- One-click `↓ Clean` button (calls `cleanPath(catId, path, label)` directly)
- Green `✓ Done` on completion

This directly answers "what should I delete right now?" without any tab navigation.

Appears in OverviewPanel between the action buttons and the 3-pane row.

### C — Rescue Mode (`RescueBanner.tsx`)

Triggered when `status.free_gb < threshold` (default: 10 GB, adjustable).

**Two states:**

*Before scan (disk critically low, no scan data yet):*
Shows a red urgent banner with hard-coded "best bet" commands — the paths most
likely to be large on any Mac, pre-computed without scanning:
```
Things to try right now (no scan needed):
• Xcode DerivedData   → typically 5–20 GB
• Xcode iOS DeviceSupport → typically 2–10 GB
• npm cache           → typically 0.5–5 GB
• Browser caches      → typically 1–5 GB
```
Each has a ↓ Clean button that fires immediately.

*After scan (data available):*
Shows the actual top 3 items from Quick Wins — specific sizes, not estimates.
"Your biggest recoverable items:"

Threshold: `free_gb / total_gb * 100 < 5%` → red (critical).
`free_gb < 10 GB` → orange (warning).

### D — DiskDoctor service (server.py)

New endpoint: `GET /api/doctor`

Returns a sorted list of the biggest cleanable paths across ALL currently-scanned
categories:
```json
{
  "free_gb": 2.5,
  "total_gb": 228,
  "free_pct": 1.1,
  "rescue_mode": true,
  "quick_wins": [
    {"category": "xcode", "label": "Xcode DerivedData", "path": "~/Library/...",
     "size_gb": 8.2, "tier": "safe"},
    ...
  ]
}
```

This is computed from the live scan data already in memory — no extra scanning.

### E — OverviewPanel wiring

New layout order (top → bottom):
1. `RescueBanner` — only shows when disk is low; gone when not needed
2. `PermissionBanner` — FDA issues
3. `HabitBanner` — growing categories
4. Action buttons (Scan / Clean safe / Clean opt-in)
5. **`QuickWins`** — top 10 safe items after scan ← NEW
6. 3-pane (hero · pie · terminal)
7. History banner
8. `SpaceBarChart`
9. Category cards

## Critical files

| File | Change |
|---|---|
| `web/cleaners.py` | Add DocumentationIndex, DeviceLogs, UserData to Xcode safe |
| `web/server.py` | Add `GET /api/doctor` endpoint |
| `apps/web/src/lib/types.ts` | Add `DoctorReport` type |
| `apps/web/src/lib/api.ts` | Add `api.doctor()` call |
| `apps/web/src/state/DashboardContext.tsx` | Add `doctorReport` state; load on scan completion |
| `apps/web/src/components/QuickWins.tsx` | New — top 10 safe items with clean buttons |
| `apps/web/src/components/RescueBanner.tsx` | New — low disk alert with immediate actions |
| `apps/web/src/components/OverviewPanel.tsx` | Wire QuickWins + RescueBanner |
| `xcode-cleanup.applescript` | kVersion 0.20.5 → 0.20.6 |
| `docs/CHANGELOG.md` | New entry |
| `plans/0009-…md` | This plan |

## Verification

1. With disk < 10 GB free: `RescueBanner` appears at top of Overview with
   "Your biggest recoverable items" or hard-coded estimates.
2. After scan: `QuickWins` shows top 10 safe items sorted by size with sizes.
3. Xcode category scan now returns `DocumentationIndex` as a separate path entry.
4. `GET /api/doctor` returns `quick_wins` sorted by `size_gb` descending.
5. Clicking a QuickWins item fires the clean and the button turns green.
6. `make check` passes.
