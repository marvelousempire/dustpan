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

def has_configured_provider() -> bool:
    """Return True if any AI key or Ollama URL is available."""
    # Check env vars for keys
    key_env_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                    "GROQ_API_KEY", "PERPLEXITY_API_KEY"]
    for var in key_env_vars:
        if os.environ.get(var, "").strip():
            return True
    # Check Ollama
    if os.environ.get("OLLAMA_URL", "").strip():
        return True
    # Check DB-stored keys via store module if available
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import sqlite_store as ss
        if ss.is_available():
            keys = ss.list_api_keys()
            if keys:
                return True
    except Exception:
        pass
    return False


def complete_agent(
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> str:
    """
    Higher-level complete() for agent use — takes separate system + user
    strings, uses a larger token budget, and auto-selects the first
    configured provider.

    Called from agent.py; the agent passes its own system prompt and
    full context as the user message.
    """
    # Auto-detect first configured provider
    provider_order = [
        ("anthropic",  os.environ.get("ANTHROPIC_API_KEY", "")),
        ("openai",     os.environ.get("OPENAI_API_KEY",    "")),
        ("gemini",     os.environ.get("GEMINI_API_KEY",    "")),
        ("groq",       os.environ.get("GROQ_API_KEY",      "")),
        ("perplexity", os.environ.get("PERPLEXITY_API_KEY","")),
    ]
    provider, key = next(
        ((p, k) for p, k in provider_order if k.strip()),
        (None, None)
    )

    # Try DB-stored keys if env vars not set
    if not provider:
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            import sqlite_store as ss
            if ss.is_available():
                for p in ["anthropic", "openai", "gemini", "groq", "perplexity"]:
                    k = ss.get_api_key(p)
                    if k:
                        provider, key = p, k
                        break
        except Exception:
            pass

    # Try Ollama as last resort
    if not provider:
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        provider, key = "ollama", ""

    pinfo   = PROVIDERS[provider]
    model   = pinfo["default_model"]
    fmt     = pinfo["fmt"]
    base    = pinfo["base"] or os.environ.get("OLLAMA_URL", "http://localhost:11434")

    # Compose the chat body with the agent's system + user messages
    if fmt == "anthropic":
        resp = _post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            body={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60,
        )
        return resp["content"][0]["text"].strip()

    elif fmt == "openai":
        url = base.rstrip("/") + "/v1/chat/completions"
        resp = _post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            body={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=60,
        )
        return resp["choices"][0]["message"]["content"].strip()

    elif fmt == "gemini":
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={key}"
        )
        combined = f"{system}\n\n{user}"
        resp = _post(
            url,
            headers={"Content-Type": "application/json"},
            body={"contents": [{"parts": [{"text": combined}]}]},
            timeout=60,
        )
        return resp["candidates"][0]["content"]["parts"][0]["text"].strip()

    raise ValueError(f"Unknown format: {fmt!r}")


# ── Plan 0023: Tool-calling loop ─────────────────────────────────────────────
# Supports multi-turn tool-use for Anthropic + OpenAI. Other providers fall
# back to text-only (no tool-use). The loop is bounded by max_rounds.
#
# Usage:
#   complete_with_tools(
#       provider="anthropic",
#       api_key=key,
#       system="You are SADPA, ...",
#       messages=[{"role":"user","content":"What's eating my disk?"}],
#       tools=agent_tools.schemas_anthropic(),
#       tool_runner=lambda name, args: agent_tools.run_tool(name, args, ctx),
#       on_event=lambda ev: send_sse(ev),
#       approval_checker=lambda name, args: needs_approval(...),
#   )
#
# `on_event` receives:
#   {"event":"provider_info",     "data":{"provider","model"}}
#   {"event":"assistant_text",    "data":{"text"}}
#   {"event":"tool_use_start",    "data":{"id","name","input"}}
#   {"event":"tool_use_result",   "data":{"id","ok","result"}}
#   {"event":"tool_approval_needed","data":{"id","name","input"}}  -> stops the loop
#   {"event":"assistant_done",    "data":{"usage","rounds"}}

