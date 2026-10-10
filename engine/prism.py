"""PRISM (Block Convey): records and checks what the AI did. Standard library only.

What this module does, in plain words:
  * trace()        records one model exchange (the essay reader's call) so PRISM can score it.
  * screen()       sends one small model call through PRISM's own proxy so its guardrail can BLOCK
                   a bad text (for example an essay with hidden instructions). Only the proxy can block.
  * kb_upload() / kb_search()   put a document in PRISM's Knowledge Base and look a claim up in it.
  * submit_steps() records the retrieve / score / bucket / explain / log trail as one trajectory.
  * evaluation()   reads PRISM's own score for that trajectory back.

Rules this module keeps:
  * No key, or PRISM_SEND not "1": every function returns at once with {"ok": False, "off": True, "why": ...}.
    PRISM never delays or breaks a label.
  * Every network call has a short timeout, never raises, and returns {"ok": False, "why": ...} on failure.
  * A key is read from the environment or a key file, used in a header, and never printed, logged or returned.
  * Scored records are capped (default 150 a day, PRISM_DAILY_LIMIT) because the plan scores only 200 a day.

Anything the vendor's docs do not pin down is written as the most likely shape, kept in ONE small function,
and marked UNVERIFIED SHAPE so it can be fixed in one place.

Environment:
  PRISM_API_KEY | PRISM_KEY_FILE   the PRISM key (a file holding exactly one key on one line)
  PRISM_PROJECT_ID | PRISM_PROJECT the project id, a UUID from Settings > Project (PRISM_PROJECT_ID wins).
                                    A project NAME is refused by PRISM with a 403 that names the right id.
  PRISM_SEND                        "1" turns sending on
  PRISM_BASE_URL                    default https://prism.blockconvey.com
  PRISM_DAILY_LIMIT                 default 150
  PRISM_TIMEOUT                     seconds, default 6
  PRISM_COUNT_FILE                  default data/local/prism_count.json
  ANTHROPIC_API_KEY | ANTHROPIC_KEY_FILE   only used by screen()
  PRISM_SCREEN_MODEL                default claude-haiku-4-5
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://prism.blockconvey.com"
DEFAULT_AGENT = "counselor-copilot"
DEFAULT_LIMIT = 150
DEFAULT_TIMEOUT = 6.0
DEFAULT_SCREEN_MODEL = "claude-haiku-4-5"

_lock = threading.Lock()


# ----------------------------------------------------------------------------------------------
# Settings and keys
# ----------------------------------------------------------------------------------------------

def _base_url() -> str:
    return (os.environ.get("PRISM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def _timeout() -> float:
    try:
        return max(0.1, float(os.environ.get("PRISM_TIMEOUT", DEFAULT_TIMEOUT)))
    except ValueError:
        return DEFAULT_TIMEOUT


def _daily_limit() -> int:
    try:
        return max(0, int(os.environ.get("PRISM_DAILY_LIMIT", DEFAULT_LIMIT)))
    except ValueError:
        return DEFAULT_LIMIT


def _project() -> str:
    return (os.environ.get("PRISM_PROJECT_ID") or os.environ.get("PRISM_PROJECT") or "").strip()


def _read_one_key(env_name: str, file_env: str) -> tuple[str, str]:
    """Return (key, problem). The key comes from the variable, else from the file it names.
    A key file must hold exactly one key on one line; anything else is a problem and no key is used."""
    direct = (os.environ.get(env_name) or "").strip()
    if direct:
        return direct, ""
    path = (os.environ.get(file_env) or "").strip()
    if not path:
        return "", f"neither {env_name} nor {file_env} is set"
    try:
        raw = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return "", f"the file named by {file_env} could not be read"
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if len(lines) != 1 or any(ch.isspace() for ch in lines[0]):
        return "", f"the file named by {file_env} must hold exactly one key on one line"
    return lines[0], ""


def _prism_key() -> tuple[str, str]:
    return _read_one_key("PRISM_API_KEY", "PRISM_KEY_FILE")


def _anthropic_key() -> tuple[str, str]:
    return _read_one_key("ANTHROPIC_API_KEY", "ANTHROPIC_KEY_FILE")


def _scrub(text) -> str:
    """Remove any key value from a string before it is returned. Keys never leave this module."""
    s = text if isinstance(text, str) else str(text)
    for k in (_prism_key()[0], _anthropic_key()[0]):
        if k and k in s:
            s = s.replace(k, "[key hidden]")
    return s


def _clean(obj):
    """Scrub every string inside a result before it is returned."""
    if isinstance(obj, str):
        return _scrub(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def status() -> dict:
    """{"on": bool, "why": str}. On only when a key exists AND PRISM_SEND is "1"."""
    key, problem = _prism_key()
    if not key:
        return {"on": False, "why": f"PRISM is off: no key ({problem}). Nothing is sent."}
    if os.environ.get("PRISM_SEND") != "1":
        return {"on": False, "why": "PRISM is off: a key exists but PRISM_SEND is not 1, so nothing is sent "
                                    "(this protects the 200 scored records a day)."}
    return {"on": True, "why": "PRISM is on: sending records to " + _base_url() + "."}


def _off() -> dict:
    return {"ok": False, "off": True, "why": status()["why"]}


# ----------------------------------------------------------------------------------------------
# Daily count of scored records (traces, trajectories, proxy calls)
# ----------------------------------------------------------------------------------------------

def _count_path() -> Path:
    return Path(os.environ.get("PRISM_COUNT_FILE") or (ROOT / "data" / "local" / "prism_count.json"))


def _today() -> str:
    # PRISM's day resets at 00:00 UTC.
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sent_today() -> int:
    try:
        d = json.loads(_count_path().read_text(encoding="utf-8"))
        return int(d.get("count", 0)) if d.get("date") == _today() else 0
    except (OSError, ValueError, TypeError):
        return 0


def _reserve() -> bool:
    """Count one scored record before sending. False (and nothing counted) when today's limit is reached."""
    with _lock:
        n = sent_today()
        if n >= _daily_limit():
            return False
        p = _count_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"date": _today(), "count": n + 1}), encoding="utf-8")
        except OSError:
            pass  # cannot persist the count: still allow, the in-process limit is best effort
        return True


