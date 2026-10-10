"""Counselor Copilot: one small local server. Standard library only.

    python server.py            ->  http://localhost:8765/

Serves the screen in web/ and four small routes:
    GET  /api/students          the SYNTHETIC demo students
    POST /api/run               a student in, the full result out
    GET  /api/colleges?q=text   name search over the 300 colleges
    GET  /api/cases             the school's own finished cases   POST /api/cases  add one
Keys are read from environment variables only (see README). Nothing is sent to PRISM unless PRISM_SEND=1.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import colleges as C  # noqa: E402
from engine import pipeline  # noqa: E402

PORT = int(os.environ.get("PORT", "8765"))
# The teammate-built applicant-evidence scorer orders the example cases by default (see engine/evidence_adapter.py).
os.environ.setdefault("SIMILARITY_PLUGIN", "engine.evidence_adapter:rank")
MAX_BODY = 400_000


def _caselog():
    try:
        from engine import caselog
        return caselog
    except Exception:
        return None


def _tracker():
    try:
        from engine import tracker
        return tracker
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "CounselorCopilot/0.1"

    def log_message(self, fmt, *args):  # quiet, and never log request bodies (they hold student text)
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?")[0]))

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            return None
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        if path == "/api/students":
            return self._send(200, pipeline.demo_students())
        if path == "/api/colleges":
            q = (parse_qs(url.query).get("q") or [""])[0].strip().lower()
            hits = [{"id": c["id"], "name": c["name"], "state": c["state"], "admit_rate": c["admit_rate"]}
                    for c in C.load_colleges() if q and q in c["name"].lower()]
            hits.sort(key=lambda c: (not c["name"].lower().startswith(q), c["name"]))
            return self._send(200, hits[:12])
        if path == "/api/cases":
            cl = _caselog()
            return self._send(200, cl.load_cases() if cl else [])
        if path == "/api/tracker":
            key = (parse_qs(url.query).get("student") or ["current"])[0]
            return self._send(200, _tracker().get(key) if _tracker() else {})
        if path == "/api/health":
            return self._send(200, {"ok": True})
        return self._static(path)

    def _same_origin(self) -> bool:
        """A page on another website must not be able to post here (it could save a case or spend model calls)."""
        origin = self.headers.get("Origin")
        if origin is None:
            return True  # not a browser cross-site request (curl, tests, same-origin GET-style fetches)
        return origin in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}")

    def do_POST(self):
        path = urlparse(self.path).path
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            return self._send(415, {"error": "Send JSON (Content-Type: application/json)."})
        if not self._same_origin():
            return self._send(403, {"error": "This server only answers its own page."})
        body = self._body()
        if not isinstance(body, dict):
            return self._send(400, {"error": "Send a JSON object under 400 KB."})
        if path == "/api/run":
            use_model = os.environ.get("USE_MODEL", "1") != "0" and body.pop("use_model", True) is not False
            try:
                return self._send(200, pipeline.run(body, use_model=use_model))
            except Exception as e:  # the screen shows this sentence
                return self._send(500, {"error": f"The run did not finish: {type(e).__name__}: {e}"})
        if path == "/api/tracker":
            tr = _tracker()
            if not tr:
                return self._send(503, {"error": "The tracker is not available."})
            if body.get("reset") is True:
                return self._send(200, tr.reset())
            key = str(body.get("student") or "current")[:120]
            demo = key in {d["label"] for d in pipeline.demo_students()}
            profile = next((d for d in pipeline.demo_students() if d["label"] == key), None) or body.get("profile") or {}
            if not isinstance(profile, dict):
                profile = {}
            res = tr.set_status(key, profile, C.find_college(str(body.get("college") or "")), str(body.get("status") or ""),
                                body.get("outcome"), demo=demo)
            return self._send(400 if res.get("error") else 200, res)
        if path == "/api/kb-check":
            return self._send(200, pipeline.kb_check(str(body.get("text", ""))[:400]))
        if path == "/api/cases":
            cl = _caselog()
            if not cl:
                return self._send(503, {"error": "The case log is not available."})
            res = cl.add_case(body)
            return self._send(400 if isinstance(res, dict) and res.get("error") else 200, res)
        return self._send(404, {"error": "No such route."})

    def _static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        base = ROOT / "docs" if path.startswith("/docs/") else ROOT / "web"
        rel = path[len("/docs/"):] if path.startswith("/docs/") else path.lstrip("/")
        target = (base / rel).resolve()
        if base.resolve() not in target.parents or not target.is_file():
            return self._send(404, {"error": "Not found."})
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        return self._send(200, target.read_bytes(), ctype)


if __name__ == "__main__":
    print(f"Counselor Copilot on http://localhost:{PORT}/   (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
