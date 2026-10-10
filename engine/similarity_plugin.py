"""The seam for a teammate's similarity tool.

The built-in matching (engine/cases.py) decides WHICH finished cases count as similar, by a fixed written rule.
A plug-in can do one of two things, chosen by the environment variable SIMILARITY_MODE:

  rank    (default) keep the built-in set and counts; let the plug-in order the examples and say why each is similar
  filter  let the plug-in decide which cases are similar (it must then describe its rule in plain words)

How to connect a tool (either one):
  SIMILARITY_PLUGIN="package.module:function"   a Python function with the signature of `rank` below
  SIMILARITY_URL="http://localhost:9000/rank"   an HTTP endpoint: we POST {"student", "college", "cases"} as JSON
                                                and expect {"ranked": [...], "rule": "..."} back within 3 seconds

Whatever happens (not set, import error, timeout, bad answer) the built-in matching is used and the reason is
recorded, so a plug-in can never break a run. Code still sets every count; a plug-in never returns odds.

A plug-in receives only de-identified fields. Cases never carry names; the student dict is the allow-listed one
from engine/pipeline.py (no essay text, activities already masked).
"""
from __future__ import annotations

import importlib
import json
import os
import urllib.request

TIMEOUT_S = 3.0


def mode() -> str:
    return "filter" if os.environ.get("SIMILARITY_MODE", "").strip().lower() == "filter" else "rank"


def configured() -> str | None:
    return os.environ.get("SIMILARITY_PLUGIN") or os.environ.get("SIMILARITY_URL") or None


def _clean(answer, known_ids):
    """Keep only well-formed items that refer to cases we actually sent. Scores are clamped to 0..1."""
    out = []
    for item in (answer or {}).get("ranked", []) if isinstance(answer, dict) else []:
        if not isinstance(item, dict) or item.get("case_id") not in known_ids:
            continue
        try:
            score = max(0.0, min(1.0, float(item.get("score", 0))))
        except (TypeError, ValueError):
            continue
        reasons = [str(r)[:120] for r in (item.get("reasons") or []) if isinstance(r, (str, int, float))][:4]
        banned = ("chance", "probab", "odds", "%")
        reasons = [r for r in reasons if not any(b in r.lower() for b in banned)]
        out.append({"case_id": item["case_id"], "score": round(score, 3), "reasons": reasons,
                    "similar": bool(item.get("similar", True))})
    rule = str((answer or {}).get("rule", ""))[:200] if isinstance(answer, dict) else ""
    return out, rule


def rank(student: dict, cases: list[dict], college: dict) -> dict:
    """Ask the plug-in. Returns {"ok", "ranked": [{"case_id", "score", "reasons", "similar"}], "rule", "why"}.

    `cases` are dicts with: case_id, sat, act, major, hooks, home_state, outcome, and for the school's own pool
    activities_note and essay_theme. The plug-in returns, for each case it wants to keep or order:
        {"case_id": "...", "score": 0.0 to 1.0 (higher = more similar), "reasons": ["same major group", ...],
         "similar": true}   ("similar" is only read in filter mode)
    plus one plain sentence "rule" describing how similarity was judged.
    """
    known = {c.get("case_id") for c in cases}
    target = os.environ.get("SIMILARITY_PLUGIN")
    url = os.environ.get("SIMILARITY_URL")
    try:
        if target:
            mod, _, fn = target.partition(":")
            answer = getattr(importlib.import_module(mod), fn or "rank")(student, cases, college)
        elif url:
            body = json.dumps({"student": student, "college": college, "cases": cases}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                answer = json.loads(r.read().decode("utf-8"))
        else:
            return {"ok": False, "ranked": [], "rule": "", "why": "no similarity plug-in is connected"}
    except Exception as e:  # never let a plug-in break a run
        return {"ok": False, "ranked": [], "rule": "", "why": f"the similarity plug-in did not answer ({type(e).__name__})"}
    ranked, rule = _clean(answer, known)
    if not ranked:
        return {"ok": False, "ranked": [], "rule": rule, "why": "the similarity plug-in returned nothing usable"}
    return {"ok": True, "ranked": ranked, "rule": rule or "ordered by the connected similarity tool", "why": ""}


def example_plugin(student: dict, cases: list[dict], college: dict) -> dict:
    """A tiny working example a teammate can copy: closer score first, same major as a reason."""
    want = student.get("sat") or 0
    ranked = []
    for c in cases:
        gap = abs((c.get("sat") or want) - want)
        reasons = [f"score within {gap} points"] + (["same major group"] if c.get("major") and c.get("major") == student.get("major_group") else [])
        ranked.append({"case_id": c["case_id"], "score": max(0.0, 1 - gap / 200), "reasons": reasons, "similar": gap <= 100})
    ranked.sort(key=lambda r: (-r["score"], str(r["case_id"])))
    return {"ranked": ranked, "rule": "closest test score first; same major group noted"}