def _limit_result() -> dict:
    return {"ok": False, "why": "daily limit reached", "sent_today": sent_today(), "limit": _daily_limit()}


# ----------------------------------------------------------------------------------------------
# HTTP (urllib only). Returns (status_code, headers, body_text, error). Never raises.
# ----------------------------------------------------------------------------------------------

def _http(method: str, url: str, headers: dict, body: bytes | None = None, timeout: float | None = None):
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    t = timeout or _timeout()
    try:
        with urllib.request.urlopen(req, timeout=t) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read().decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            text = ""
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, text, ""
    except Exception as e:  # noqa: BLE001 - timeout, refused, DNS, anything: report, never raise
        kind = "timed out" if "timed out" in str(e).lower() else "could not connect"
        return 0, {}, "", f"{kind} ({type(e).__name__})"


def _json(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _call(method: str, path: str, payload: dict | None = None) -> dict:
    """One PRISM API call. Returns {"ok", "status", "data", "why"}."""
    key, _ = _prism_key()
    headers = {"X-PRISMtrace-Key": key, "Accept": "application/json", "User-Agent": "counselor-copilot/1"}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    code, _h, text, err = _http(method, _base_url() + path, headers, body)
    return _finish(code, text, err)


def _finish(code: int, text: str, err: str) -> dict:
    if err:
        return {"ok": False, "status": 0, "data": None, "why": err}
    data = _json(text)
    if 200 <= code < 300:
        return {"ok": True, "status": code, "data": data if data is not None else {}, "why": ""}
    detail = ""
    if isinstance(data, dict):
        detail = str(data.get("detail") or data.get("error") or data.get("message") or "")[:200]
    elif text:
        detail = text[:120]
    return {"ok": False, "status": code, "data": data, "why": f"PRISM answered {code}" + (f": {detail}" if detail else "")}


def _result(r: dict, **extra) -> dict:
    out = {"ok": r["ok"], "status": r["status"]}
    if not r["ok"]:
        out["why"] = r["why"]
    out.update(extra)
    return _clean(out)


# ----------------------------------------------------------------------------------------------
# trace
# ----------------------------------------------------------------------------------------------

def trace(agent_name: str, session_id: str, model: str, input_messages: list, output_message: str,
          latency_ms: int, metadata: dict | None = None, background: bool = False) -> dict:
    """Record one model exchange. agent_name and session_id are required (a trace without a session
    cannot be grouped later). With background=True the send happens on a thread and this returns at once."""
    if not status()["on"]:
        return _off()
    if not agent_name or not session_id:
        return {"ok": False, "why": "agent_name and session_id are required"}
    project = _project()
    if not project:
        return {"ok": False, "why": "no project: set PRISM_PROJECT (or PRISM_PROJECT_ID)"}
    if not _reserve():
        return _limit_result()
    payload = _trace_payload(project, agent_name, session_id, model, input_messages, output_message,
                             latency_ms, metadata)
    if background:
        threading.Thread(target=_send_trace, args=(payload,), daemon=True).start()
        return {"ok": True, "queued": True}
    return _send_trace(payload)


def _trace_payload(project, agent_name, session_id, model, input_messages, output_message, latency_ms, metadata) -> dict:
    # Documented: POST /api/traces. Required project_id, model, input_messages [{role, content}],
    # output_message, latency_ms. Optional session_id, agent_id, agent_name, metadata.
    msgs = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))}
            for m in (input_messages or []) if isinstance(m, dict)]
    meta = {"app": "counselor-copilot"}
    meta.update(metadata or {})
    return {
        "project_id": project,
        "model": str(model or "unknown"),
        "input_messages": msgs,
        "output_message": str(output_message if output_message is not None else ""),
        "latency_ms": int(latency_ms or 0),
        "session_id": str(session_id),
        "agent_id": str(agent_name),     # stable id: PRISM splits one agent into several without it
        "agent_name": str(agent_name),
        "metadata": meta,
    }