def complete_with_tools(
    provider:         str,
    api_key:          str,
    system:           str,
    messages:         list[dict],
    tools:            Optional[list[dict]],
    tool_runner:      Optional[callable] = None,
    on_event:         Optional[callable] = None,
    approval_checker: Optional[callable] = None,
    pending_results:  Optional[list[dict]] = None,
    max_tokens:       int = 4096,
    max_rounds:       int = 10,
    model_override:   Optional[str] = None,
) -> dict:
    """
    Multi-turn tool-use loop. Returns:
      {"ok": True, "messages": [...], "usage": {...}, "rounds": N, "stopped_for_approval": bool}

    On unsupported provider returns: {"ok": False, "unsupported": True, "reason": "..."}.

    If `approval_checker(name, args) -> bool` returns True for a tool call,
    the loop stops, emits `tool_approval_needed`, and returns
    `stopped_for_approval=True`. The caller persists `messages` + pending
    tool-call ids, then resumes by re-calling with `pending_results=[...]`
    populated for the approved/rejected calls.
    """
    if provider not in ("anthropic", "openai"):
        if on_event:
            on_event({"event": "provider_info", "data": {
                "provider": provider, "tool_use_supported": False,
            }})
        return {"ok": False, "unsupported": True,
                "reason": f"{provider} does not support tool-use in DustPan yet"}

    pinfo = PROVIDERS.get(provider) or {}
    model = model_override or pinfo.get("default_model", "")

    if on_event:
        on_event({"event": "provider_info", "data": {
            "provider": provider, "model": model, "tool_use_supported": True,
        }})

    # Conversation lives in `messages` and grows each round.
    msgs = list(messages)

    # If we have pending tool results from a prior approval gate, inject them now
    if pending_results:
        if provider == "anthropic":
            tr_blocks = []
            for r in pending_results:
                if r.get("approved"):
                    tr_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": r["id"],
                        "content": json.dumps(r.get("result", {"ok": True})),
                    })
                else:
                    tr_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": r["id"],
                        "content": "User rejected this action.",
                        "is_error": True,
                    })
            msgs.append({"role": "user", "content": tr_blocks})
        else:  # openai
            for r in pending_results:
                msgs.append({
                    "role": "tool",
                    "tool_call_id": r["id"],
                    "content": (json.dumps(r.get("result", {"ok": True}))
                                if r.get("approved") else "User rejected this action."),
                })

    rounds = 0
    usage  = {"input_tokens": 0, "output_tokens": 0}

    while rounds < max_rounds:
        rounds += 1

        if provider == "anthropic":
            body = {
                "model":      model,
                "max_tokens": max_tokens,
                "system":     system,
                "messages":   msgs,
                "tools":      tools or [],
            }
            resp = _post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         api_key,
                    "anthropic-version": "2023-06-01",
                },
                body=body,
                timeout=120,
            )
            u = resp.get("usage", {}) or {}
            usage["input_tokens"]  += u.get("input_tokens", 0)
            usage["output_tokens"] += u.get("output_tokens", 0)

            stop_reason = resp.get("stop_reason", "")
            content     = resp.get("content", []) or []

            # Surface text blocks
            text_chunks = []
            tool_uses   = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    text_chunks.append(block.get("text", ""))
                elif btype == "tool_use":
                    tool_uses.append(block)

            if text_chunks and on_event:
                joined = "\n".join(t for t in text_chunks if t.strip())
                if joined:
                    on_event({"event": "assistant_text", "data": {"text": joined}})

            # Add assistant turn to history
            msgs.append({"role": "assistant", "content": content})

            if not tool_uses or stop_reason == "end_turn":
                # Done
                break

            # Check approvals first — if ANY call in this round needs approval,
            # we stop the whole loop, return the unresolved tool_uses, and let
            # the client handle re-entry.
            pending_for_approval = []
            for tu in tool_uses:
                name = tu.get("name", "")
                inp  = tu.get("input", {}) or {}
                if approval_checker and approval_checker(name, inp):
                    pending_for_approval.append({"id": tu.get("id"), "name": name, "input": inp})

            if pending_for_approval:
                for p in pending_for_approval:
                    if on_event:
                        on_event({"event": "tool_approval_needed", "data": p})
                return {
                    "ok": True, "messages": msgs, "usage": usage, "rounds": rounds,
                    "stopped_for_approval": True,
                    "pending_calls": pending_for_approval,
                }

            # Execute all tool calls, append results as a single user turn
            tr_blocks = []
            for tu in tool_uses:
                tid  = tu.get("id")
                name = tu.get("name", "")
                inp  = tu.get("input", {}) or {}
                if on_event:
                    on_event({"event": "tool_use_start", "data": {"id": tid, "name": name, "input": inp}})
                result = (tool_runner(name, inp) if tool_runner
                          else {"ok": False, "error": "no tool runner configured"})
                if on_event:
                    on_event({"event": "tool_use_result", "data": {"id": tid, "name": name, **result}})
                tr_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tid,
                    "content": json.dumps(result)[:50_000],  # cap to avoid context blowup
                })
            msgs.append({"role": "user", "content": tr_blocks})
            continue

        else:  # openai
            url  = "https://api.openai.com/v1/chat/completions"
            # OpenAI requires system as a message
            oai_msgs = [{"role": "system", "content": system}] + msgs
            body = {
                "model":    model,
                "messages": oai_msgs,
                "tools":    tools or [],
                "tool_choice": "auto" if (tools or []) else "none",
                "max_tokens": max_tokens,
            }
            resp = _post(
                url,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                body=body,
                timeout=120,
            )
            u = resp.get("usage", {}) or {}
            usage["input_tokens"]  += u.get("prompt_tokens", 0)
            usage["output_tokens"] += u.get("completion_tokens", 0)

            msg = resp["choices"][0]["message"]
            finish = resp["choices"][0].get("finish_reason", "")
            text = (msg.get("content") or "").strip()
            tool_calls = msg.get("tool_calls") or []

            if text and on_event:
                on_event({"event": "assistant_text", "data": {"text": text}})

            # Add the assistant message to history (preserving tool_calls)
            asst_msg: dict = {"role": "assistant", "content": text}
            if tool_calls:
                asst_msg["tool_calls"] = tool_calls
            msgs.append(asst_msg)

            if not tool_calls or finish == "stop":
                break

            # Approval check
            pending_for_approval = []
            for tc in tool_calls:
                name = tc.get("function", {}).get("name", "")
                try:
                    inp = json.loads(tc.get("function", {}).get("arguments", "{}"))
                except json.JSONDecodeError:
                    inp = {}
                if approval_checker and approval_checker(name, inp):
                    pending_for_approval.append({"id": tc.get("id"), "name": name, "input": inp})

            if pending_for_approval:
                for p in pending_for_approval:
                    if on_event:
                        on_event({"event": "tool_approval_needed", "data": p})
                return {
                    "ok": True, "messages": msgs, "usage": usage, "rounds": rounds,
                    "stopped_for_approval": True,
                    "pending_calls": pending_for_approval,
                }

            # Run each tool call, append a tool message per call
            for tc in tool_calls:
                tid  = tc.get("id")
                name = tc.get("function", {}).get("name", "")
                try:
                    inp = json.loads(tc.get("function", {}).get("arguments", "{}"))
                except json.JSONDecodeError:
                    inp = {}
                if on_event:
                    on_event({"event": "tool_use_start", "data": {"id": tid, "name": name, "input": inp}})
                result = (tool_runner(name, inp) if tool_runner
                          else {"ok": False, "error": "no tool runner configured"})
                if on_event:
                    on_event({"event": "tool_use_result", "data": {"id": tid, "name": name, **result}})
                msgs.append({
                    "role":         "tool",
                    "tool_call_id": tid,
                    "content":      json.dumps(result)[:50_000],
                })
            continue

    if on_event:
        on_event({"event": "assistant_done", "data": {"usage": usage, "rounds": rounds}})

    return {
        "ok":                    True,
        "messages":              msgs,
        "usage":                 usage,
        "rounds":                rounds,
        "stopped_for_approval":  False,
    }


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
