"""Connects the applicant-evidence package (`admissions/`, built by a teammate) to the case search.

That package scores how alike two applicant profiles are with explicit weights (grades, submitted SAT, rigor,
activities, interests), reports how much of the profile could actually be compared ("coverage"), and never
estimates a chance of admission. Here its `similarity` function orders the finished cases shown as examples and
says in plain words why each one is alike.

It is the default similarity tool (see server.py). It plugs in through engine/similarity_plugin.py, so if it is
missing or fails, the built-in ordering is used and the result says why.
"""
from __future__ import annotations

WORDS = {"gpa": "grades", "sat_submitted": "test score", "rigor": "course rigor", "activities": "activities", "interests": "interests"}


def _tags(*values) -> list | None:
    out = []
    for v in values:
        if isinstance(v, (list, tuple, set, frozenset)):
            out += [str(x).strip() for x in v if str(x).strip()]
        elif v not in (None, "", "none", "NONE", "-1"):
            out.append(str(v).strip())
    return out or None


def _profile_from_student(student: dict) -> dict:
    gpa = student.get("gpa")
    return {
        "gpa": {"value": float(gpa), "scale": float(student.get("gpa_scale") or 4.0), "weighted": False} if isinstance(gpa, (int, float)) else None,
        "sat_submitted": student.get("sat") if isinstance(student.get("sat"), int) else None,
        "rigor": None,
        "activities": _tags([a.get("type") for a in (student.get("activities") or []) if isinstance(a, dict)]),
        "interests": _tags(student.get("major_group"), student.get("major_interests")),
    }


def _profile_from_case(case: dict) -> dict:
    gpa = case.get("gpa")
    try:
        gpa = float(gpa) if gpa not in (None, "") else None
    except (TypeError, ValueError):
        gpa = None
    sat = case.get("sat")
    return {
        "gpa": {"value": gpa, "scale": 4.0, "weighted": False} if gpa is not None and 0 <= gpa <= 4.0 else None,
        "sat_submitted": int(sat) if isinstance(sat, (int, float)) and 400 <= sat <= 1600 else None,
        "rigor": None,
        "activities": _tags(case.get("activities_tags"), case.get("activities_note")),
        "interests": _tags(case.get("major"), case.get("major_group")),
    }


def rank(student: dict, cases: list[dict], college: dict) -> dict:
    """The plug-in entry point: see engine/similarity_plugin.py for the shape."""
    from admissions.core import similarity  # the teammate's scoring function

    query = _profile_from_student(student)
    ranked = []
    for c in cases:
        res = similarity(query, _profile_from_case(c))
        comps = res.get("components") or {}
        alike = [WORDS.get(k, k) for k, v in sorted(comps.items(), key=lambda kv: -kv[1]["similarity"]) if v["similarity"] >= 0.8]
        apart = [WORDS.get(k, k) for k, v in comps.items() if v["similarity"] < 0.5]
        reasons = ([("alike on " + ", ".join(alike))] if alike else []) + ([("differs on " + ", ".join(apart))] if apart else [])
        if res.get("coverage", 0) < 0.5:
            reasons.append("only part of the profile could be compared")
        # Ranking multiplies similarity by coverage, as the package does, so a sparse match cannot rank first.
        ranked.append({"case_id": c.get("case_id"), "score": round(res.get("score", 0) * res.get("coverage", 0), 4),
                       "reasons": reasons, "similar": res.get("score", 0) >= 0.6})
    ranked.sort(key=lambda r: (-r["score"], str(r["case_id"])))
    return {"ranked": ranked,
            "rule": "Ordered by the applicant-evidence scorer: grades 35%, test score 25%, rigor 20%, activities 15%, interests 5%, scaled by how much could be compared."}