def _send_trace(payload: dict) -> dict:
    r = _call("POST", "/api/traces", payload)
    d = r["data"] if isinstance(r["data"], dict) else {}
    return _result(r, id=d.get("id"), session_id=d.get("session_id"), cost_usd=d.get("cost_usd"))


# ----------------------------------------------------------------------------------------------
# screen: the guardrail only BLOCKS on PRISM's own proxy
# ----------------------------------------------------------------------------------------------

def screen(text: str) -> dict:
    """{"blocked": bool, "how": "prism-proxy" | "off", "detail": str}.
    Sends one small model call through PRISM's Anthropic proxy. If a guardrail blocks it, blocked is True."""
    st = status()
    if not st["on"]:
        return {"blocked": False, "how": "off", "detail": st["why"]}
    akey, problem = _anthropic_key()
    if not akey:
        return {"blocked": False, "how": "off",
                "detail": f"No Anthropic key for the screening call ({problem}); the guardrail cannot block without it."}
    pkey, _ = _prism_key()
    if not _reserve():
        return {"blocked": False, "how": "off", "detail": "daily limit reached; text was not screened"}
    model = os.environ.get("PRISM_SCREEN_MODEL") or DEFAULT_SCREEN_MODEL
    headers = {
        "X-PRISMtrace-Key": pkey,
        "x-api-key": akey,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "User-Agent": "counselor-copilot/1",
        # UNVERIFIED SHAPE: whether the proxy reads agent and session from headers. If it does not,
        # proxy records land under an unknown agent. Harmless if ignored.
        "X-PRISMtrace-Agent-Name": DEFAULT_AGENT + "-screen",
        "X-PRISMtrace-Session-Id": "screen-" + uuid.uuid4().hex[:12],
    }
    body = json.dumps(_screen_body(model, text)).encode("utf-8")
    code, hdrs, resp_text, err = _http("POST", _base_url() + "/proxy/anthropic/v1/messages", headers, body)
    if err:
        return _clean({"blocked": False, "how": "off", "detail": f"Screening call failed: {err}"})
    reason = _proxy_block_reason(code, hdrs, resp_text)
    if reason is not None:
        return _clean({"blocked": True, "how": "prism-proxy", "detail": reason})
    if 200 <= code < 300:
        return {"blocked": False, "how": "prism-proxy", "detail": "PRISM's guardrail checked this text and let it through."}
    return _clean({"blocked": False, "how": "off",
                   "detail": f"Screening call answered {code}, which is not a guardrail block: {_error_text(resp_text)}"})


