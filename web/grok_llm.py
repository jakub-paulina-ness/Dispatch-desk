"""Call Grok as the live dispatcher/driver. Stdlib only. Key from XAI_API_KEY."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.x.ai/v1/chat/completions"
# Fast non-reasoning Grok 4.20 — ~0.6s on this key. Override with GROK_DESK_MODEL.
MODEL = os.environ.get("GROK_DESK_MODEL") or "grok-4.20-0309-non-reasoning"
LABEL = "Grok 4.20 fast"


def api_key() -> str:
    return (os.environ.get("XAI_API_KEY") or "").strip()


def chat(messages: list[dict], *, timeout: float = 12.0) -> str:
    key = api_key()
    if not key:
        raise RuntimeError("XAI_API_KEY is not set")
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Grok HTTP {exc.code}: {err[:240]}") from exc
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("Grok returned no choices")
    return str((choices[0].get("message") or {}).get("content") or "")


def parse_json(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Grok did not return JSON")
    obj = json.loads(raw[start : end + 1])
    if not isinstance(obj, dict):
        raise RuntimeError("Grok JSON was not an object")
    return obj
