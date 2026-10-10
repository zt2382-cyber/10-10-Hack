"""Closeness: does this student look more like the people admitted at a college, or the people denied?

A distance, never a probability. Each part (score, activities rating, major group, hooks, residency, GPA) is 0
(same) to 1 (far); the total is a weighted mean over the parts both sides have. Per college and per pool the
student is compared with the nearest admitted and the nearest denied cases; the gap between those two means
sets the lean. The two pools (national self-reported, own school) are never merged.

Everything here is counting and sorting in code. No model is called. Hooks, race, gender and income are matched
on where the data has them, never suggested as things to change.

    python -m engine.similarity            prints the block for one demo student at one college
    python -m engine.similarity --check    the holds-up table (R5), written to docs/closeness_check.json
"""
from __future__ import annotations

from engine import cases as _cases
from engine import colleges as _colleges

NEIGHBOURS = 7
NEEDED = _cases.NEEDED
LEAN_GAP = 0.03
CAVEAT = "Closeness compares this student with people who chose to post their results. It is not a forecast."
NATIONAL_SOURCE = _cases.NATIONAL_SOURCE
OWN_SOURCE = _cases.OWN_SOURCE

# R1. Starting values, not tuned. Only the parts both sides have are used, and the weights renormalise over them.
WEIGHTS = {"score": 0.45, "activities": 0.20, "major": 0.15, "hooks": 0.10, "residency": 0.10, "gpa": 0.20}
SCORE_SPAN = 400      # SAT points that count as "far" (distance 1)
RATING_SPAN = 10.0    # activities rating is 0 to 10
GPA_SPAN = 1.0        # GPA points that count as "far", on a 4.0 scale
PART_WORD = {"score": "score", "activities": "activities rating", "major": "major group", "hooks": "hook status",
             "residency": "residency", "gpa": "GPA"}


# ---------------------------------------------------------------- the two sides of a comparison

