"""Where each college on a student's plan stands, and the loop that turns a result into a finished case.

considering -> applying -> submitted -> result (admitted / denied / waitlisted)

When a result is recorded, one finished case is added to the school's own pool with only de-identified fields
(score, major group, home state, hooks). Cases made this way from the invented demo students are stored as DEMO
and can be removed again with reset(). Nothing here is a prediction, and no name is ever stored.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "local" / "tracker.json"
STATUSES = ("considering", "applying", "submitted", "result")
OUTCOMES = ("admitted", "denied", "waitlisted")


def _load() -> dict:
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=1), encoding="utf-8")


def get(student_key: str) -> dict:
    """{college_id: {"status", "outcome", "updated"}} for one student (empty when nothing is recorded)."""
    return _load().get(str(student_key), {})


def set_status(student_key: str, student: dict, college: dict, status: str, outcome: str | None = None,
               demo: bool = True) -> dict:
    """Record where one college stands. Recording a result also adds one finished case to the school's pool."""
    if status not in STATUSES:
        return {"error": "The status must be one of: " + ", ".join(STATUSES) + "."}
    if status == "result" and outcome not in OUTCOMES:
        return {"error": "A result must be admitted, denied or waitlisted."}
    if not college or not college.get("id"):
        return {"error": "That college is not in our file."}
    data = _load()
    entry = data.setdefault(str(student_key), {}).get(college["id"], {})
    already_logged = entry.get("status") == "result"
    entry = {"status": status, "outcome": outcome if status == "result" else None,
             "updated": datetime.now().astimezone().isoformat(timespec="seconds"), "case_id": entry.get("case_id")}
    out = {"saved": True, "status": status, "outcome": entry["outcome"], "case_added": None, "note": ""}
    if status == "result" and not already_logged:
        try:
            from engine import caselog
            group = None
            try:
                from engine import cases
                group = cases.major_group_for(student.get("intended_major"))
            except Exception:
                pass
            case = {"cycle_year": datetime.now().year, "sat": student.get("sat"), "act": student.get("act"),
                    "gpa": student.get("gpa"), "major_group": group or "OTHER",
                    "hooks": ",".join(h for h in (student.get("hooks") or []) if h != "none") or "none",
                    "home_state": student.get("home_state"), "college": college["name"], "outcome": outcome,
                    "activities_note": "", "essay_theme": "", "verified_by": "counselor"}
            try:
                added = caselog.add_case(case, demo=demo)   # demo cases are stored as DEMO and can be cleared
            except TypeError:
                added = caselog.add_case(case)
            if isinstance(added, dict) and added.get("error"):
                out["note"] = "The result was saved, but no case was added: " + added["error"]
            else:
                entry["case_id"] = (added or {}).get("case_id")
                out["case_added"] = {"case_id": entry["case_id"], "college": college["name"], "outcome": outcome, "demo": demo}
                out["note"] = ("One finished case was added to your school's cases. Because this is an invented demo "
                               "student, it is marked as demo data and can be removed." if demo else
                               "One finished case was added to your school's cases. No name was stored.")
        except Exception as e:
            out["note"] = f"The result was saved, but the case log could not be reached ({type(e).__name__})."
    data[str(student_key)][college["id"]] = entry
    _save(data)
    return out


def reset() -> dict:
    """Clear every recorded status, and remove the demo cases the tracker added."""
    removed = 0
    try:
        from engine import caselog
        if hasattr(caselog, "reset_demo"):
            removed = caselog.reset_demo()
    except Exception:
        pass
    _save({})
    return {"reset": True, "demo_cases_removed": removed}
