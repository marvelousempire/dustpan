# Changelog

## v0.4.4 — 2026-05-08

### Added
- **`docs/Launch-Plan.md`** — full public-launch playbook generated via the `launch-strategy` skill from coreyhaines31/marketingskills, reading from `.agents/product-marketing-context.md` for positioning.
  - Pre-launch checklist + launch-day timeline (T-1d through T+24h)
  - Ready-to-paste copy for: **Show HN** (title + URL + anchor first-comment), **r/iOSProgramming**, **r/swift**, **iOS dev Mastodon** (3-post thread), **X/Twitter** (2-tweet sequence)
  - Engagement playbook (what to do in the first 30min on every channel, what to absolutely not do, tone reminders)
  - **Hit/Steady/Flop** scenario plans with what to do in each — including issue triage, PR review readiness, and how to diagnose a flop before re-launching
  - **7-day follow-up plan** day by day
  - Metrics tracking template
  - Product Hunt deferred to v1.0 (low ROI for a dev utility at launch)
  - Pointers into the next marketing-skill chain (`customer-research`, `page-cro`, `programmatic-seo`, `email-sequence`)

## v0.4.2 — 2026-05-08

### Changed
- **README hero rewritten** using the `copywriting` skill from coreyhaines31/marketingskills. New headline ("Reclaim 10–25 GB Xcode is hoarding. One click.") leads with the specific outcome and uses customer-language ("hoarding"). Subhead names what's wiped + the trust-anchor (skips Archives). "Why bother" section replaces the feature list with five benefits framed against alternatives (manual rm, CleanMyMac, dev guesswork). Install table moved above-the-fold so first-time visitors see the path-to-value in the first screen.

### Why
Before: engineering-voice spec sheet. After: conversion-shaped landing page. Same product, clearer story.

## v0.4.1 — 2026-05-08

### Added
- **`scripts/remote-cleanup.sh`** — pure-shell cleanup that doesn't depend on AppleScript, `osascript`, or a UI session. Safe to run over SSH, in CI, or anywhere headless. Honors `--dry-run` / `--force` flags + `XCODE_CLEANUP_*` env vars; appends a `real-ssh` row to the CSV history when not in dry-run.
- **`docs/SHORTCUTS.md`** — paste-ready blocks for Apple Shortcuts' Run Shell Script and Run Script Over SSH actions, with field-by-field parameter values for macOS 26 / Shortcuts 12.4, four script variants per action (self-updating, repo-pinned, CLI-via-xcc, fully inline), gotchas table, and three suggested whole-Shortcut compositions ("Clean all my Macs", "Babysit the build server", "Pre-flight before TestFlight upload").

### Changed
- README links to `docs/SHORTCUTS.md` from the install section.

## v0.4 — 2026-05-08

Closes all 7 remaining elevations from the post-v0.2 gap-audit.

### Added
- **`bin/xcc` CLI wrapper** — `xcc --dry-run`, `xcc --force`, `xcc --history`, `xcc --report`, `xcc --patterns '...'`. Installable via `make install-cli` (symlinks to `~/.local/bin/xcc`). Covers users who don't want to touch Shortcuts at all. *(Elevation C)*
- **launchd agent** — `launchd/com.marvelousempire.xcode-cleanup.plist` runs the cleanup hourly in the background. Threshold-gated so it no-ops when disk is healthy. Install/uninstall via `make install-launchd` / `make uninstall-launchd`. *(Elevation E)*
- **SwiftBar plugin** — `swiftbar/xcode-cleanup.30m.sh` shows free disk space in the menu bar (`🧹 12GB` / `🚨` red / `✨` green) with click-to-cleanup actions. `make install-swiftbar`. *(Elevation G)*
- **Daily update check** — script fetches the latest release tag from the GitHub Releases API once per day (cached at `~/Library/Caches/xcode-cleanup-version-cache`) and fires a `display notification` if newer. Opt-out: `XCODE_CLEANUP_NO_UPDATE_CHECK=1`. *(Elevation F)*
- **CSV history log** — `~/Library/Logs/xcode-cleanup-history.csv` gets a row per run: `timestamp,mode,freed_gb,before_gb,after_gb`. *(Elevation H)*
- **`scripts/report.py`** + **`make report`** — Unicode-block sparkline of freed-GB across recent real cleanup runs, plus min/max/avg/total stats. *(Elevation H)*
- **`make package-shortcut`** — signs an exported `.shortcut` bundle in Anyone Mode for distribution via `shortcuts sign`. *(Elevation B)*
- **`.github/workflows/release.yml`** — auto-creates a git tag + GitHub Release whenever a commit message on `main` starts with `vX.Y.Z:`. Pulls release notes from the matching CHANGELOG section. *(Elevation A)*
- **Retroactive tags + releases** for v0.1, v0.2, v0.2.1.

### Changed
- Makefile grows 7 new targets: `install-cli`, `uninstall-cli`, `install-launchd`, `uninstall-launchd`, `install-swiftbar`, `uninstall-swiftbar`, `package-shortcut`, `report`. `make help` displays them all.
- README gains an "Install options" matrix + sections per install path. PRD lists F20–F27 with ✅ status.

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