def _rating(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if 0 <= v <= 10 else None


def _gpa(v, scale=None):
    """GPA on a 4.0 scale, or None. A scale other than 4.0 is converted; a value past the scale is dropped."""
    try:
        g = float(v)
        s = float(scale) if scale not in (None, "") else 4.0
    except (TypeError, ValueError):
        return None
    if s <= 0 or g < 0 or g > s + 1e-9:
        return None
    return g * 4.0 / s


def _student_view(student, college, tags=None) -> dict:
    """The student's side, built once: the same score, group and hook rules as cases.find_similar."""
    student, tags = student or {}, tags or {}
    sat, act = _cases._valid_sat(student.get("sat")), _cases._valid_act(student.get("act"))
    score, converted = _cases._score(sat, act)
    group = _cases.major_group_for(student.get("intended_major"))
    if group is None and tags.get("major_group") in _cases.MAJOR_GROUPS and tags.get("major_group_agreed", True):
        group = tags["major_group"]
    interests = []
    for m in (student.get("major_interests") or []):
        g = _cases.major_group_for(m)
        if g and g not in interests:
            interests.append(g)
    if not interests and group:
        interests = [group]
    home = str(student.get("home_state") or "").strip().upper() or None
    return {"score": score, "converted": converted, "activities": _rating(student.get("activities_rating")),
            "major_group": group, "major_interests": interests,
            "hooks": frozenset(_cases._hooks_from_student(student.get("hooks"))),
            "home_state": home, "gpa": _gpa(student.get("gpa"), student.get("gpa_scale"))}


def _case_view(row, gpa=None) -> dict:
    """One past case in the same shape as the student view. `row` is a cases._national or _own_rows dict."""
    return {"case_id": row["case_id"], "num": row.get("num", 0), "score": row.get("score"),
            "activities": _rating(row.get("rating")), "major_group": row.get("group"),
            "hooks": frozenset(row.get("hooks_set") or {"NONE"}),
            "home_state": (row.get("home_state") or None), "gpa": gpa, "outcome": row.get("outcome"), "row": row}


def _in_state(home, college):
    return home is not None and college.get("state") is not None and home == str(college["state"]).upper()


def part_distances(a: dict, b: dict, college: dict) -> dict:
    """Per-part distance 0 (same) to 1 (far) for every part both sides have. Missing parts are left out."""
    d = {}
    if a["score"] is not None and b["score"] is not None:
        d["score"] = min(abs(a["score"] - b["score"]) / SCORE_SPAN, 1.0)
    if a["activities"] is not None and b["activities"] is not None:
        d["activities"] = min(abs(a["activities"] - b["activities"]) / RATING_SPAN, 1.0)
    if a["major_group"] is not None and b["major_group"] is not None:
        d["major"] = 0.0 if a["major_group"] == b["major_group"] else 1.0
    d["hooks"] = 0.0 if a["hooks"] == b["hooks"] else 1.0
    if (college or {}).get("control") == "public" and a["home_state"] is not None and b["home_state"] is not None:
        d["residency"] = 0.0 if _in_state(a["home_state"], college) == _in_state(b["home_state"], college) else 1.0
    if a.get("gpa") is not None and b.get("gpa") is not None:
        d["gpa"] = min(abs(a["gpa"] - b["gpa"]) / GPA_SPAN, 1.0)
    return d


def total(parts: dict) -> float | None:
    """Weighted mean of the parts present. Score is required; without it there is no distance."""
    if not parts or "score" not in parts:
        return None
    w = sum(WEIGHTS[p] for p in parts)
    return sum(WEIGHTS[p] * v for p, v in parts.items()) / w


def closeness(student, college, tags=None) -> dict:
    """The contract block for one college. Stage 1 stub: a fixed example in the contract shape."""
    if college is None or _colleges.case_name_for(college) is None:
        return {"needed": NEEDED, "neighbours": NEIGHBOURS,
                "national": {"source": NATIONAL_SOURCE, "verified": False, "status": "none",
                             "n_admitted": 0, "n_denied": 0, "n_waitlisted": 0},
                "own": {"source": OWN_SOURCE, "verified": True, "status": "none",
                        "n_admitted": 0, "n_denied": 0, "n_waitlisted": 0},
                "caveat": CAVEAT}
    return {
        "needed": NEEDED, "neighbours": NEIGHBOURS,
        "national": {
            "source": NATIONAL_SOURCE, "verified": False, "status": "ok",
            "n_admitted": 212, "n_denied": 480, "n_waitlisted": 61,
            "d_admitted": 0.18, "d_denied": 0.24, "gap": 0.06, "lean": "closer_to_admitted",
            "text": "Looks more like the people admitted here than the people denied.",
            "steady": False, "flips": [{"cause": "score 30 points lower", "to": "in_between"}],
            "parts": [{"part": "score", "distance": 0.05, "text": "close"},
                      {"part": "activities", "distance": 0.4, "text": "far"}],
            "not_used": ["GPA", "essay", "activity descriptions"],
            "nearest_admitted": [], "nearest_denied": [],
            "kinds": [{"kind_id": "K1", "name": "High score, CS, activities 7", "size": 88, "median_sat": 1540,
                       "median_activities": 7, "top_major": "CS", "medoid_case_id": "N-1042", "distance": 0.12,
                       "nearest": True}],
            "changes": [{"change": "Score 60 points higher", "gap_before": 0.06, "gap_after": 0.11,
                         "lean_after": "closer_to_admitted", "because": ["N-88", "N-1042"]}],
            "points": [{"case_id": "N-1042", "sat": 1460, "activities": 6.5, "outcome": "admitted", "kind_id": "K1"}],
        },
        "own": {"source": OWN_SOURCE, "verified": True, "status": "not_enough", "n_admitted": 1, "n_denied": 3},
        "caveat": CAVEAT,
    }


if __name__ == "__main__":
    import json
    import sys

    from engine import pipeline
    st = pipeline.demo_students()[0]
    col = _colleges.find_college(st["college_list"][0])
    print(json.dumps(closeness(st, col), indent=2, ensure_ascii=False))
    if "--check" in sys.argv:
        print("--check is not built yet.")
