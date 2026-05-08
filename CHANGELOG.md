# Changelog

## v0.3 — 2026-05-08

### Added
- **`XCODE_CLEANUP_TMP_PATTERNS=...`** — override the default `/tmp` orphan globs. Empty string skips phase 4 entirely. Repo is now useful to non-maintainer users without editing source.
- **History log** at `~/Library/Logs/xcode-cleanup.log` — every run (real, dry-run, or demo) appends one line: `timestamp | mode | freed GB | before GB | after GB`.
- **`make history`** Makefile target — prints the last 20 log entries.
- **CI workflow** `.github/workflows/check.yml` — runs `make check` on every push and PR (macos-latest runner). README has the badge.
- **README hero** — centered Lucide `wand-sparkles` icon (Apple blue), title, tagline, 5 shields.io badges (MIT, macOS 14+, Xcode 15+, AppleScript, CI status).
- **`assets/icon.svg` + `assets/icon-hero.svg` + `assets/ATTRIBUTION.md`** — ISC-licensed icon assets and Lucide attribution.

### Changed
- README "Customize" section explicitly flags the Red-E Play `/tmp` patterns as example-only and documents the env-var override.
- Retroactive git tags + GitHub Releases for v0.1, v0.2, v0.2.1.

## v0.2.1 — 2026-05-08

### Added
- **`XCODE_CLEANUP_AUTO_CONFIRM=1`** — skips the confirmation alert. Intended for scripted screen-recording (so the alert doesn't block the capture timeline). Real users should leave this off — the alert is the safety gate before destructive deletion.
- **Demo mode now fires per-phase `display notification` banners** so the recording catches a visible 4-step sequence instead of silent sleeps.

## v0.2 — 2026-05-08

### Added
- **Dry-run mode** — `XCODE_CLEANUP_DRY_RUN=1` measures what would be freed without deleting anything. Reports `Would free ~X.X GB` via notification.
- **Demo mode** — `XCODE_CLEANUP_DEMO=1` simulates phases with sleeps instead of deleting. Used for capturing the README progress-bar GIF.
- **Force mode** — `XCODE_CLEANUP_FORCE=1` skips the 50 GB free threshold check, useful for testing or running on demand even when the disk looks healthy.
- **Per-phase size measurement** — each phase uses `du -sk` before deletion, so dry-run can report total bytes touched.
- **Makefile** — `make help` lists targets: `run`, `dry-run`, `demo`, `force`, `install-shortcut`, `uninstall-shortcut`, `shortcut-run`, `record-demo`, `check`, `size-report`.
- **`assets/RECORDING.md`** — instructions for capturing the progress-bar GIF.

### Changed
- Script title in the progress bar updates to `(Dry Run)` or `(Demo)` based on the active flag.
- README documents the Makefile and the new flags.

## v0.1 — 2026-05-08

Initial release. One-button macOS Shortcut that reclaims Xcode disk space (DerivedData, DeviceSupport, SwiftPM caches, unavailable simulators, /tmp orphans) with a native progress bar, threshold-gated confirmation, and final notification.
