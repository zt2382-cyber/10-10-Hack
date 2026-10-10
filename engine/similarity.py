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