def _screen_body(model: str, text: str) -> dict:
    # The text is the user turn so the guardrails see exactly what the reader would see.
    # The system line keeps the reply tiny and harmless; max_tokens 16 keeps the cost near zero.
    return {"model": model, "max_tokens": 16, "system": "Reply with the single word OK.",
            "messages": [{"role": "user", "content": str(text)[:20000]}]}


def _error_text(resp_text: str) -> str:
    d = _json(resp_text)
    if isinstance(d, dict):
        e = d.get("error")
        if isinstance(e, dict):
            return str(e.get("message") or e.get("type") or "")[:200]
        return str(e or d.get("detail") or d.get("message") or "")[:200]
    return (resp_text or "")[:120]


def _proxy_block_reason(code: int, headers: dict, resp_text: str):
    """Returns the reason text when this is a guardrail block, else None. Fix the block test here only.
    SEEN LIVE 2026-10-10 12:55: a block is an HTTP 200 whose body is a normal-looking message with
    "id": "guardrail-block", "stop_reason": "guardrail_block" and zero tokens used (the provider was never called).
    The 4xx and header tests below are kept as a guess for other rule types."""
    try:
        d = json.loads(resp_text or "")
    except ValueError:
        d = None
    if isinstance(d, dict) and (d.get("stop_reason") == "guardrail_block" or d.get("id") == "guardrail-block"):
        return "PRISM's guardrail stopped this text before it reached the model."
    for h in ("x-prismtrace-blocked", "x-prismtrace-guardrail", "x-prismtrace-block-reason"):
        if h in headers:
            return str(headers[h])[:300] or "blocked by a PRISM guardrail"
    if code in (400, 403, 422, 451):
        low = (resp_text or "").lower()
        if any(w in low for w in ("guardrail", "blocked", "prompt injection", "prompt_injection", "violat")):
            return _error_text(resp_text) or "blocked by a PRISM guardrail"
    return None


# ----------------------------------------------------------------------------------------------
# Knowledge Base
# ----------------------------------------------------------------------------------------------

def kb_upload(path) -> dict:
    """Upload one file to the project's Knowledge Base. Costs no credits and no scored record."""
    if not status()["on"]:
        return _off()
    project = _project()
    if not project:
        return {"ok": False, "why": "no project: set PRISM_PROJECT (or PRISM_PROJECT_ID)"}
    p = Path(path)
    try:
        content = p.read_bytes()
    except OSError:
        return {"ok": False, "why": "the file could not be read"}
    ctype = "text/markdown" if p.suffix.lower() in (".md", ".markdown") else "text/plain"
    boundary = "----cc" + uuid.uuid4().hex
    body, ctype_header = _multipart(boundary, {"project_id": project, "description": f"Counselor Copilot: {p.name}"},
                                    "file", p.name, content, ctype)
    key, _ = _prism_key()
    headers = {"X-PRISMtrace-Key": key, "Content-Type": ctype_header, "Accept": "application/json",
               "User-Agent": "counselor-copilot/1"}
    # Not in the public docs; follows the vendor SDK source (POST /api/knowledge-base/documents, multipart
    # "file" + project_id + description) and was confirmed live (200, chunk_count returned).
    code, _h, text, err = _http("POST", _base_url() + "/api/knowledge-base/documents", headers, body)
    r = _finish(code, text, err)
    d = r["data"] if isinstance(r["data"], dict) else {}
    return _result(r, id=d.get("id"), name=d.get("name"), chunk_count=d.get("chunk_count"))


