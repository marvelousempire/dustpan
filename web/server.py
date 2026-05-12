#!/usr/bin/env python3
"""Xcode Cleanup web UI — localhost-only server.

Runs a tiny HTTP server on http://127.0.0.1:8765 that exposes a few endpoints
the bundled HTML calls. Streams cleanup output via Server-Sent Events.

Pure stdlib. No pip install. macOS only (uses du / bash / xcrun via subprocess).
"""

import csv
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_DIR = Path(__file__).resolve().parent.parent
WEB_DIR  = REPO_DIR / "web"
PORT     = int(os.environ.get("XCC_UI_PORT", "8765"))
HOST     = "127.0.0.1"   # localhost only — never bind 0.0.0.0

# Basic scan: same set the AppleScript cleans in normal mode
CLEANUP_PATHS = [
    ("DerivedData",            "~/Library/Developer/Xcode/DerivedData"),
    ("iOS DeviceSupport",      "~/Library/Developer/Xcode/iOS DeviceSupport"),
    ("watchOS DeviceSupport",  "~/Library/Developer/Xcode/watchOS DeviceSupport"),
    ("tvOS DeviceSupport",     "~/Library/Developer/Xcode/tvOS DeviceSupport"),
    ("Xcode caches",           "~/Library/Caches/com.apple.dt.Xcode"),
    ("SwiftPM cache",          "~/Library/Caches/org.swift.swiftpm"),
    ("Simulator caches",       "~/Library/Developer/CoreSimulator/Caches"),
]

# Deep scan: an exhaustive list of Xcode-adjacent locations, grouped by safety.
# "safe"          → cleanable by normal mode + the script
# "probably_safe" → user must opt-in; bigger reclaim but loses simulator app data, etc.
# "caution"       → never auto-delete; surface size only so user can review manually
DEEP_PATHS = {
    "safe": [
        ("DerivedData",                 "~/Library/Developer/Xcode/DerivedData"),
        ("iOS DeviceSupport",           "~/Library/Developer/Xcode/iOS DeviceSupport"),
        ("watchOS DeviceSupport",       "~/Library/Developer/Xcode/watchOS DeviceSupport"),
        ("tvOS DeviceSupport",          "~/Library/Developer/Xcode/tvOS DeviceSupport"),
        ("visionOS DeviceSupport",      "~/Library/Developer/Xcode/visionOS DeviceSupport"),
        ("Xcode caches",                "~/Library/Caches/com.apple.dt.Xcode"),
        ("SwiftPM cache",               "~/Library/Caches/org.swift.swiftpm"),
        ("Simulator caches",            "~/Library/Developer/CoreSimulator/Caches"),
        ("CoreSimulator Cryptex",       "~/Library/Developer/CoreSimulator/Cryptex"),
        ("iOS Device Logs",             "~/Library/Developer/Xcode/iOS Device Logs"),
        ("Xcode Snapshots",             "~/Library/Developer/Xcode/Snapshots"),
        ("Interface Builder caches",    "~/Library/Developer/Xcode/UserData/IB Support"),
        ("Xcode Products",              "~/Library/Developer/Xcode/Products"),
    ],
    "probably_safe": [
        ("Simulator app data (all)",    "~/Library/Developer/CoreSimulator/Devices"),
        ("Instruments traces",          "~/Library/Application Support/Instruments"),
        ("CocoaPods cache",             "~/Library/Caches/CocoaPods"),
        ("CocoaPods specs",             "~/.cocoapods/repos"),
    ],
    "caution": [
        ("iOS device backups (Finder/iTunes)",  "~/Library/Application Support/MobileSync/Backup"),
        ("Xcode Archives (NEEDED for crash symbolication)", "~/Library/Developer/Xcode/Archives"),
        ("Provisioning Profiles",                "~/Library/MobileDevice/Provisioning Profiles"),
    ],
}

