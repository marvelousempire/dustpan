# DustPan Changelog Context

## Current Version

DustPan is moving from `0.28.2` to `0.28.3`.

## Recent Releases

- `0.28.3` — Disk Activity cockpit and server bottom density. Adds bounded
  latest-file activity with app inference, charts, and meters; tightens Server
  Performance lower panels.
- `0.28.2` — AI rule refresh for dashboard release discipline. Codifies server
  status visibility, version/changelog coupling, Tech Stack modal updates, and
  meter-rich Server Performance behavior.
- `0.28.1` — Header status pill and system stack modal. The top-left version
  chip now shows a live server LED, connected host/port, and opens a two-tab
  Change Log + Tech Stack modal.
- `0.28.0` — Realtime Server Performance analytics. Adds Mac/Linux snapshot and
  SSE performance APIs, Ultra Dashboard live meter wall, Detailed Activity
  Monitor, process/network/service views, bottleneck radar, and DustBench.
- `0.27.9` — AI_AGENT_RULES Provider Coverage. Extends compact handbook loading
  from Ask DustPan chat to every API-key provider call.

## This Release

`0.28.3` adds the latest-file Disk/Overview activity cockpit and improves the
Server Performance lower-panel density. The file-activity surface is read-only,
bounded, best-effort inference only, and must not become a full-disk watcher or
a cleanup action.
