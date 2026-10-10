"""Adapter for the parsed r/collegeresults pool (data/cases/parsed/). NOT wired in: nothing imports this by default.

  load()              -> (applicants, decisions): the two parsed CSVs as lists of plain dicts, numbers converted.
  as_national_rows()  -> {college key: [case, ...]}: the same structure engine.cases._national()[0] builds for the
                         2,247-applicant national pool, plus two extra fields per case, `activities_tags` and
                         `essay_themes` (lists of strings).

The college key is the case-file short name (e.g. "UPENN") when the college has one, otherwise the Scorecard college
name. engine.cases looks cases up by short name only, so wiring this in for colleges outside today's 58 would need a
lookup by Scorecard name there (not done here: engine/cases.py, engine/pipeline.py and web/ are untouched).

Everything here is self-described in a public Reddit post; not verified. Activities and essay fields are the applicant's
own short description, never essay text.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from engine import cases as _cases
from engine import colleges as _colleges

PARSED_DIR = Path(__file__).resolve().parent.parent / "data" / "cases" / "parsed"
SOURCE_NOTE = "self-described in a public Reddit post; not verified"


def _rows(path: Path) -> list:
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    return list(csv.DictReader(lines))


def _num(v, cast=float):
    if v in ("", None):
        return None
    try:
        return cast(v)
    except ValueError:
        return None


def load(directory=None):
    """(applicants, decisions) as lists of dicts. Empty cells become None; numeric cells become numbers."""
    d = Path(directory) if directory else PARSED_DIR
    applicants = []
    for r in _rows(d / "applicants.csv"):
        a = dict(r)
        for k in ("post_year", "application_year", "sat_total", "act_composite", "ap_ib_count", "n_decisions",
                  "n_mapped_decisions"):
            a[k] = _num(r[k], int)
        for k in ("gpa_unweighted", "gpa_weighted", "gpa_unlabeled", "gpa_scale", "class_rank_top_pct", "essay_self_rating"):
            a[k] = _num(r[k])
        for k in ("activities_tags", "essay_themes", "hooks"):
            a[k] = [x for x in r[k].split(";") if x]
        for k in ("major_text", "major_group", "home_state", "school_type", "activities_summary", "essay_topic",
                  "class_rank_raw"):
            a[k] = r[k] or None
        applicants.append(a)
    decisions = [dict(r) for r in _rows(d / "decisions.csv")]
    return applicants, decisions


def as_national_rows(directory=None):
    """{college key: [case dict, ...]} in the shape of engine.cases._national()[0], with activities_tags and essay_themes."""
    applicants, decisions = load(directory)
    by_id = {a["record_id"]: a for a in applicants}
    cases_by_rec = {}
    for i, a in enumerate(sorted(applicants, key=lambda x: x["record_id"])):
        sat = _cases._valid_sat(a["sat_total"]) if a["sat_total"] is not None else None
        act = _cases._valid_act(a["act_composite"]) if a["act_composite"] is not None else None
        score, _conv = _cases._score(sat, act)
        shown_act = act
        if act is not None and sat is not None:
            conv = _colleges.act_to_sat(act)
            if conv is None or abs(conv - sat) > 250:
                shown_act = None
        vocab = [h for h in a["hooks"] if h in ("FIRST-GEN", "LEGACY", "ATHLETE")]
        major = a["major_text"]
        cases_by_rec[a["record_id"]] = {
            "case_id": "P-" + a["record_id"][2:], "num": i, "sat": sat, "act": shown_act, "score": score,
            "major": major, "group": _cases._case_major_group(major),
            "hooks_set": _cases._hooks_from_case(";".join(vocab)), "hooks": ";".join(vocab) or "NONE",
            "home_state": a["home_state"], "rating": None,
            "activities_tags": list(a["activities_tags"]), "essay_themes": list(a["essay_themes"]),
        }
    pairs = {}
    for d in decisions:
        if d["record_id"] not in by_id or not d["college_id"]:
            continue
        outcome = _cases._OUTCOME_WORD.get(d["outcome"].strip().lower())
        if outcome is None:
            continue
        key = d["case_name"] or d["college_name"]
        pairs.setdefault((key, d["record_id"]), set()).add(outcome)
    by_college = {}
    for (college, rid), outs in pairs.items():  # same collapse as engine.cases: admitted beats denied beats waitlisted
        final = "admitted" if "admitted" in outs else "denied" if "denied" in outs else "waitlisted"
        c = dict(cases_by_rec[rid])
        c["outcome"] = final
        by_college.setdefault(college, []).append(c)
    for rows in by_college.values():
        rows.sort(key=lambda c: c["num"])
    return by_college
