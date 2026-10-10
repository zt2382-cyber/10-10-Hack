"""The one door to the AI models: the Nicrron gateway (OpenAI-compatible).

Standard library only. Never raises: every function returns a dict with "ok" and "error".
The key is read from env NICRRON_API_KEY, else from the file named by env NICRRON_KEY_FILE.
The key is never printed, logged, returned, or placed in an error message.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.nicrron.ai/v1"
DEFAULT_MODEL = "anthropic/claude-haiku-4-5"
DEFAULT_EMBED_MODEL = "openai/text-embedding-3-small"
# Models in this family reject the temperature setting, so we leave it out for them.
NO_TEMPERATURE_PREFIXES = ("anthropic/claude-sonnet-5",)


# ----------------------------------------------------------------------------- key handling

def _key_file_path(raw: str) -> Path:
    """Accept a Windows path or a Git Bash style path such as /c/Projects/key.txt."""
    p = Path(raw)
    if p.exists():
        return p
    m = re.match(r"^/([A-Za-z])/(.*)$", raw)
    if m:
        alt = Path(m.group(1).upper() + ":/" + m.group(2))
        if alt.exists():
            return alt
    return p


def _load_key() -> str:
    key = os.environ.get("NICRRON_API_KEY", "").strip()
    if key:
        return key
    path = os.environ.get("NICRRON_KEY_FILE", "").strip()
    if path:
        try:
            return _key_file_path(path).read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def has_key() -> bool:
    return bool(_load_key())


def _scrub(text: str, key: str) -> str:
    """Remove the key (and anything shaped like one) from text before it goes anywhere."""
    text = str(text)
    if key:
        text = text.replace(key, "[key removed]")
    return re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[key removed]", text)


# ----------------------------------------------------------------------------- defensive JSON

def parse_json(text: str):
    """Pull one JSON object out of model text: handles code fences and chatter around it. None if none found."""
    if not text:
        return None
    t = text.strip()
    fence = re.search(r"```(?:json|JSON)?\s*(.*?)```", t, re.S)
    candidates = [fence.group(1).strip()] if fence else []
    candidates.append(t)
    dec = json.JSONDecoder()
    for cand in candidates:
        try:
            obj = json.loads(cand)
            if isinstance(obj, (dict, list)):
                return obj
        except Exception:
            pass
        for m in re.finditer(r"[{\[]", cand):
            try:
                obj, _ = dec.raw_decode(cand[m.start():])
            except Exception:
                continue
            if isinstance(obj, (dict, list)):
                return obj
    return None


# ----------------------------------------------------------------------------- HTTP

def _request(method: str, path: str, body, key: str, timeout: int):
    """Returns (status, parsed_json_or_None, raw_text, headers_lowercase, ms). status 0 = network failure."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Authorization": "Bearer " + key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    started = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode("utf-8", "replace")
        status, hdrs = resp.status, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        status, hdrs = err.code, {k.lower(): v for k, v in (err.headers or {}).items()}
    except Exception as err:  # timeouts, DNS, refused
        return 0, None, type(err).__name__ + ": " + str(err)[:150], {}, int((time.time() - started) * 1000)
    ms = int((time.time() - started) * 1000)
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = None
    return status, parsed, raw, hdrs, ms


def _error_text(status: int, parsed, raw: str, key: str) -> str:
    msg = ""
    if isinstance(parsed, dict):
        err = parsed.get("error")
        msg = err.get("message", "") if isinstance(err, dict) else (err or "")
    msg = msg or raw
    if status == 0:
        return _scrub("network error: " + msg, key)
    return _scrub("HTTP %d: %s" % (status, str(msg)[:200]), key)


def _result(**kw) -> dict:
    base = {"ok": False, "text": "", "json": None, "model": "", "request_id": "", "latency_ms": 0, "error": ""}
    base.update(kw)
    return base


# ----------------------------------------------------------------------------- chat

def _response_format(json_schema):
    if not json_schema:
        return None
    if isinstance(json_schema, dict) and "schema" in json_schema and "name" in json_schema:
        spec = dict(json_schema)
        spec.setdefault("strict", True)
        return {"type": "json_schema", "json_schema": spec}
    return {"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": json_schema}}