def _multipart(boundary: str, fields: dict, file_field: str, filename: str, content: bytes, ctype: str):
    crlf = b"\r\n"
    parts = []
    for k, v in fields.items():
        parts += [f"--{boundary}".encode(), f'Content-Disposition: form-data; name="{k}"'.encode(), b"", str(v).encode("utf-8")]
    safe = filename.replace('"', "")
    parts += [f"--{boundary}".encode(),
              f'Content-Disposition: form-data; name="{file_field}"; filename="{safe}"'.encode(),
              f"Content-Type: {ctype}".encode(), b"", content, f"--{boundary}--".encode(), b""]
    return crlf.join(parts), f"multipart/form-data; boundary={boundary}"


def kb_search_result(query: str, top_k: int = 3) -> dict:
    """{"ok", "why", "results": [{"text", "score", "doc"}]}. Used by kb_search and the self-test."""
    if not status()["on"]:
        return {**_off(), "results": []}
    project = _project()
    if not project:
        return {"ok": False, "why": "no project: set PRISM_PROJECT (or PRISM_PROJECT_ID)", "results": []}
    # Path and body follow the vendor SDK source and were confirmed live (200); the public docs do not list them.
    r = _call("POST", "/api/knowledge-base/search", {"query": str(query), "project_id": project, "limit": int(top_k)})
    d = r["data"] if isinstance(r["data"], dict) else {}
    chunks = d.get("results") if isinstance(d.get("results"), list) else (r["data"] if isinstance(r["data"], list) else [])
    return _result(r, results=[_chunk(c) for c in chunks if isinstance(c, dict)], method=d.get("method"))


def _chunk(c: dict) -> dict:
    # Field names observed live on 2026-10-10: content, relevance_score, doc_name (older SDK text said "score").
    doc = c.get("doc_name") or c.get("document_name") or c.get("filename") or c.get("doc_id")
    score = c.get("relevance_score", c.get("score"))
    return {"text": c.get("content") or c.get("text") or "", "score": score, "doc": doc}


def kb_search(query: str, top_k: int = 3) -> list:
    """[{"text", "score", "doc"}], or [] when PRISM is off or the call fails."""
    return kb_search_result(query, top_k)["results"]


# ----------------------------------------------------------------------------------------------
# Trajectory (the retrieve / score / bucket / explain / log trail) and its evaluation
# ----------------------------------------------------------------------------------------------

def _to_trajectory_steps(steps: list) -> list:
    """Map the contract's steps [{"step","what","ms","by"}] to PRISM steps. Steps already carrying
    "step_type" pass through. UNVERIFIED SHAPE: which step_type suits code-only steps is a guess."""
    kind = {"retrieve": "tool_call", "score": "reasoning", "bucket": "reasoning", "explain": "reasoning", "log": "final_answer"}
    out = []
    for s in steps or []:
        if not isinstance(s, dict):
            continue
        if "step_type" in s:
            out.append(dict(s))
            continue
        name = str(s.get("step", "step"))
        st = kind.get(name, "reasoning")
        item = {"step_type": st, "label": name, "output_summary": str(s.get("what", "")),
                "input_summary": f"input to the {name} step (done by {s.get('by', 'code')})", "duration_ms": int(s.get("ms") or 0), "status": "success"}
        if st == "tool_call":
            item["tool_name"] = name
        out.append(item)
    return out


def submit_steps(session_id: str, steps: list, agent_name: str = DEFAULT_AGENT, model: str | None = None,
                 final_status: str = "success") -> dict:
    """Record the visible trail as one trajectory (PRISM scores goal adherence, tool use, efficiency, safety)."""
    if not status()["on"]:
        return _off()
    if not agent_name or not session_id:
        return {"ok": False, "why": "agent_name and session_id are required"}
    project = _project()
    if not project:
        return {"ok": False, "why": "no project: set PRISM_PROJECT (or PRISM_PROJECT_ID)"}
    tsteps = _to_trajectory_steps(steps)
    if not tsteps:
        return {"ok": False, "why": "no steps to send"}
    if not _reserve():
        return _limit_result()
    # Documented in the vendor SDK source: POST /api/trajectories.
    payload = {"project_id": project, "conversation_id": str(session_id), "request_id": uuid.uuid4().hex,
               "agent_id": str(agent_name), "agent_name": str(agent_name), "steps": tsteps,
               "total_duration_ms": sum(s.get("duration_ms") or 0 for s in tsteps),
               "final_status": final_status, "model": model}
    r = _call("POST", "/api/trajectories", payload)
    d = r["data"] if isinstance(r["data"], dict) else {}
    return _result(r, id=d.get("id"), step_count=d.get("step_count"))