# Deep-action recipes — what each opt-in deep cleanup does
DEEP_ACTIONS = {
    "erase-simulators": {
        "label": "Erase all simulator app data",
        "desc":  "Runs `xcrun simctl erase all`. Keeps simulator devices, wipes installed apps + their data.",
        "cmd":   ["xcrun", "simctl", "erase", "all"],
    },
    "clear-instruments": {
        "label": "Clear Instruments traces",
        "desc":  "Removes all saved .trace files.",
        "shell": "rm -rf ~/Library/Application\ Support/Instruments/*",
    },
    "clear-cocoapods": {
        "label": "Clear CocoaPods caches",
        "desc":  "Removes ~/Library/Caches/CocoaPods + ~/.cocoapods/repos. Re-fetched on next `pod install`.",
        "shell": "rm -rf ~/Library/Caches/CocoaPods/* ~/.cocoapods/repos/*",
    },
    "clear-extras": {
        "label": "Clear Xcode extras",
        "desc":  "Wipes Snapshots, IB caches, iOS Device Logs, Products — all regenerable.",
        "shell": "rm -rf ~/Library/Developer/Xcode/Snapshots/* ~/Library/Developer/Xcode/UserData/IB\ Support/* ~/Library/Developer/Xcode/iOS\ Device\ Logs/* ~/Library/Developer/Xcode/Products/*",
    },
}


def get_status() -> dict:
    total, used, free = shutil.disk_usage("/")
    return {
        "free_gb":  round(free  / 1024**3, 1),
        "used_gb":  round(used  / 1024**3, 1),
        "total_gb": round(total / 1024**3, 1),
        "used_pct": round(used / total * 100, 1),
    }


def get_sizes() -> dict:
    results = []
    for label, path in CLEANUP_PATHS:
        expanded = os.path.expanduser(path)
        try:
            out = subprocess.check_output(
                ["du", "-sk", expanded],
                stderr=subprocess.DEVNULL, timeout=15,
            )
            size_kb = int(out.split()[0])
            results.append({
                "label": label,
                "path": path,
                "size_kb": size_kb,
                "size_gb": round(size_kb / 1024 / 1024, 2),
            })
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            results.append({"label": label, "path": path, "size_kb": 0, "size_gb": 0})
    return {"paths": results, "total_gb": round(sum(p["size_gb"] for p in results), 2)}


def get_report() -> dict:
    csv_path = Path.home() / "Library/Logs/xcode-cleanup-history.csv"
    if not csv_path.exists():
        return {"runs": [], "total_freed_gb": 0, "real_runs": 0}
    runs = []
    with csv_path.open() as f:
        for row in csv.reader(f):
            if len(row) >= 5:
                try:
                    runs.append({
                        "ts":     row[0],
                        "mode":   row[1],
                        "freed":  float(row[2]),
                        "before": float(row[3]),
                        "after":  float(row[4]),
                    })
                except ValueError:
                    continue
    real = [r for r in runs if r["mode"] == "real"]
    return {
        "runs": runs[-30:],
        "real_runs": len(real),
        "total_freed_gb": round(sum(r["freed"] for r in real), 1),
        "max_freed_gb":   round(max((r["freed"] for r in real), default=0), 1),
    }


