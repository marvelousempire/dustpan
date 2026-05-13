Status: shipped (commit pending merge, v0.20.3)

# Plan 0008 — Fix zeroed sections: permission detection + path bugs + UX (v0.20.3)

## Context

**Root cause audit.** Most zeroed sections have one of three causes:

1. **macOS TCC silently blocks `du`** (biggest bug). `_measure_path` runs
   `subprocess.check_output(["du", "-sk", path], stderr=subprocess.DEVNULL)`.
   For any directory protected by macOS transparency/consent (Full Disk Access) —
   `~/Downloads`, `~/Library/Containers/*`, `~/Library/Group Containers/*`,
   Notes, Safari, Backups, iCloud — `du` exits non-zero with
   `Operation not permitted` on stderr. The `DEVNULL` throws that away silently,
   `CalledProcessError` is caught, and `size_kb` stays 0. The path exists, the
   data exists, but Dustpan sees 0. **Fix: detect the permission error and surface
   a "Grant Full Disk Access to Terminal" banner in the UI.**

2. **Structurally broken categories:**
   - **Archives** has `safe=[], probably_safe=[], caution=[]` — zero measurement
     paths. It always shows 0 regardless of permissions.
   - **System** has `"tm-snapshots"` as a path — `os.path.expanduser("tm-snapshots")`
     returns `"tm-snapshots"` (unchanged), `os.path.exists("tm-snapshots")` = False,
     so it silently returns 0 forever.
   - **iCloud** measures `~/Library/Mobile Documents` as a whole but doesn't break
     it down by app, and doesn't measure Notes Group Container at all.

3. **Clean button text confusion.** When `totals.safe < 0.01` after a scan, the
   button says "· scan first" — even when the user just scanned and everything IS
   clean. It should say "· all clean ✓" in that case.

## Approach

### A — `_measure_path`: detect and surface permission errors

Replace `subprocess.check_output(..., stderr=DEVNULL)` with `subprocess.run(...,
capture_output=True)`. Check `result.returncode` and `result.stderr` for
`"Operation not permitted"` or `"Permission denied"`. Return a new sixth value:
`permission_denied: bool`.

```python
def _measure_path(args):
    group_name, label, path = args
    expanded = os.path.expanduser(path)
    exists = os.path.exists(expanded)
    size_kb = 0
    permission_denied = False
    if exists:
        try:
            r = subprocess.run(["du", "-sk", expanded],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                size_kb = int(r.stdout.split()[0])
            elif ("Operation not permitted" in r.stderr
                  or "Permission denied" in r.stderr):
                permission_denied = True
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass
    return (group_name, label, path, size_kb, exists, permission_denied)
```

### B — `scan_category`: propagate `permission_denied` into response

Track `permission_denied_count` across all paths and include in the JSON response.
Also track `permission_denied_paths` (list of labels) so the frontend can show
exactly which paths need FDA.

```python
"permission_denied_count": sum(1 for ...),
"permission_denied_paths": [label for ... if denied],
```

### C — Frontend: `PermissionBanner` component

New `apps/web/src/components/PermissionBanner.tsx`. Shown in OverviewPanel when
ANY scanned category has `permission_denied_count > 0`. Dismissed via localStorage.

Banner content:
- **Headline:** "🔐 Full Disk Access needed for accurate results"
- **Body:** "Dustpan measures disk usage with `du`. macOS blocks `du` for protected
  directories (Downloads, Safari, iCloud, Notes, device backups) without Full Disk
  Access. Without it, those sections report 0 GB even when they contain data."
- **Steps:** System Settings → Privacy & Security → Full Disk Access → add Terminal
  (or the app you use: iTerm2, Warp, etc.) → restart Terminal → re-scan
- **Paths affected:** bullet list of the `permission_denied_paths` from scan
- **Dismiss:** "Got it" button that sets `localStorage("dustpan-fda-dismissed")`

### D — Fix Archives (always 0)

Add real measurement paths to caution:

