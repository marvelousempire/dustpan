"""
Dustpan database module (plan 0006).

Provides a thin Postgres connection pool, DDL migrations, and CRUD helpers.
Completely optional — if DATABASE_URL is not set or psycopg2 is not installed,
every public function is a no-op and is_available() returns False.

Security note: API keys are stored AES-256-GCM encrypted using DUSTPAN_MASTER_KEY.
If the cryptography package is not installed, keys are stored with a "PLAIN:" prefix
as plaintext (acceptable for local-only deployments; not recommended for shared hosts).
"""

import hashlib
import json
import os
import sys
import time
from typing import Any, Optional

# ── Optional imports (no hard failure when not installed) ────────────────────

_psycopg2: Any = None
_pool: Any = None
_AESGCM: Any = None

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    _psycopg2 = psycopg2
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _AESGCM = AESGCM
except ImportError:
    pass

# ── Configuration ─────────────────────────────────────────────────────────────

DATABASE_URL    = os.environ.get("DATABASE_URL", "")
MASTER_KEY      = os.environ.get("DUSTPAN_MASTER_KEY", "")

# ── DDL ───────────────────────────────────────────────────────────────────────

_MIGRATIONS = [
    # api_keys: encrypted provider key vault
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id          serial      PRIMARY KEY,
        provider    text        NOT NULL UNIQUE,
        key_enc     bytea       NOT NULL,
        created_at  timestamptz NOT NULL DEFAULT now(),
        updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    # ollama_settings: URL + model for local models
    """
    CREATE TABLE IF NOT EXISTS ollama_settings (
        id          serial      PRIMARY KEY,
        url         text        NOT NULL DEFAULT 'http://ollama:11434',
        model       text        NOT NULL DEFAULT 'llama3.2',
        updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    # runs: every scan + clean operation
    """
    CREATE TABLE IF NOT EXISTS runs (
        id              serial      PRIMARY KEY,
        ts              timestamptz NOT NULL DEFAULT now(),
        mode            text        NOT NULL,
        category        text,
        tier            text,
        freed_gb        numeric(10,3),
        duration_ms     int,
        disk_before_gb  numeric(10,1),
        disk_after_gb   numeric(10,1)
    )
    """,
    # category_snapshots: periodic space readings for the habit engine
    """
    CREATE TABLE IF NOT EXISTS category_snapshots (
        id          serial      PRIMARY KEY,
        ts          timestamptz NOT NULL DEFAULT now(),
        category    text        NOT NULL,
        safe_gb     numeric(10,3) NOT NULL DEFAULT 0,
        optin_gb    numeric(10,3) NOT NULL DEFAULT 0,
        caution_gb  numeric(10,3) NOT NULL DEFAULT 0
    )
    """,
    # habits: cached computed slopes (updated after each snapshot batch)
    """
    CREATE TABLE IF NOT EXISTS habits (
        id                  serial      PRIMARY KEY,
        category            text        NOT NULL UNIQUE,
        computed_at         timestamptz NOT NULL DEFAULT now(),
        growth_gb_per_week  numeric(8,4),
        days_to_threshold   int,
        threshold_gb        numeric(8,2) NOT NULL DEFAULT 20.0,
        recommendation      text
    )
    """,
]

# ── Encryption helpers ────────────────────────────────────────────────────────

def _derive_key(master: str) -> bytes:
    """Derive 32-byte AES key from master key string via SHA-256."""
    return hashlib.sha256(master.encode()).digest()

def encrypt_key(plaintext: str) -> bytes:
    """AES-256-GCM encrypt. Returns 12-byte nonce + ciphertext+tag."""
    if not MASTER_KEY:
        # No master key → store plaintext with prefix (local-only fallback)
        return b"PLAIN:" + plaintext.encode()
    if _AESGCM is None:
        return b"PLAIN:" + plaintext.encode()
    nonce = os.urandom(12)
    ct = _AESGCM(_derive_key(MASTER_KEY)).encrypt(nonce, plaintext.encode(), None)
    return nonce + ct

def decrypt_key(data: bytes) -> str:
    """Decrypt AES-256-GCM blob or plaintext fallback."""
    if data[:6] == b"PLAIN:":
        return data[6:].decode()
    if _AESGCM is None or not MASTER_KEY:
        raise ValueError("cryptography package or DUSTPAN_MASTER_KEY not available")
    nonce, ct = data[:12], data[12:]
    return _AESGCM(_derive_key(MASTER_KEY)).decrypt(nonce, ct, None).decode()

# ── Connection pool ───────────────────────────────────────────────────────────

def _init_pool() -> bool:
    """Initialise the connection pool. Returns True on success."""
    global _pool
    if _psycopg2 is None or not DATABASE_URL:
        return False
    if _pool is not None:
        return True
    try:
        _pool = _psycopg2.pool.ThreadedConnectionPool(1, 4, DATABASE_URL)
        return True
    except Exception as e:
        print(f"[db] pool init failed: {e}", file=sys.stderr)
        return False

def is_available() -> bool:
    """Return True when Postgres is configured and reachable."""
    if _psycopg2 is None or not DATABASE_URL:
        return False
    if _pool is None:
        _init_pool()
    return _pool is not None

def _get() -> Any:
    if not _init_pool():
        raise RuntimeError("database not available")
    return _pool.getconn()

def _put(conn: Any) -> None:
    if _pool:
        _pool.putconn(conn)

# ── Query helpers ─────────────────────────────────────────────────────────────

def execute(sql: str, params: tuple = ()) -> None:
    conn = _get()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        cur.close()
    finally:
        _put(conn)

def fetchall(sql: str, params: tuple = ()) -> list:
    conn = _get()
    try:
        cur = conn.cursor(_psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows
    finally:
        _put(conn)

def fetchone(sql: str, params: tuple = ()) -> Optional[dict]:
    conn = _get()
    try:
        cur = conn.cursor(_psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        _put(conn)

# ── Migrations ────────────────────────────────────────────────────────────────

def migrate() -> None:
    """Run DDL migrations. Safe to call on every startup — all are IF NOT EXISTS."""
    if not is_available():
        return
    conn = _get()
    try:
        cur = conn.cursor()
        for ddl in _MIGRATIONS:
            cur.execute(ddl)
        conn.commit()
        cur.close()
        print("[db] migrations OK", file=sys.stderr)
    except Exception as e:
        conn.rollback()
        print(f"[db] migration error: {e}", file=sys.stderr)
    finally:
        _put(conn)

# ── Domain helpers ────────────────────────────────────────────────────────────

def save_api_key(provider: str, key_plaintext: str) -> None:
    enc = encrypt_key(key_plaintext)
    execute(
        """
        INSERT INTO api_keys (provider, key_enc, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (provider) DO UPDATE
          SET key_enc = EXCLUDED.key_enc, updated_at = now()
        """,
        (provider, enc),
    )

def get_api_key(provider: str) -> Optional[str]:
    row = fetchone("SELECT key_enc FROM api_keys WHERE provider = %s", (provider,))
    if not row:
        return None
    return decrypt_key(bytes(row["key_enc"]))

def delete_api_key(provider: str) -> None:
    execute("DELETE FROM api_keys WHERE provider = %s", (provider,))

def list_key_providers() -> list:
    """Return list of provider names that have a key stored (no values)."""
    rows = fetchall("SELECT provider FROM api_keys ORDER BY provider")
    return [r["provider"] for r in rows]

def get_ollama_settings() -> dict:
    row = fetchone("SELECT url, model FROM ollama_settings ORDER BY id DESC LIMIT 1")
    if row:
        return {"url": row["url"], "model": row["model"]}
    return {"url": os.environ.get("OLLAMA_URL", "http://ollama:11434"),
            "model": os.environ.get("OLLAMA_MODEL", "llama3.2")}

def save_ollama_settings(url: str, model: str) -> None:
    execute("DELETE FROM ollama_settings", ())
    execute("INSERT INTO ollama_settings (url, model) VALUES (%s, %s)", (url, model))

def record_snapshot(category: str, scan_result: dict) -> None:
    """Write a category_snapshots row after every scan."""
    safe   = float(scan_result.get("totals", {}).get("safe", 0) or 0)
    optin  = float(scan_result.get("totals", {}).get("probably_safe", 0) or 0)
    caution= float(scan_result.get("totals", {}).get("caution", 0) or 0)
    execute(
        "INSERT INTO category_snapshots (category, safe_gb, optin_gb, caution_gb) "
        "VALUES (%s, %s, %s, %s)",
        (category, safe, optin, caution),
    )

def record_run(mode: str, category: Optional[str], tier: Optional[str],
               freed_gb: float, duration_ms: int,
               disk_before_gb: float, disk_after_gb: float) -> None:
    execute(
        "INSERT INTO runs (mode, category, tier, freed_gb, duration_ms, "
        "disk_before_gb, disk_after_gb) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (mode, category, tier, freed_gb, duration_ms, disk_before_gb, disk_after_gb),
    )

# ── Habit computation ─────────────────────────────────────────────────────────

_DEFAULT_THRESHOLDS = {
    "xcode": 20.0,
    "llms":  10.0,
    "docker": 15.0,
    "apps":   5.0,
    "browsers": 3.0,
    "downloads": 10.0,
    "temp":   2.0,
    "archives": 5.0,
    "system": 5.0,
    "creative": 10.0,
}

def compute_habits() -> list:
    """
    Compute growth slope for every category using last 28 days of snapshots.
    Returns list of habit dicts. Skips categories with < 2 data points.
    """
    if not is_available():
        return []
    rows = fetchall(
        "SELECT category, ts, safe_gb + optin_gb + caution_gb AS total "
        "FROM category_snapshots "
        "WHERE ts > now() - INTERVAL '28 days' "
        "ORDER BY category, ts"
    )
    # Group by category
    from collections import defaultdict
    by_cat: dict = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)

    habits = []
    for cat, points in by_cat.items():
        if len(points) < 2:
            continue
        xs = [(p["ts"] - points[0]["ts"]).total_seconds() / 86400.0 for p in points]
        ys = [float(p["total"]) for p in points]
        n = len(xs)
        xbar = sum(xs) / n
        ybar = sum(ys) / n
        denom = sum((x - xbar) ** 2 for x in xs)
        slope_per_day = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom if denom > 0 else 0
        slope_per_week = slope_per_day * 7
        current = ys[-1]
        threshold = _DEFAULT_THRESHOLDS.get(cat, 15.0)
        if slope_per_day > 0:
            days_left = int((threshold - current) / slope_per_day)
        else:
            days_left = 9999
        habits.append({
            "category":           cat,
            "growth_gb_per_week": round(slope_per_week, 3),
            "days_to_threshold":  days_left,
            "current_gb":         round(current, 2),
            "threshold_gb":       threshold,
            "recommendation":     None,
        })
    return habits
