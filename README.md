<p align="center">
  <img src="assets/icon-hero.svg" width="96" height="96" alt="Xcode Cleanup">
</p>

<h1 align="center">Reclaim 10–25 GB Xcode is hoarding. One click.</h1>

<p align="center">
  A free macOS Shortcut that wipes <code>DerivedData</code>, iOS/watchOS/tvOS <code>DeviceSupport</code>, SwiftPM caches, and dead simulators — safely. Skips your Archives so App Store crash symbolication keeps working. No subscription. No telemetry. One short AppleScript you can read in five minutes.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/macOS-14%2B-blue" alt="macOS 14+">
  <img src="https://img.shields.io/badge/Xcode-15%2B-blue" alt="Xcode 15+">
  <img src="https://img.shields.io/badge/built%20with-AppleScript-orange" alt="AppleScript">
  <a href="https://github.com/marvelousempire/xcode-cleanup-shortcut/actions/workflows/check.yml"><img src="https://github.com/marvelousempire/xcode-cleanup-shortcut/actions/workflows/check.yml/badge.svg" alt="CI"></a>
</p>

---

> **The 30-second version.** Xcode's caches (`DerivedData`, `DeviceSupport`, SwiftPM, simulator caches) routinely grow to 20+ GB and stay there. Every iOS dev has Googled which paths are safe to `rm -rf`. This script settles it — wipes the ones that are, skips the ones that aren't, tells you how much it freed.