```python
"caution": [
    ("~/Downloads  (total folder — review individually)",  "~/Downloads"),
    ("~/Desktop   (large files accumulate here)",           "~/Desktop"),
    ("~/Documents (exports, project archives)",             "~/Documents"),
],
```

This gives Archives something to measure. The actions still do the
smarter extension-filtered find. The caution entries show total folder sizes so
users understand the scope before using actions.

### E — Fix System (fake `tm-snapshots` path)

Remove `"tm-snapshots"` from groups/caution — it's not a real path.
The Time Machine snapshot action already handles this correctly. The
informational `show-system-updates` action also stays.

Add instead:
```python
("Diagnostic reports log folder", "~/Library/Logs"),
```
`~/Library/Logs` exists and typically has 50–200 MB of app logs.

### F — Expand iCloud category (Notes + per-app breakdown)

Add to `caution` tier so sizes are shown but never auto-deleted:

```python
("Notes app local data (photos, attachments)", "~/Library/Group Containers/group.com.apple.notes"),
("Notes iCloud sync folder",                   "~/Library/Mobile Documents/iCloud~com~apple~Notes"),
("Pages documents (iCloud)",                   "~/Library/Mobile Documents/com~apple~Pages"),
("Numbers documents (iCloud)",                 "~/Library/Mobile Documents/com~apple~Numbers"),
("Keynote documents (iCloud)",                 "~/Library/Mobile Documents/com~apple~Keynote"),
("Reminders local data",                       "~/Library/Group Containers/group.com.apple.reminders"),
("Mail local cache + attachments",             "~/Library/Containers/com.apple.mail"),
```

Add action `"show-notes-size"` to explain Notes storage and how to turn off
local Notes sync (System Settings → Apple ID → iCloud → Notes → toggle off).
Add action `"evict-icloud-app-docs"` that runs `brctl evict` specifically on
Pages, Numbers, Keynote documents in Mobile Documents.

### G — Fix clean button text

In `OverviewPanel.tsx`, change the button label logic:

```tsx
// Before (confusing)
{totals.safe >= 0.01 ? `· ${fmt(totals.safe)} GB` : "· scan first"}

// After (accurate)
{totals.safe >= 0.01
  ? `· ${fmt(totals.safe)} GB`
  : totals.scanned > 0 ? "· all clean ✓" : "· scan first"}
```

Same fix for CategoryPanel's TierButton component.

## Critical files

| File | Change |
|---|---|
| `web/server.py` | `_measure_path` + `scan_category` — permission error detection |
| `web/cleaners.py` | Archives: add caution paths; System: fix tm-snapshots; iCloud: add Notes + app containers + action |
| `apps/web/src/components/PermissionBanner.tsx` | New — FDA detection banner |
| `apps/web/src/components/OverviewPanel.tsx` | Import + render PermissionBanner; fix "scan first" → "all clean ✓" |
| `apps/web/src/components/CategoryPanel.tsx` | Fix TierButton "none" → "clean ✓" text |
| `apps/web/src/lib/types.ts` | Add `permission_denied_count`, `permission_denied_paths` to `CategoryScan` |
| `apps/web/src/state/DashboardContext.tsx` | Expose `hasPermissionErrors` derived from scans |
| `xcode-cleanup.applescript` | kVersion 0.20.2 → 0.20.3 |
| `docs/CHANGELOG.md` | New `[0.20.3]` entry |
| `plans/0008-…md` | This plan |

## Verification

1. `make ui` → scan → PermissionBanner appears listing which paths need FDA
   (if Terminal doesn't have FDA) or does NOT appear (if it does).
2. With FDA granted: `~/Downloads`, Safari, Notes show non-zero GB.
3. Archives shows `~/Downloads` + `~/Desktop` sizes in caution tier.
4. iCloud shows Notes Group Container size + per-app breakdown.
5. System no longer has a 0-forever caution entry.
6. After a full clean + re-scan: Clean ALL safe button shows "· all clean ✓"
   not "· scan first".