def evaluation(trajectory_id: str, retrigger: bool = False) -> dict:
    """Read PRISM's own score for a submitted trajectory. It runs a little after submission, so a first
    read may say it is not ready. retrigger=True asks PRISM to run it again (the vendor SDK's call; may cost a credit)."""
    if not status()["on"]:
        return _off()
    if not trajectory_id:
        return {"ok": False, "why": "trajectory_id is required"}
    project = _project()
    tid = str(trajectory_id)
    if retrigger:
        r = _call("POST", f"/api/trajectories/{tid}/evaluate?project_id={project}", {})
    else:
        # Confirmed live with a key of purpose "custom" (200, a scorecard). Not in the public docs.
        r = _call("GET", f"/api/trajectories/{tid}/evaluation")
    out = _result(r, evaluation=r["data"] if r["ok"] else None, summary=_eval_summary(r["data"]) if r["ok"] else None)
    if not r["ok"] and r["status"] == 404:
        out["why"] = "not ready yet (PRISM scores a little after submission)"
    return out


def _eval_summary(data) -> dict | None:
    """The few numbers worth showing. Field names observed live on 2026-10-10 (scorecard.*_score, passed, failure_reasons)."""
    card = data.get("scorecard") if isinstance(data, dict) else None
    if not isinstance(card, dict):
        return None
    keys = ("overall_score", "safety_score", "correctness_score", "efficiency_score", "robustness_score",
            "passed", "failure_reasons", "evaluation_mode")
    return {k: card.get(k) for k in keys}


def doctor() -> dict:
    """PRISM's own setup check: is real traffic arriving? Read-only, free."""
    if not status()["on"]:
        return _off()
    project = _project()
    r = _call("GET", "/api/setup-doctor?project_id=" + urllib.parse.quote(project, safe=""))
    d = r["data"] if isinstance(r["data"], dict) else {}
    return _result(r, live_connected=d.get("live_connected"), blocked_step=d.get("blocked_step"))


# ----------------------------------------------------------------------------------------------
# Self-check: python -m engine.prism
# ----------------------------------------------------------------------------------------------

def self_test() -> None:
    st = status()
    print("PRISM status:", "ON" if st["on"] else "OFF")
    print(" ", st["why"])
    if not st["on"]:
        print("With no key every PRISM call returns an 'off' answer at once, and the labels are unaffected.")
        print("To try it for real: set PRISM_KEY_FILE, PRISM_PROJECT and PRISM_SEND=1 (see docs/PRISM_SETUP.md).")
        return
    print(f"  Records sent today: {sent_today()} of {_daily_limit()} allowed by this build.")
    t = trace(DEFAULT_AGENT + "-selftest", "selftest-" + uuid.uuid4().hex[:8], "none (self-test)",
              [{"role": "user", "content": "Self-test: no model was called."}], "Self-test record.", 0,
              {"purpose": "self_test"})
    print("Trace:", "sent" if t.get("ok") else "not sent", "-", t.get("why") or f"PRISM stored it (id {t.get('id')})")
    kb_dir = ROOT / "data" / "kb"
    docs = sorted(kb_dir.glob("*.md")) if kb_dir.is_dir() else []
    if not docs:
        print("Knowledge Base: no file in data/kb to upload.")
        return
    small = min(docs, key=lambda p: p.stat().st_size)
    u = kb_upload(small)
    print(f"Knowledge Base upload ({small.name}):", "done" if u.get("ok") else "failed",
          "-", u.get("why") or f"{u.get('chunk_count')} pieces stored")
    s = kb_search_result("how are reach, target and likely labels set", 3)
    if s["ok"]:
        print(f"Knowledge Base search: {len(s['results'])} piece(s) came back.")
        for c in s["results"]:
            print(f"  score {c['score']}  from {c['doc']}:  {c['text'][:90]!r}")
    else:
        print("Knowledge Base search failed -", s["why"])


if __name__ == "__main__":
    self_test()