**See what it'd free, without deleting anything:**

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/marvelousempire/xcode-cleanup-shortcut/main/scripts/remote-cleanup.sh) --dry-run
```

## Why bother

- **Safe by design.** Never touches `~/Library/Developer/Xcode/Archives` (App Store crash symbolication stays intact). Never wipes simulators you actively use — only ones whose runtime was uninstalled.
- **Specific.** Five known-safe Xcode cache locations, plus simulator caches and configurable `/tmp` orphans. Everything else is left alone.
- **Auditable.** [One short AppleScript](./xcode-cleanup.applescript). No binary blobs, no closed-source helper, no opaque CleanMyMac-style "let us decide."
- **Quiet.** Threshold-gated: does nothing when your disk is healthy (>50 GB free). Run it hourly via launchd — it stays silent until you actually need cleanup.
- **Reusable.** Run it from a Shortcut, a hotkey, the menu bar, the terminal (`xcc`), a `launchd` agent, or over SSH on a remote Mac. Pick one, stack them all.

## Install (60 seconds — pick your path)

```sh
git clone https://github.com/marvelousempire/xcode-cleanup-shortcut.git
cd xcode-cleanup-shortcut
make help        # see every option
```

| If you want… | Run this | What you get |
|---|---|---|
| **Apple Shortcut** (menu bar, hotkey, schedulable) | `make install-shortcut` | Pastes the AppleScript into a new Shortcut for you |
| **CLI** (`xcc --dry-run`, `xcc --force`) | `make install-cli` | Symlink at `~/.local/bin/xcc` |
| **Hands-free hourly cleanup** | `make install-launchd` | LaunchAgent runs every hour, silent when disk is healthy |
| **Live disk indicator in your menu bar** | `make install-swiftbar` | SwiftBar plugin — `🧹 12 GB`, click to clean |
| **Remote Mac (build server)** over SSH | [`docs/SHORTCUTS.md`](./docs/SHORTCUTS.md) | Paste-ready Run Script Over SSH block |
| **Web UI in your browser** | `make ui` | Localhost-only Python server + HTML dashboard — live disk indicator, per-path sizes, sparkline history, one-click cleanup |

> [!TIP]
> First time? Run `make dry-run` to see exactly how much you'd reclaim before committing to a delete.

### Web UI (`make ui`)

If you want the most visual way to use it — type `make ui` and your browser opens to a localhost dashboard with:

- **Live disk indicator** — big GB-free number, color-coded (red <20, orange <50, green ≥50), auto-refreshes every 15 seconds.
- **Per-path size breakdown** — bar-chart of every cleanup target (DerivedData, DeviceSupport, simulator caches, …) showing exactly what you'd reclaim.
- **Three one-click actions** — Dry run, Clean now, Force clean. Output streams live in a terminal-style pane (Server-Sent Events).
- **History sparkline** — Unicode-block chart of your real cleanup runs over time, plus total GB freed all-time.

Zero dependencies — pure Python stdlib (`http.server`), zero npm/pip installs. Localhost only (`127.0.0.1`) — never reachable from your network. Ctrl-C in the terminal to stop.

## Install (the Shortcut way)

1. Open **Shortcuts.app** (built into macOS).
2. **File → New Shortcut** (`⌘N`). Name it **"Xcode Cleanup"**.
3. Search the action library for **Run AppleScript**, drag it into the workflow.
4. Replace the placeholder code with the contents of [`xcode-cleanup.applescript`](./xcode-cleanup.applescript).
5. Open the shortcut's info panel (ⓘ) and enable:
   - **Pin in Menu Bar** — adds it to the Shortcuts dropdown.
   - **Use as Quick Action → Services Menu** — adds to Finder right-click.
   - Optional: bind a keyboard shortcut (e.g. `⌃⌥⌘X`).
6. Hit ▶️ to test. macOS will ask for Automation permission on first run — approve.

> **Faster install:** `make install-shortcut` copies the script to your clipboard and opens Shortcuts.app, ready to paste.

> **Want paste-ready blocks for Run Shell Script + Run Script Over SSH?** See [`docs/SHORTCUTS.md`](./docs/SHORTCUTS.md) — covers local Mac, remote Mac via SSH, AppleScript variant, common gotchas, and 3 suggested whole-workflow compositions.

## Use without a Shortcut (Makefile)

If you want to skip the GUI entirely, the script runs standalone via osascript:

```sh
make run            # Run cleanup with the same UX (alert, progress, notification)
make dry-run        # Show what would be freed; delete nothing
make demo           # Simulate phases (for screen recording)
make force          # Run even if disk looks healthy
make size-report    # Print current size of every cleanup target
make check          # Verify AppleScript compiles
make help           # List all targets
```

`make dry-run` is the fastest way to get a "how much could I save right now?" number without committing to a delete.

## Install options (pick one or stack them)

| Path | Best for | Setup |
|---|---|---|
| **Shortcut** (default) | One-button GUI invocation, scheduling, menu bar | `make install-shortcut`, then paste in Shortcuts.app |
| **CLI** (`xcc`) | Terminal users; scripting; piping into other workflows | `make install-cli` — symlinks to `~/.local/bin/xcc` |
| **launchd agent** | Hands-free hourly background cleanup | `make install-launchd` — runs every hour, no-ops when disk is healthy |
| **SwiftBar plugin** | Live free-disk indicator in the menu bar + 1-click cleanup | `brew install --cask swiftbar` → `make install-swiftbar` |

Each path uses the same underlying script. Mix and match — e.g. `install-cli` + `install-swiftbar` gives you terminal access *and* a live disk-pressure indicator.

### `xcc` — CLI

```sh
make install-cli         # symlink to ~/.local/bin/xcc
xcc --help               # see all flags
xcc --dry-run            # measure freeable space
xcc --force              # run even when disk is healthy
xcc --history            # last 20 run-log entries
xcc --report             # sparkline of freed GB over time
xcc --patterns '/tmp/myproj-*'  # override /tmp orphan globs
```

### launchd — hourly background cleanup

```sh
make install-launchd     # runs every hour via ~/Library/LaunchAgents/com.marvelousempire.xcode-cleanup.plist
make uninstall-launchd   # to disable
```

The launchd agent passes `XCODE_CLEANUP_AUTO_CONFIRM=1` so it never blocks on the safety alert, and `XCODE_CLEANUP_NO_UPDATE_CHECK=1` to skip the network call. The 50 GB threshold still gates real deletion — most hourly runs no-op silently.

### SwiftBar — menu-bar indicator

```sh
brew install --cask swiftbar
make install-swiftbar    # symlinks the plugin into ~/Library/Application Support/SwiftBar/Plugins/
```

The menu bar shows `🧹 12GB` (or `🚨` red under 20 GB, `✨` green over 50 GB). Click for dropdown: Run / Dry run / Force / Show history / Report.

### Update check

On every real-mode run, the script makes a single GitHub Releases API call (cached for 24h) and fires a `display notification` if a newer tag exists. Set `XCODE_CLEANUP_NO_UPDATE_CHECK=1` to opt out (the launchd agent does this by default).

### Run history & sparkline report

Every run appends a row to `~/Library/Logs/xcode-cleanup-history.csv`:

```csv
2026-05-08 12:13:57,real,18.3,12.0,30.3
```

```sh
make history             # human-readable last 20 entries
make report              # ▁▂▃▄▅▆▇ sparkline of freed GB
xcc --report             # same, from CLI
```

## Schedule it (optional)

Shortcuts → Automation tab → **Create Personal Automation → Time of Day → 9:00 AM Daily** → Add action **Run Shortcut → Xcode Cleanup** → toggle **Run Immediately**.

The threshold check (>50 GB free) means it stays silent on days you don't need it.

## Invoke it

| How | Action |
|---|---|
| Menu bar | Shortcuts icon → Xcode Cleanup |
| Hotkey | Whatever you bound in setup |
| Spotlight | `⌘Space` → "Xcode Cleanup" → Return |
| Finder | Right-click → Services → Xcode Cleanup |
| Terminal | `shortcuts run "Xcode Cleanup"` (or `make run` for direct osascript) |
| Schedule | Automation → Time of Day |

## Environment flags

The AppleScript reads three optional env vars:

| Variable | Effect |
|---|---|
| `XCODE_CLEANUP_DRY_RUN=1` | Measure phase sizes; no files deleted. |
| `XCODE_CLEANUP_DEMO=1` | Sleep instead of deleting. For screen recording. |
| `XCODE_CLEANUP_FORCE=1` | Skip the 50 GB free threshold check. |
| `XCODE_CLEANUP_AUTO_CONFIRM=1` | Skip the confirmation alert. For scripted recording only — leave off for normal use. |
| `XCODE_CLEANUP_TMP_PATTERNS=...` | Override the `/private/tmp` orphan globs. Empty string skips phase 4 entirely. |
| `XCODE_CLEANUP_NO_UPDATE_CHECK=1` | Skip the once-daily GitHub release check. |

Set them when invoking via `osascript` (the Makefile targets do this for you). They're not visible to the Shortcuts UI itself; the Shortcut always runs in normal mode.

## Customize

### `/tmp` orphan patterns (important for non-maintainer users)

The shipped defaults are example patterns from the maintainer's project (Red-E Play): `redeplay-*`, `RedEPlay-*`, `sweep.mov.sb-*`, `keen-euclid-*`. They will never match anything for other users — phase 4 will safely no-op.

To set patterns matching your own scratch dirs, either:

```sh
# One-off, per invocation:
XCODE_CLEANUP_TMP_PATTERNS="/private/tmp/myproject-* /private/tmp/build-cache-*" make run