class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif url.path == "/api/status":
            self._serve_json(get_status())
        elif url.path == "/api/sizes":
            self._serve_json(get_sizes())
        elif url.path == "/api/report":
            self._serve_json(get_report())
        elif url.path == "/api/stream":
            mode = parse_qs(url.query).get("mode", ["dry"])[0]
            self._stream_cleanup(mode)
        elif url.path == "/api/deep-scan":
            self._serve_json(self._deep_scan())
        elif url.path == "/api/deep-actions":
            self._serve_json({"actions": [
                {"id": k, "label": v["label"], "desc": v["desc"]}
                for k, v in DEEP_ACTIONS.items()
            ]})
        elif url.path == "/api/deep-action":
            action = parse_qs(url.query).get("id", [""])[0]
            self._stream_deep_action(action)
        else:
            self.send_error(404)

    def _serve_file(self, name: str, ctype: str):
        path = WEB_DIR / name
        if not path.exists():
            return self.send_error(404)
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _deep_scan(self):
        result = {"categories": [], "total_safe_gb": 0, "total_probably_gb": 0, "total_caution_gb": 0}
        for category, items in DEEP_PATHS.items():
            paths = []
            for label, path in items:
                expanded = os.path.expanduser(path)
                size_kb = 0
                try:
                    out = subprocess.check_output(
                        ["du", "-sk", expanded], stderr=subprocess.DEVNULL, timeout=30,
                    )
                    size_kb = int(out.split()[0])
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                    pass
                size_gb = round(size_kb / 1024 / 1024, 2)
                paths.append({
                    "label": label, "path": path,
                    "size_kb": size_kb, "size_gb": size_gb,
                })
            cat_total = round(sum(p["size_gb"] for p in paths), 2)
            result["categories"].append({"name": category, "paths": paths, "total_gb": cat_total})
            if category == "safe":         result["total_safe_gb"]     = cat_total
            elif category == "probably_safe": result["total_probably_gb"] = cat_total
            elif category == "caution":    result["total_caution_gb"]  = cat_total
        return result

    def _stream_deep_action(self, action_id: str):
        if action_id not in DEEP_ACTIONS:
            return self.send_error(400, f"unknown action: {action_id}")

        action = DEEP_ACTIONS[action_id]

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        before = get_status()
        self._send_sse({"event": "status", "data": before})
        self._send_sse({"event": "line", "data": f"→ {action['label']}"})
        self._send_sse({"event": "line", "data": f"  {action['desc']}"})

        if "shell" in action:
            cmd = ["bash", "-c", action["shell"] + " 2>&1"]
        else:
            cmd = action["cmd"]

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                bufsize=1, text=True,
            )
            for line in proc.stdout:
                self._send_sse({"event": "line", "data": line.rstrip()})
            proc.wait()
            after = get_status()
            self._send_sse({
                "event": "done",
                "data": {
                    "code": proc.returncode,
                    "before_gb": before["free_gb"],
                    "after_gb":  after["free_gb"],
                    "freed_gb":  round(after["free_gb"] - before["free_gb"], 1),
                },
            })
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _stream_cleanup(self, mode: str):
        """SSE stream of cleanup output. Modes: dry / real / force."""
        if mode not in ("dry", "real", "force"):
            return self.send_error(400, "bad mode")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        before = get_status()
        self._send_sse({"event": "status", "data": before})

        script = REPO_DIR / "scripts" / "remote-cleanup.sh"
        cmd = ["bash", str(script)]
        if mode == "dry":
            cmd.append("--dry-run")
        elif mode == "force":
            cmd.append("--force")
        # real mode = no flag; relies on threshold gate

        env = os.environ.copy()

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=env, bufsize=1, text=True,
            )
            for line in proc.stdout:
                self._send_sse({"event": "line", "data": line.rstrip()})
            proc.wait()

            after = get_status()
            self._send_sse({
                "event": "done",
                "data": {
                    "code": proc.returncode,
                    "before_gb": before["free_gb"],
                    "after_gb":  after["free_gb"],
                    "freed_gb":  round(after["free_gb"] - before["free_gb"], 1),
                },
            })
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_sse(self, payload: dict):
        try:
            self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        return  # silence default access log


def main():
    httpd = socketserver.ThreadingTCPServer((HOST, PORT), Handler)
    httpd.daemon_threads = True
    url = f"http://{HOST}:{PORT}"
    print(f"🧹  Xcode Cleanup web UI → \033[1;36m{url}\033[0m")
    print("    Localhost only — never reachable from your network.")
    print("    Press Ctrl+C to stop.\n")

    # Open the browser unless XCC_UI_NO_OPEN=1
    if not os.environ.get("XCC_UI_NO_OPEN"):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n    Stopped.")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