def chat(messages, model=None, fallbacks=None, json_schema=None, max_tokens=900, timeout=40) -> dict:
    """One chat call. Returns {"ok", "text", "json", "model", "request_id", "latency_ms", "error"}. Never raises."""
    key = _load_key()
    if not key:
        return _result(error="no key")
    try:
        model = model or DEFAULT_MODEL
        body = {"model": model, "messages": messages, "max_tokens": max_tokens}
        if fallbacks:
            body["models"] = [model, *fallbacks]
        if not model.startswith(NO_TEMPERATURE_PREFIXES):
            body["temperature"] = 0
        rf = _response_format(json_schema)
        if rf:
            body["response_format"] = rf

        total_ms = 0
        status, parsed, raw, hdrs, ms = _request("POST", "/chat/completions", body, key, timeout)
        total_ms += ms
        # One retry each for the two settings some models refuse, using the server's own words to decide.
        for _ in range(2):
            if status == 400:
                low = raw.lower()
                if "temperature" in body and "temperature" in low:
                    body.pop("temperature")
                elif "response_format" in body and ("response_format" in low or "schema" in low or "json" in low):
                    body.pop("response_format")
                else:
                    break
                status, parsed, raw, hdrs, ms = _request("POST", "/chat/completions", body, key, timeout)
                total_ms += ms
            else:
                break

        request_id = hdrs.get("x-request-id") or hdrs.get("request-id") or ""
        if status != 200 or not isinstance(parsed, dict):
            return _result(request_id=request_id, latency_ms=total_ms, error=_error_text(status, parsed, raw, key))
        try:
            text = parsed["choices"][0]["message"].get("content") or ""
        except Exception:
            text = ""
        served = str(parsed.get("model") or model)
        if not text.strip():
            return _result(model=served, request_id=request_id, latency_ms=total_ms,
                           error="the model returned no text (raise max_tokens?)")
        return _result(ok=True, text=text, json=parse_json(text) if json_schema else None, model=served,
                       request_id=request_id, latency_ms=total_ms)
    except Exception as err:  # last resort: never raise
        return _result(error=_scrub("unexpected error: " + type(err).__name__ + ": " + str(err)[:150], key))


# ----------------------------------------------------------------------------- embeddings and model list

def embed(texts, model=DEFAULT_EMBED_MODEL, timeout=40) -> dict:
    """Returns {"ok", "vectors": [[float]], "model", "request_id", "latency_ms", "error"}. Never raises."""
    key = _load_key()
    out = {"ok": False, "vectors": [], "model": model, "request_id": "", "latency_ms": 0, "error": "", "http_status": None}
    if not key:
        out["error"] = "no key"
        return out
    try:
        if isinstance(texts, str):
            texts = [texts]
        status, parsed, raw, hdrs, ms = _request("POST", "/embeddings", {"model": model, "input": list(texts)}, key, timeout)
        out["http_status"] = status
        out["latency_ms"] = ms
        out["request_id"] = hdrs.get("x-request-id") or hdrs.get("request-id") or ""
        if status != 200 or not isinstance(parsed, dict):
            out["error"] = _error_text(status, parsed, raw, key)
            return out
        rows = sorted(parsed.get("data", []), key=lambda r: r.get("index", 0))
        out["vectors"] = [r["embedding"] for r in rows]
        out["model"] = str(parsed.get("model") or model)
        out["ok"] = len(out["vectors"]) == len(texts)
        if not out["ok"]:
            out["error"] = "got %d vectors for %d texts" % (len(out["vectors"]), len(texts))
        return out
    except Exception as err:
        out["error"] = _scrub("unexpected error: " + type(err).__name__ + ": " + str(err)[:150], key)
        return out


def list_models(timeout=30) -> dict:
    """Returns {"ok", "models": [ids], "error"}. Never raises."""
    key = _load_key()
    out = {"ok": False, "models": [], "error": ""}
    if not key:
        out["error"] = "no key"
        return out
    try:
        status, parsed, raw, hdrs, ms = _request("GET", "/models", None, key, timeout)
        if status != 200 or not isinstance(parsed, dict):
            out["error"] = _error_text(status, parsed, raw, key)
            return out
        out["models"] = sorted(str(m.get("id")) for m in parsed.get("data", []) if isinstance(m, dict) and m.get("id"))
        out["ok"] = True
        return out
    except Exception as err:
        out["error"] = _scrub("unexpected error: " + type(err).__name__ + ": " + str(err)[:150], key)
        return out


if __name__ == "__main__":
    print("key present:", has_key())
    r = chat([{"role": "user", "content": "Reply with the single word: ready"}], max_tokens=20)
    print({k: v for k, v in r.items() if k != "json"})
    print("parse_json check:", parse_json('Sure!\n```json\n{"a": 1}\n```'))