# Skip phase 4 entirely:
XCODE_CLEANUP_TMP_PATTERNS="" make run

# Permanent: edit the kDefaultTmpPatterns property at the top of xcode-cleanup.applescript
```

### Add cleanup phases

The script is one self-contained AppleScript. Common additions you can paste in:

- Wipe simulator app/data state too (keeps device definitions): `xcrun simctl erase all`
- Homebrew cleanup: `brew cleanup -s`
- pnpm/npm/yarn caches: `pnpm store prune`, `npm cache clean --force`, `yarn cache clean`

### History log

Every run (real, dry-run, or demo) appends one line to `~/Library/Logs/xcode-cleanup.log`:

```
2026-05-08 12:13:57 | mode: dry-run | freed: 14.2 GB | before: 22.5 GB | after: 22.5 GB
```

`make history` prints the last 20 entries.

## Files

- [`xcode-cleanup.applescript`](./xcode-cleanup.applescript) — the canonical script.
- [`Makefile`](./Makefile) — CLI targets for run/dry-run/demo/install.
- [`PRD.md`](./PRD.md) — product requirements.
- [`HANDOFF.md`](./HANDOFF.md) — current state, what's in flight, next steps.
- [`CHANGELOG.md`](./CHANGELOG.md) — version history.
- [`assets/RECORDING.md`](./assets/RECORDING.md) — how to capture the README GIF.

## Credits

Icon: [Lucide](https://lucide.dev) `wand-sparkles` (ISC). See [`assets/ATTRIBUTION.md`](./assets/ATTRIBUTION.md).

## License

MIT. See [`LICENSE`](./LICENSE).
