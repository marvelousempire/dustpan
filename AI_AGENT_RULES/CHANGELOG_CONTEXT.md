# DustPan Changelog Context

## Current Version

DustPan is moving from `0.27.8` to `0.27.9`.

## Recent Releases

- `0.27.8` — AI_AGENT_RULES Handbook. Added the root handbook and wired Ask
  DustPan chat to load compact local-law context with read-on-demand section
  lookup.
- `0.27.7` — Dev Build Rescue Payload. DustPan learned that Claude Desktop
  `vm_bundles` can be the real 10+ GB blocker during iOS device builds, and
  encoded scoped cleanup plus broader build-space diagnosis.
- `0.27.6` — Xcode Build Rescue. Added guarded Xcode/SwiftPM cleanup for
  disk-full build failures.

## This Release

`0.27.9` extends the same compact `AI_AGENT_RULES` context to DustPan's lighter
scan-summary and diagnosis provider calls, so every API-key AI path reads the
local handbook before answering.
