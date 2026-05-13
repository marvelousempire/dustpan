"""
Dustpan AI provider dispatch (plan 0006).

Pure Python stdlib (urllib) — no pip installs required.
Handles four API surface variations:
  - OpenAI-compatible  → OpenAI, Perplexity, Groq, Ollama
  - Anthropic          → separate request format + headers
  - Gemini             → Google's generateContent REST API

Usage:
    text = complete("openai", api_key="sk-...", prompt="...")
    text = complete("anthropic", api_key="sk-ant-...", prompt="...")
    text = complete("ollama", api_key="", prompt="...", base_url="http://localhost:11434", model="llama3.2")
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Optional

# ── Provider catalogue ────────────────────────────────────────────────────────

PROVIDERS = {
    "openai":     {"base": "https://api.openai.com",         "fmt": "openai",    "default_model": "gpt-4o-mini"},
    "perplexity": {"base": "https://api.perplexity.ai",      "fmt": "openai",    "default_model": "llama-3.1-sonar-small-128k-chat"},
    "groq":       {"base": "https://api.groq.com/openai",    "fmt": "openai",    "default_model": "llama-3.1-8b-instant"},
    "gemini":     {"base": "https://generativelanguage.googleapis.com", "fmt": "gemini", "default_model": "gemini-1.5-flash"},
    "anthropic":  {"base": "https://api.anthropic.com",      "fmt": "anthropic", "default_model": "claude-3-haiku-20240307"},
    "ollama":     {"base": None,                             "fmt": "openai",    "default_model": "llama3.2"},
}

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Dustpan's disk-cleanup assistant. "
    "You receive structured disk-usage data and respond with a concise, "
    "plain-English 2-sentence recommendation. Be specific about what to clean "
    "and why. Do not use markdown. Do not repeat the numbers back verbatim."
)

# ── HTTP helper ───────────────────────────────────────────────────────────────

def _post(url: str, headers: dict, body: dict, timeout: int = 20) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {err_body[:300]}") from e

# ── Format handlers ───────────────────────────────────────────────────────────

def _openai_complete(base_url: str, api_key: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    resp = _post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        body={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens": 180,
            "temperature": 0.4,
        },
    )
    return resp["choices"][0]["message"]["content"].strip()

def _anthropic_complete(api_key: str, model: str, prompt: str) -> str:
    resp = _post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        body={
            "model": model,
            "max_tokens": 180,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    return resp["content"][0]["text"].strip()

def _gemini_complete(api_key: str, model: str, prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    combined = f"{SYSTEM_PROMPT}\n\n{prompt}"
    resp = _post(
        url,
        headers={"Content-Type": "application/json"},
        body={"contents": [{"parts": [{"text": combined}]}]},
    )
    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()

# ── Public API ────────────────────────────────────────────────────────────────

def complete(
    provider: str,
    api_key: str,
    prompt: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Call the configured AI provider and return the completion text.

    provider : one of the keys in PROVIDERS, or a custom string for Ollama
    api_key  : provider API key (empty string for Ollama)
    prompt   : the user-facing prompt (disk summary)
    model    : override default model for this provider
    base_url : override base URL (required for Ollama)
    """
    pinfo = PROVIDERS.get(provider)
    if pinfo is None:
        raise ValueError(f"Unknown provider: {provider!r}")

    resolved_model    = model    or pinfo["default_model"]
    resolved_base_url = base_url or pinfo["base"] or ""

    fmt = pinfo["fmt"]
    if fmt == "openai":
        if not resolved_base_url:
            raise ValueError(f"No base_url configured for provider {provider!r}")
        return _openai_complete(resolved_base_url, api_key, resolved_model, prompt)
    elif fmt == "anthropic":
        return _anthropic_complete(api_key, resolved_model, prompt)
    elif fmt == "gemini":
        return _gemini_complete(api_key, resolved_model, prompt)
    else:
        raise ValueError(f"Unknown format {fmt!r}")

def build_scan_prompt(category: str, scan_result: dict, habit: Optional[dict] = None) -> str:
    """
    Build the structured prompt sent to the AI after a scan.
    """
    totals = scan_result.get("totals", {})
    safe    = totals.get("safe", 0) or 0
    optin   = totals.get("probably_safe", 0) or 0
    caution = totals.get("caution", 0) or 0
    label   = scan_result.get("label", category)

    lines = [
        f"Category: {label}",
        f"  Safe to delete:    {safe:.1f} GB",
        f"  Opt-in (probably): {optin:.1f} GB",
        f"  Caution (review):  {caution:.1f} GB",
    ]
    if habit:
        gpw = habit.get("growth_gb_per_week", 0)
        dthr = habit.get("days_to_threshold", 9999)
        if gpw > 0:
            lines.append(f"  Growth trend:      +{gpw:.2f} GB/week")
        if dthr < 9999:
            lines.append(f"  Days to threshold: ~{dthr} days")

    lines.append("\nGive a 2-sentence plain-English recommendation.")
    return "\n".join(lines)
