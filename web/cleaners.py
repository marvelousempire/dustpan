"""All cleanup categories, paths, and actions for the web UI dashboard.

Structure:
    CATEGORIES = {
        "<category-id>": {
            "label":  "Display name",
            "icon":   "emoji or SVG ref",
            "groups": { "safe": [...], "probably_safe": [...], "caution": [...] },
            "actions": {
                "<action-id>": {
                    "label": str, "desc": str, "cost": str,
                    "shell": str OR "cmd": [str], "sudo": bool,
                },
                ...
            },
        },
        ...
    }

Path entries are tuples: (display_label, expand-to-path).

Cost annotations are written for users — "what you lose when you click this."
"""

CATEGORIES = {

    # ─── Xcode ─────────────────────────────────────────────────────────
    "xcode": {
        "label": "Xcode",
        "icon":  "🛠",
        "tagline": "Reclaim 10–25 GB Xcode is hoarding.",
        "groups": {
            "safe": [
                ("DerivedData",              "~/Library/Developer/Xcode/DerivedData"),
                ("iOS DeviceSupport",        "~/Library/Developer/Xcode/iOS DeviceSupport"),
                ("watchOS DeviceSupport",    "~/Library/Developer/Xcode/watchOS DeviceSupport"),
                ("tvOS DeviceSupport",       "~/Library/Developer/Xcode/tvOS DeviceSupport"),
                ("visionOS DeviceSupport",   "~/Library/Developer/Xcode/visionOS DeviceSupport"),
                ("Xcode caches",             "~/Library/Caches/com.apple.dt.Xcode"),
                ("SwiftPM cache",            "~/Library/Caches/org.swift.swiftpm"),
                ("Simulator caches",         "~/Library/Developer/CoreSimulator/Caches"),
                ("CoreSimulator Cryptex",    "~/Library/Developer/CoreSimulator/Cryptex"),
                ("iOS Device Logs",          "~/Library/Developer/Xcode/iOS Device Logs"),
                ("Xcode Snapshots",          "~/Library/Developer/Xcode/Snapshots"),
                ("Interface Builder caches", "~/Library/Developer/Xcode/UserData/IB Support"),
                ("Xcode Products",           "~/Library/Developer/Xcode/Products"),
            ],
            "probably_safe": [
                ("Simulator app data (all devices)",  "~/Library/Developer/CoreSimulator/Devices"),
                ("Instruments traces",                "~/Library/Application Support/Instruments"),
                ("CocoaPods cache",                   "~/Library/Caches/CocoaPods"),
                ("CocoaPods specs",                   "~/.cocoapods/repos"),
            ],
            "caution": [
                ("iOS device backups (Finder/iTunes)",            "~/Library/Application Support/MobileSync/Backup"),
                ("Xcode Archives (NEEDED for symbolication)",     "~/Library/Developer/Xcode/Archives"),
                ("Provisioning Profiles",                          "~/Library/MobileDevice/Provisioning Profiles"),
            ],
        },
        "actions": {
            "clean-safe": {
                "label": "Clean all safe Xcode caches",
                "desc":  "Wipes DerivedData + DeviceSupport + SwiftPM cache + simulator caches + Xcode extras.",
                "cost":  "First build after cleanup takes ~30s longer (caches regenerate). Device debug symbols re-download when a device reconnects. Nothing project-affecting.",
                "shell": "rm -rf ~/Library/Developer/Xcode/DerivedData/* "
                         "~/Library/Developer/Xcode/iOS\\ DeviceSupport/* "
                         "~/Library/Developer/Xcode/watchOS\\ DeviceSupport/* "
                         "~/Library/Developer/Xcode/tvOS\\ DeviceSupport/* "
                         "~/Library/Developer/Xcode/visionOS\\ DeviceSupport/* "
                         "~/Library/Caches/com.apple.dt.Xcode/* "
                         "~/Library/Caches/org.swift.swiftpm/* "
                         "~/Library/Developer/CoreSimulator/Caches/* "
                         "~/Library/Developer/Xcode/Snapshots/* "
                         "~/Library/Developer/Xcode/UserData/IB\\ Support/* "
                         "~/Library/Developer/Xcode/iOS\\ Device\\ Logs/* "
                         "~/Library/Developer/Xcode/Products/* 2>/dev/null; "
                         "xcrun simctl delete unavailable 2>/dev/null; true",
            },
            "erase-simulators": {
                "label": "Erase all simulator app data",
                "desc":  "Runs `xcrun simctl erase all` — keeps simulator devices, wipes installed apps + their data.",
                "cost":  "Simulator apps you've installed for testing are gone (re-installable from your projects). Saved app state in simulators is lost. Simulator device definitions and runtimes stay.",
                "cmd":   ["xcrun", "simctl", "erase", "all"],
            },
            "clear-instruments": {
                "label": "Clear Instruments traces",
                "desc":  "Removes all saved .trace files.",
                "cost":  "Past Instruments profiling sessions are gone. Future profiling unaffected.",
                "shell": "rm -rf ~/Library/Application\\ Support/Instruments/* 2>/dev/null; true",
            },
            "clear-cocoapods": {
                "label": "Clear CocoaPods caches",
                "desc":  "Removes ~/Library/Caches/CocoaPods + ~/.cocoapods/repos.",
                "cost":  "Next `pod install` re-fetches pod specs (slower over flaky internet, otherwise minimal).",
                "shell": "rm -rf ~/Library/Caches/CocoaPods/* ~/.cocoapods/repos/* 2>/dev/null; true",
            },
        },
    },

    # ─── LLM tools (sub-tabs) ──────────────────────────────────────────
    "llms-claude": {
        "label": "Claude",
        "parent": "llms",
        "icon":   "🤖",
        "tagline": "Claude Code + Claude Desktop caches.",
        "groups": {
            "safe": [
                ("Claude Desktop updater cache",      "~/Library/Caches/com.anthropic.claudefordesktop.ShipIt"),
                ("Claude Desktop cache",              "~/Library/Caches/com.anthropic.claudefordesktop"),
                ("Claude Desktop logs",               "~/Library/Logs/Claude"),
                ("Claude Code plugin cache",          "~/.claude/plugins/cache"),
            ],
            "probably_safe": [
                ("Claude Code session transcripts",   "~/.claude/projects"),
                ("Claude Desktop app state",          "~/Library/Application Support/Claude"),
            ],
            "caution": [
                ("Claude Code config + settings",     "~/.claude/settings.json"),
                ("Claude Code installed skills",      "~/.claude/skills"),
            ],
        },
        "actions": {
            "clear-shipit": {
                "label": "Clear Claude Desktop updater cache",
                "desc":  "Removes ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt (often 500MB+).",
                "cost":  "Next Claude Desktop update re-downloads (typical ~200MB). Nothing else affected.",
                "shell": "rm -rf ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt/* 2>/dev/null; true",
            },
            "clear-claude-cache": {
                "label": "Clear all Claude caches + logs",
                "desc":  "Removes Claude Desktop cache, ShipIt cache, logs, and Claude Code plugin cache.",
                "cost":  "Logs gone (rarely useful). Plugins re-cache on next use. Updater re-downloads next update.",
                "shell": "rm -rf ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt/* "
                         "~/Library/Caches/com.anthropic.claudefordesktop/* "
                         "~/Library/Logs/Claude/* "
                         "~/.claude/plugins/cache/* 2>/dev/null; true",
            },
            "clear-claude-sessions": {
                "label": "Clear Claude Code session transcripts",
                "desc":  "Removes ~/.claude/projects (per-project session histories).",
                "cost":  "You lose conversation history with Claude Code. Settings, skills, and plugins are preserved.",
                "shell": "rm -rf ~/.claude/projects/* 2>/dev/null; true",
            },
            "reset-claude-desktop": {
                "label": "Reset Claude Desktop (sign out + clear local cache)",
                "desc":  "Removes ~/Library/Application Support/Claude — Claude Desktop's local app state, can be 5–15 GB.",
                "cost":  "Hard reset: you sign out of Claude Desktop and re-sign-in (cloud conversation history re-syncs). Local-only drafts, unsaved project files, and any MCP-server state stored there are LOST. Only run this if you're OK with that trade.",
                "shell": "rm -rf ~/Library/Application\ Support/Claude/* 2>/dev/null; true",
            },
        },
    },

    "llms-cursor": {
        "label": "Cursor",
        "parent": "llms",
        "icon":   "✏️",
        "tagline": "Cursor IDE caches.",
        "groups": {
            "safe": [
                ("Cursor Code Cache",              "~/Library/Application Support/Cursor/Code Cache"),
                ("Cursor GPU Cache",               "~/Library/Application Support/Cursor/GPUCache"),
                ("Cursor CachedData",              "~/Library/Application Support/Cursor/CachedData"),
                ("Cursor CachedExtensions",        "~/Library/Application Support/Cursor/CachedExtensions"),
                ("Cursor CachedExtensionVSIXs",    "~/Library/Application Support/Cursor/CachedExtensionVSIXs"),
                ("Cursor Cache",                   "~/Library/Application Support/Cursor/Cache"),
                ("Cursor logs",                    "~/Library/Application Support/Cursor/logs"),
                ("Cursor crash reports",           "~/Library/Application Support/Cursor/Crashpad"),
            ],
            "probably_safe": [
                ("Cursor remote (cursor-server)",  "~/.cursor-server"),
                ("Cursor workspace state",         "~/Library/Application Support/Cursor/User/workspaceStorage"),
            ],
            "caution": [
                ("Cursor user settings",           "~/Library/Application Support/Cursor/User/settings.json"),
                ("Cursor keybindings",             "~/Library/Application Support/Cursor/User/keybindings.json"),
                ("Cursor snippets",                "~/Library/Application Support/Cursor/User/snippets"),
            ],
        },
        "actions": {
            "clear-cursor-caches": {
                "label": "Clear Cursor caches",
                "desc":  "Removes Cursor's Code Cache, GPUCache, CachedData, CachedExtensions, and logs.",
                "cost":  "Cursor takes ~10s longer on next launch (caches rebuild). Extensions stay installed; their cached metadata is rebuilt. No code/settings/projects affected.",
                "shell": "rm -rf ~/Library/Application\\ Support/Cursor/Code\\ Cache/* "
                         "~/Library/Application\\ Support/Cursor/GPUCache/* "
                         "~/Library/Application\\ Support/Cursor/CachedData/* "
                         "~/Library/Application\\ Support/Cursor/CachedExtensions/* "
                         "~/Library/Application\\ Support/Cursor/CachedExtensionVSIXs/* "
                         "~/Library/Application\\ Support/Cursor/Cache/* "
                         "~/Library/Application\\ Support/Cursor/logs/* 2>/dev/null; true",
            },
            "clear-cursor-workspace-state": {
                "label": "Clear workspace state",
                "desc":  "Removes per-workspace history (open files, search history, undo stack, etc.).",
                "cost":  "Workspace state (open tabs, recent files, search history) resets to fresh on next open. Your files and settings are untouched.",
                "shell": "rm -rf ~/Library/Application\\ Support/Cursor/User/workspaceStorage/* 2>/dev/null; true",
            },
        },
    },

    "llms-chatgpt": {
        "label": "ChatGPT",
        "parent": "llms",
        "icon":   "💬",
        "tagline": "ChatGPT desktop app caches.",
        "groups": {
            "safe": [
                ("ChatGPT cache",        "~/Library/Caches/com.openai.chat"),
                ("ChatGPT logs",         "~/Library/Logs/com.openai.chat"),
            ],
            "probably_safe": [
                ("ChatGPT app state",    "~/Library/Application Support/com.openai.chat"),
            ],
            "caution": [],
        },
        "actions": {
            "clear-chatgpt-cache": {
                "label": "Clear ChatGPT caches + logs",
                "desc":  "Removes the desktop app's cache and logs.",
                "cost":  "ChatGPT desktop loads slightly slower on next launch (re-caches assets). You stay signed in. Conversation history is preserved (lives in OpenAI's cloud, not local).",
                "shell": "rm -rf ~/Library/Caches/com.openai.chat/* ~/Library/Logs/com.openai.chat/* 2>/dev/null; true",
            },
        },
    },

    # ─── Docker ────────────────────────────────────────────────────────
    "docker": {
        "label": "Docker",
        "icon":  "🐳",
        "tagline": "Reclaim 5–60 GB. Docker.raw is the usual culprit.",
        "groups": {
            "safe": [
                ("Docker Desktop logs",                "~/Library/Containers/com.docker.docker/Data/log"),
                ("Docker buildx build cache",          "~/.docker/buildx"),
                ("Docker CLI plugins cache",           "~/.docker/cli-plugins-cache"),
                ("Docker Desktop diagnostics",         "~/Library/Group Containers/group.com.docker/diagnostics"),
                ("Docker Desktop telemetry queue",     "~/Library/Group Containers/group.com.docker/telemetry"),
            ],
            "probably_safe": [
                # Images / containers / volumes live INSIDE Docker.raw — not measurable
                # by `du` on the host. Reclaim them via the prune actions below.
            ],
            "caution": [
                ("Docker VM disk (Docker.raw — new location)",      "~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"),
                ("Docker VM disk (Docker.raw — legacy location)",   "~/Library/Containers/com.docker.docker/Data/vms/0/Docker.raw"),
                ("Docker Desktop group container state",            "~/Library/Group Containers/group.com.docker"),
            ],
        },
        "actions": {
            "docker-prune-safe": {
                "label": "Prune Docker — safe (stopped containers + dangling images + buildx)",
                "desc":  "Runs `docker container prune`, `image prune` (dangling only), `network prune`, and `buildx prune -af`. Skips volumes.",
                "cost":  "Stopped containers gone (start them again to recreate). Untagged/dangling images gone (re-pull on demand). Unused networks gone (`docker compose up` recreates). Build cache wiped — next build runs from scratch once. Volumes are NOT touched, so any DB data is safe.",
                "shell": "if command -v docker >/dev/null 2>&1; then "
                         "echo '▶ container prune'; docker container prune -f 2>&1; "
                         "echo '▶ image prune (dangling)'; docker image prune -f 2>&1; "
                         "echo '▶ network prune'; docker network prune -f 2>&1; "
                         "echo '▶ buildx prune'; docker buildx prune -af 2>&1; "
                         "echo '▶ disk usage now:'; docker system df 2>&1; "
                         "else echo 'Docker CLI not found — install Docker Desktop or skip.'; fi",
            },
            "docker-prune-everything": {
                "label": "Nuke ALL unused Docker (system prune --volumes)",
                "desc":  "Aggressive: `docker system prune -a --volumes -f`. Removes everything not currently in use, including volumes.",
                "cost":  "ALL stopped containers gone. ALL unused images gone (re-pull on next `docker compose up`, often 5+ GB). **ALL unused volumes gone** — this is the dangerous one: any DB/postgres/redis volume not attached to a RUNNING container is wiped. Confirm your important containers are running before clicking.",
                "shell": "if command -v docker >/dev/null 2>&1; then "
                         "docker system prune -a --volumes -f 2>&1; "
                         "echo ''; echo '▶ disk usage now:'; docker system df 2>&1; "
                         "else echo 'Docker CLI not found.'; fi",
            },
            "docker-vm-reset-info": {
                "label": "How to actually shrink Docker.raw (informational)",
                "desc":  "Pruning shrinks what's INSIDE the VM, not the .raw file on host disk. This shows how to reset the VM image.",
                "cost":  "Resetting Docker Desktop's VM wipes ALL images, containers, volumes, and Kubernetes state. Surfaces the manual command rather than running it for you.",
                "shell": "echo 'Docker.raw is the VM disk that holds your images/containers/volumes.'; "
                         "echo 'Pruning shrinks WHAT IS INSIDE the VM, not the .raw file on host disk.'; "
                         "echo ''; echo 'Current Docker.raw size:'; "
                         "ls -lh ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw 2>/dev/null || "
                         "ls -lh ~/Library/Containers/com.docker.docker/Data/vms/0/Docker.raw 2>/dev/null || "
                         "echo '  (Docker.raw not found — Docker Desktop may not be installed.)'; "
                         "echo ''; echo 'To shrink it (in Docker Desktop):'; "
                         "echo '  Settings → Troubleshoot → Clean / Purge data → Reset disk image'; "
                         "echo ''; echo 'Or from Terminal (nukes everything, then rebuilds the VM):'; "
                         "echo '  docker system prune -a --volumes -f'; "
                         "echo '  killall Docker'; "
                         "echo '  rm -f ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw'; "
                         "echo '  open -a Docker'",
                "informational": True,
            },
            "docker-clear-logs": {
                "label": "Clear Docker Desktop logs + diagnostics",
                "desc":  "Removes ~/Library/Containers/com.docker.docker/Data/log + Group Containers diagnostics.",
                "cost":  "Past Docker Desktop logs + diagnostics gone. Containers, images, and volumes are untouched.",
                "shell": "rm -rf ~/Library/Containers/com.docker.docker/Data/log/* "
                         "~/Library/Group\\ Containers/group.com.docker/diagnostics/* "
                         "~/Library/Group\\ Containers/group.com.docker/telemetry/* 2>/dev/null; true",
            },
        },
    },

    # ─── Adobe (Creative sub-tab) ──────────────────────────────────────
    "creative-adobe": {
        "label": "Adobe",
        "parent": "creative",
        "icon":   "🎨",
        "tagline": "Premiere · After Effects · Photoshop · Lightroom caches.",
        "groups": {
            "safe": [
                ("Adobe Media Cache (Premiere/AE shared)",       "~/Library/Application Support/Adobe/Common/Media Cache Files"),
                ("Adobe Media Cache index",                       "~/Library/Application Support/Adobe/Common/Media Cache"),
                ("Premiere Pro disk cache",                       "~/Library/Application Support/Adobe/Premiere Pro"),
                ("After Effects disk cache",                      "~/Library/Application Support/Adobe/After Effects"),
                ("Photoshop disk cache",                          "~/Library/Application Support/Adobe/Adobe Photoshop"),
                ("Adobe general cache",                           "~/Library/Caches/Adobe"),
                ("Adobe Creative Cloud cache",                    "~/Library/Caches/com.adobe.acc.AdobeCreativeCloud"),
                ("Adobe Acrobat cache",                           "~/Library/Caches/com.adobe.Acrobat.Pro"),
            ],
            "probably_safe": [
                ("Camera Raw cache",                              "~/Library/Caches/Adobe Camera Raw"),
                ("Adobe Bridge cache",                            "~/Library/Caches/Adobe/Bridge"),
            ],
            "caution": [
                ("Lightroom folder (CATALOG + previews together)",  "~/Pictures/Lightroom"),
            ],
        },
        "actions": {
            "clear-adobe-media-cache": {
                "label": "Clear Adobe Media Cache (Premiere + AE shared)",
                "desc":  "Removes the shared Media Cache Files + index that Premiere Pro and After Effects both use. Often the single biggest reclaim on a video editor's Mac.",
                "cost":  "Premiere / After Effects re-conform audio and rebuild peaks the next time you open each project (one-time cost per project, can take minutes on long timelines). Project files, sequences, edits — all untouched.",
                "shell": "rm -rf "
                         "~/Library/Application\\ Support/Adobe/Common/Media\\ Cache\\ Files/* "
                         "~/Library/Application\\ Support/Adobe/Common/Media\\ Cache/* 2>/dev/null; true",
            },
            "clear-adobe-app-caches": {
                "label": "Clear Adobe app caches (Premiere / AE / Photoshop)",
                "desc":  "Per-app disk caches for Premiere Pro, After Effects, Photoshop. Doesn't touch the shared Media Cache (that has its own action).",
                "cost":  "Each app rebuilds its disk cache on next launch / next preview render. Preference settings, presets, and project files are NOT affected.",
                "shell": "rm -rf "
                         "~/Library/Application\\ Support/Adobe/Premiere\\ Pro/*/Common/Media\\ Cache* "
                         "~/Library/Application\\ Support/Adobe/After\\ Effects/*/Adobe\\ After\\ Effects\\ Disk\\ Cache* "
                         "~/Library/Application\\ Support/Adobe/Adobe\\ Photoshop\\ */Cache* "
                         "~/Library/Caches/Adobe/Bridge/* "
                         "~/Library/Caches/Adobe/* 2>/dev/null; true",
            },
            "clear-camera-raw-cache": {
                "label": "Clear Camera Raw cache",
                "desc":  "Removes Camera Raw's previews + ACR cache (~/Library/Caches/Adobe Camera Raw).",
                "cost":  "Lightroom / Photoshop rebuilds raw previews on next view (slower per-image first-time). Edits are stored in catalogs / sidecar XMP files and are unaffected.",
                "shell": "rm -rf ~/Library/Caches/Adobe\\ Camera\\ Raw/* 2>/dev/null; true",
            },
            "lightroom-preview-info": {
                "label": "How to clear Lightroom previews (without touching your catalog)",
                "desc":  "Lightroom previews live next to the catalog inside `~/Pictures/Lightroom`. We deliberately don't auto-delete in that folder — your `.lrcat` catalog is irreplaceable.",
                "cost":  "Informational. Shows the size of your Lightroom folder and the in-app step to clear previews safely.",
                "shell": "echo 'Lightroom catalog + previews live in:'; "
                         "du -sh ~/Pictures/Lightroom/* 2>/dev/null || echo '  (no ~/Pictures/Lightroom found)'; "
                         "echo ''; echo 'To clear 1:1 previews safely (won\\'t touch your catalog):'; "
                         "echo '  Lightroom Classic → Library menu → Previews → Discard 1:1 Previews'; "
                         "echo '  They rebuild on demand as you view photos.'; "
                         "echo ''; echo 'Never delete the .lrcat file from this UI — that is your catalog.'",
                "informational": True,
            },
        },
    },

    # ─── DaVinci Resolve (Creative sub-tab) ────────────────────────────
    "creative-davinci": {
        "label": "DaVinci Resolve",
        "parent": "creative",
        "icon":   "🎬",
        "tagline": "Render cache, proxies, optimized media.",
        "groups": {
            "safe": [
                ("Render Cache",                          "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Render Cache"),
                ("Optimized Media",                       "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Optimized Media"),
                ("CacheClip (proxies)",                   "~/Movies/CacheClip"),
                ("DaVinci Resolve logs",                  "~/Library/Logs/Blackmagic Design/DaVinci Resolve"),
                ("DaVinci general cache",                 "~/Library/Caches/com.blackmagic-design.DaVinciResolve"),
            ],
            "probably_safe": [
                ("Gallery Stills (per-project color refs)",   "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Gallery Stills"),
                ("Fusion Disk Cache",                          "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Disk Cache"),
            ],
            "caution": [
                ("Resolve Projects",                           "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Resolve Projects"),
                ("Resolve Disk Database",                      "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Resolve Disk Database"),
                ("~/Movies/DaVinci Resolve (may contain exports)",  "~/Movies/DaVinci Resolve"),
            ],
        },
        "actions": {
            "clear-davinci-cache": {
                "label": "Clear Render Cache + Optimized Media + CacheClip",
                "desc":  "Removes the three big regenerable buckets: Render Cache, Optimized Media, and CacheClip (proxies).",
                "cost":  "Resolve re-renders cached / optimized clips on next playback (slower scrubbing until the cache rebuilds — usually within a session). Anything you've EXPORTED is untouched; projects and color grades are untouched.",
                "shell": "rm -rf "
                         "~/Library/Application\\ Support/Blackmagic\\ Design/DaVinci\\ Resolve/Render\\ Cache/* "
                         "~/Library/Application\\ Support/Blackmagic\\ Design/DaVinci\\ Resolve/Optimized\\ Media/* "
                         "~/Movies/CacheClip/* 2>/dev/null; true",
            },
            "clear-davinci-logs": {
                "label": "Clear DaVinci logs + general cache",
                "desc":  "Removes ~/Library/Logs/Blackmagic Design + ~/Library/Caches/com.blackmagic-design.*",
                "cost":  "Past crash logs gone. Projects, render cache, and color databases untouched.",
                "shell": "rm -rf ~/Library/Logs/Blackmagic\\ Design/* "
                         "~/Library/Caches/com.blackmagic-design.*/* 2>/dev/null; true",
            },
            "clear-fusion-cache": {
                "label": "Clear Fusion disk cache",
                "desc":  "Removes Fusion's disk cache (used for VFX node previews).",
                "cost":  "Fusion comp nodes recompute on next preview (slower the first time per comp). Final flows / saved comps are stored in projects and unaffected.",
                "shell": "rm -rf ~/Library/Application\\ Support/Blackmagic\\ Design/DaVinci\\ Resolve/Fusion/Disk\\ Cache/* 2>/dev/null; true",
            },
        },
    },

    # ─── Apps (browsers, communicators, downloads) ────────────────────
    "apps": {
        "label": "Apps",
        "icon":  "🧹",
        "tagline": "Browser caches, chat-app caches, old installers.",
        "groups": {
            "safe": [
                ("Chrome cache",                          "~/Library/Caches/Google/Chrome"),
                ("Safari cache",                          "~/Library/Caches/com.apple.Safari"),
                ("Firefox cache",                         "~/Library/Caches/Firefox"),
                ("Brave cache",                           "~/Library/Caches/BraveSoftware"),
                ("Arc cache",                             "~/Library/Caches/Arc"),
                ("Slack service-worker cache",            "~/Library/Application Support/Slack/Service Worker"),
                ("Discord cache",                         "~/Library/Application Support/discord/Cache"),
                ("Spotify cache",                         "~/Library/Caches/com.spotify.client"),
                ("Zoom cache",                            "~/Library/Caches/us.zoom.xos"),
                ("Microsoft Teams cache",                 "~/Library/Caches/com.microsoft.teams"),
                ("Homebrew downloads",                    "~/Library/Caches/Homebrew/downloads"),
            ],
            "probably_safe": [
                ("~/Downloads/*.dmg installer images",    "~/Downloads"),
                ("Trash",                                 "~/.Trash"),
                ("All ~/Library/Caches/*",                "~/Library/Caches"),
            ],
            "caution": [
                ("Mail downloads",                        "~/Library/Containers/com.apple.mail/Data/Library/Mail Downloads"),
            ],
        },
        "actions": {
            "clear-browser-caches": {
                "label": "Clear browser caches",
                "desc":  "Clears Chrome, Safari, Firefox, Brave, Arc caches.",
                "cost":  "Each browser reloads pages from origin on next visit (slightly slower first-load per site). Bookmarks, history, passwords, cookies are NOT affected.",
                "shell": "rm -rf ~/Library/Caches/Google/Chrome/*/Cache/* "
                         "~/Library/Caches/Google/Chrome/*/Code\\ Cache/* "
                         "~/Library/Caches/com.apple.Safari/* "
                         "~/Library/Caches/Firefox/* "
                         "~/Library/Caches/BraveSoftware/*/Cache/* "
                         "~/Library/Caches/Arc/* 2>/dev/null; true",
            },
            "clear-chat-caches": {
                "label": "Clear chat-app caches",
                "desc":  "Clears Slack, Discord, Zoom, Teams caches.",
                "cost":  "Slack/Discord re-download recent message media on next launch. You stay signed in. No conversation history lost.",
                "shell": "rm -rf ~/Library/Application\\ Support/Slack/Service\\ Worker/* "
                         "~/Library/Application\\ Support/discord/Cache/* "
                         "~/Library/Caches/com.spotify.client/* "
                         "~/Library/Caches/us.zoom.xos/* "
                         "~/Library/Caches/com.microsoft.teams/* 2>/dev/null; true",
            },
            "clear-old-installers": {
                "label": "Clear *.dmg installers in ~/Downloads",
                "desc":  "Removes ~/Downloads/*.dmg and *.pkg files (often 100MB–5GB each).",
                "cost":  "You'll need to re-download installers from the apps' websites if you want to reinstall. Apps already installed stay installed.",
                "shell": "rm -f ~/Downloads/*.dmg ~/Downloads/*.pkg 2>/dev/null; true",
            },
            "empty-trash": {
                "label": "Empty Trash",
                "desc":  "Permanently removes everything in ~/.Trash.",
                "cost":  "Files in Trash are gone forever. Anything outside Trash is untouched.",
                "shell": "rm -rf ~/.Trash/* ~/.Trash/.[!.]* 2>/dev/null; true",
            },
            "clear-homebrew": {
                "label": "Clear Homebrew downloads",
                "desc":  "Runs `brew cleanup -s` — removes old formula downloads + clears cache.",
                "cost":  "Re-downloads needed on next `brew install` of a formula whose download was pruned (usually fast). Installed brews stay installed.",
                "shell": "command -v brew >/dev/null && brew cleanup -s 2>&1 || echo 'Homebrew not installed — skipping'",
            },
        },
    },

    # ─── System (macOS-level junk) ─────────────────────────────────────
    "system": {
        "label": "System",
        "icon":  "💾",
        "tagline": "macOS system-level junk: installers, indexes, snapshots.",
        "groups": {
            "safe": [
                ("Icon cache",                          "~/Library/Caches/com.apple.iconservices"),
                ("Spotlight parser cache",              "~/Library/Caches/com.apple.parsecd"),
                ("Help system cache",                   "~/Library/Caches/com.apple.helpd"),
                ("CloudKit cache",                      "~/Library/Caches/CloudKit"),
                ("iCloud Drive (bird) cache",           "~/Library/Caches/com.apple.bird"),
                ("CoreFollowUp",                        "~/Library/CoreFollowUp"),
                ("Sharing recent items cache",          "~/Library/Application Support/com.apple.sharedfilelist"),
                ("DiagnosticReports",                   "~/Library/Logs/DiagnosticReports"),
            ],
            "probably_safe": [
                # /Applications and ~/Library/Logs are intentionally not measured here —
                # /Applications would count all your apps, ~/Library/Logs covers all app
                # logs (mostly useful ones). Old-installer detection lives in the action
                # below as `show-old-macos-installers`.
            ],
            "caution": [
                ("System Updates (needs sudo)",         "/Library/Updates"),
                ("System Caches (needs sudo)",          "/Library/Caches"),
                ("Time Machine local snapshots",        "tm-snapshots"),
            ],
        },
        "actions": {
            "clear-system-caches-user": {
                "label": "Clear user-level system caches",
                "desc":  "Clears icon cache, Spotlight parser, help cache, CloudKit cache, iCloud Drive cache, CoreFollowUp.",
                "cost":  "First Finder window reloads icon cache (~1 min). Spotlight re-indexes some content. Help search re-builds. Nothing user-data affected.",
                "shell": "rm -rf ~/Library/Caches/com.apple.iconservices/* "
                         "~/Library/Caches/com.apple.parsecd/* "
                         "~/Library/Caches/com.apple.helpd/* "
                         "~/Library/Caches/CloudKit/* "
                         "~/Library/Caches/com.apple.bird/* "
                         "~/Library/CoreFollowUp/* "
                         "~/Library/Application\\ Support/com.apple.sharedfilelist/* 2>/dev/null; true",
            },
            "clear-diagnostics": {
                "label": "Clear diagnostic reports",
                "desc":  "Removes app crash reports from ~/Library/Logs/DiagnosticReports.",
                "cost":  "Past app crash logs are gone. Useful if you were debugging — otherwise just noise.",
                "shell": "rm -rf ~/Library/Logs/DiagnosticReports/* 2>/dev/null; true",
            },
            "clear-time-machine-snapshots": {
                "label": "Clear local Time Machine snapshots",
                "desc":  "Lists and deletes local APFS snapshots (these can hold 10+ GB of 'free' disk that macOS reserves for backups).",
                "cost":  "Local Time Machine snapshots are gone — your external Time Machine backups on a separate drive are untouched. Frees 'purgeable' space immediately.",
                "shell": "for s in $(tmutil listlocalsnapshots / 2>/dev/null | sed 's/.*\\.\\([0-9]\\{4\\}-[0-9-]*\\)/\\1/' ); do "
                         "echo \"Deleting snapshot $s…\"; tmutil deletelocalsnapshots \"$s\" 2>/dev/null; done; "
                         "echo 'Done. Run `df -h /` to see freed purgeable space.'",
            },
            "show-old-macos-installers": {
                "label": "Show old macOS installers in /Applications",
                "desc":  "Lists 'Install macOS *.app' bundles — typically 12–15 GB each.",
                "cost":  "Just informational — you delete them manually if you don't need them. Safe to delete if you've already upgraded past that macOS version.",
                "shell": "ls -lh /Applications | grep -i 'Install macOS' || echo 'No macOS installer apps found.'",
                "informational": True,
            },
            "show-system-updates": {
                "label": "Check /Library/Updates (sudo required)",
                "desc":  "Surfaces the size of /Library/Updates (system update downloads). The web UI can't delete this without sudo.",
                "cost":  "If you delete /Library/Updates/*, queued updates re-download. Most users can safely clear this after applying updates.",
                "shell": "du -sh /Library/Updates 2>/dev/null || echo 'Empty or not readable'; "
                         "echo ''; echo 'To clear (in your Terminal, not here):'; "
                         "echo '  sudo rm -rf /Library/Updates/*'",
                "informational": True,
                "sudo": True,
            },
        },
    },

}

# Tab structure — top-level navigation
TABS = [
    {"id": "xcode",    "label": "Xcode",    "category": "xcode"},
    {"id": "llms",     "label": "LLMs",     "subcategories": ["llms-claude", "llms-cursor", "llms-chatgpt"]},
    {"id": "docker",   "label": "Docker",   "category": "docker"},
    {"id": "apps",     "label": "Apps",     "category": "apps"},
    {"id": "creative", "label": "Creative", "subcategories": ["creative-adobe", "creative-davinci"]},
    {"id": "system",   "label": "System",   "category": "system"},
]
