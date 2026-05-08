# Real-Time Handoff Sheet

> The single source of truth for "what's the state of this repo right now?"
> Edit this in place. Don't append a new section per handoff — overwrite stale lines.

**Last updated:** 2026-05-08
**Updated by:** v0.3 ship

---

## TL;DR

Repo is at v0.3, all 7 gaps from the post-v0.2 audit are closed. Shipped today: CI workflow on macOS runners, env-var override for `/tmp` orphan patterns (so the repo is useful to non-maintainer users), per-run history log + `make history`, retroactive version tags on v0.1/v0.2/v0.2.1/v0.3 with matching GitHub Releases, README hero with Lucide icon + 5 shields.io badges. Issue #2 (progress-bar GIF) remains open as a manual-only follow-up.

## Current status

- ✅ v0.1, v0.2, v0.2.1, v0.3 tagged + released on GitHub
- ✅ CI green on `main` (`.github/workflows/check.yml` — `make check` on macOS-latest)
- ✅ `/tmp` patterns customizable via `XCODE_CLEANUP_TMP_PATTERNS` env var
- ✅ History log at `~/Library/Logs/xcode-cleanup.log` populated on every run
- 🟡 Issue #2 — progress-bar GIF still uncaptured. v0.2.1 made auto-recording feasible; v0.3 didn't move it forward. Owner-driven follow-up.

## In flight right now

Nothing.

## Recent decisions

| Date | Decision | Why |
|---|---|---|
| 2026-05-08 | Build as a Shortcut + Run AppleScript, not a Mac app | Lower friction, no signing, native progress + notifications, schedulable. |
| 2026-05-08 | 50 GB threshold, hardcoded | Reasonable absolute floor for an active dev machine. |
| 2026-05-08 | Skip `Archives/` and active simulator devices | Preserves crash symbolication and installed simulator state. |
| 2026-05-08 | `xcrun simctl delete unavailable`, not `erase all` | Removes only simulators whose runtime is uninstalled. |
| 2026-05-08 | v0.2 flags via env vars (system attribute), not Shortcut variables | Keeps the Shortcut path one-paste; flags are for power users invoking via Makefile. |
| 2026-05-08 | Dry-run uses `du -sk` per phase, not df-delta | Df-delta would be 0 in dry-run; per-phase measurement gives the answer the user wants. |
| 2026-05-08 | `XCODE_CLEANUP_AUTO_CONFIRM` separate flag from DEMO | Recording automation needs to skip the alert; real demo users still see the safety prompt. |
| 2026-05-08 | `/tmp` patterns kept Red-E Play–defaults but env-var overridable | Maintainer's machine still works out of the box; forks/clones can override without editing source. |
| 2026-05-08 | History log local-only at `~/Library/Logs/xcode-cleanup.log`, no upload | Privacy. Pure reflection tool, never phones home. |
| 2026-05-08 | Lucide `wand-sparkles` icon over Apple/Xcode artwork | Apple icons are trademarked; Lucide is ISC. |
| 2026-05-08 | CI on macOS-latest, single `make check` step | `osacompile` is macOS-only; AppleScript syntax is the only thing meaningful to validate. |

## Blockers

None.

## Open questions (mirrored from PRD)

1. **Threshold: absolute GB or percentage?** — currently 50 GB hardcoded.
2. **Ship a prebuilt `.shortcut` bundle?** — saves install friction but bundles are tied to creator's iCloud signature. Mitigated for now via `make install-shortcut` (clipboard paste).

## Next steps (in priority order)

1. **Capture progress-bar GIF** (issue #2) via `make record-demo` on a sanitized desktop. AUTO_CONFIRM + per-phase notifications make this an interactive ~5-minute task.
2. **(v0.4)** `launchd` agent that triggers cleanup automatically when free space drops below threshold (elevation E from prior audit).
3. **(v0.4)** `make report` target rendering an ASCII sparkline of freed-GB over time from the history log (elevation H).
4. **(v0.4)** SwiftBar sibling repo for live menu-bar disk indicator (elevation G).
5. **(v0.4)** `.shortcut` bundle packaging via `shortcuts sign --mode anyone`, attached to GitHub Releases (elevation B).

## Key files

| File | What it is |
|---|---|
| `xcode-cleanup.applescript` | The canonical script. The whole product is this one file. |
| `Makefile` | CLI targets: run/dry-run/demo/force/install-shortcut/uninstall-shortcut/shortcut-run/record-demo/check/size-report/history/help. |
| `.github/workflows/check.yml` | CI — `make check` on every push/PR. |
| `assets/icon-hero.svg` | Lucide wand-sparkles, 96×96, Apple-blue (#0A84FF). README hero. |
| `assets/icon.svg` | Original 24×24 currentColor variant. |
| `assets/ATTRIBUTION.md` | Lucide ISC attribution. |
| `assets/RECORDING.md` | How to capture the README progress-bar GIF (issue #2). |
| `README.md` | User-facing install + usage. Has hero + 5 badges. |
| `PRD.md` | Why this exists, what's in / out of scope, F-requirements with ✅/⬜ status. |
| `CHANGELOG.md` | v0.1 → v0.3 history. |
| `HANDOFF.md` | This file. Overwrite, don't append. |
| `LICENSE` | MIT. |

## Contact / context

- Maintainer: [@marvelousempire](https://github.com/marvelousempire)
- Origin: extracted from a Red-E Play dev workflow where DerivedData regularly hit 19 GB and `/private/tmp` accumulated multi-GB sandbox orphans from `xcodebuild`-driven scratch sessions.
