"""List balance: is the list too reach-heavy, and what else could widen it?

Everything here is computed by code from the labels and the published College Scorecard numbers.
No model call. No personal probability. Cost is sticker price only.

    assess(labelled, student) -> {"counts", "warnings", "suggestions", "cost_notes"[, "suggestions_note"]}

`labelled` is a list of {"college": College | None, "name": str, "label": label}. The function never raises
on empty or odd input.
"""
from __future__ import annotations

import re

from engine import colleges as _colleges

STATES = ("reach", "target", "likely", "cant_say", "outside_data")
NO_SCORE_NOTE = "No suggestions without a test score: there is nothing to compare."
MAX_PER_BUCKET = 3
MIN_ADMIT_RATE_FOR_SUGGESTION = 0.15
RECALC_NOTE = "What this family would actually pay is not known here."


# ---------------------------------------------------------------- small helpers

def _norm(name) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()


def _num(x):
    if isinstance(x, bool) or x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _money(v) -> str:
    return "${:,}".format(int(round(v / 100.0)) * 100)


def _state_of(entry) -> str:
    label = entry.get("label") if isinstance(entry, dict) else None
    state = label.get("state") if isinstance(label, dict) else None
    if state in ("reach", "reach_for_everyone"):
        return "reach"
    if state in ("target", "likely", "cant_say", "outside_data"):
        return state
    return "cant_say"  # missing or unknown label: the safe reading is "could not label"


def _clean_list(labelled) -> list:
    if not isinstance(labelled, (list, tuple)):
        return []
    return [e for e in labelled if isinstance(e, dict)]


def _college_of(entry):
    c = entry.get("college")
    return c if isinstance(c, dict) else None


def _entry_name(entry) -> str:
    name = entry.get("name")
    if name:
        return str(name)
    c = _college_of(entry)
    return str(c.get("name")) if c and c.get("name") else "(unnamed college)"


def _entry_admit_rate(entry):
    c = _college_of(entry)
    rate = _num(c.get("admit_rate")) if c else None
    if rate is None:
        label = entry.get("label")
        if isinstance(label, dict) and isinstance(label.get("inputs"), dict):
            rate = _num(label["inputs"].get("admit_rate"))
    return rate


def _student_scores(student) -> tuple:
    s = student if isinstance(student, dict) else {}
    return _num(s.get("sat")), _num(s.get("act"))


def _home_state(student) -> str:
    s = student if isinstance(student, dict) else {}
    return str(s.get("home_state") or "").strip().upper()


# ---------------------------------------------------------------- labelling for suggestions

def _inline_label(student: dict, college: dict) -> dict:
    """Private copy of contract rules R1 to R5 (no edge test, no publishers). Used only if engine.labels is absent."""
    rate = _num(college.get("admit_rate"))
    sat, act = _student_scores(student)
    if rate is not None and rate < 0.15:
        return {"state": "reach_for_everyone", "rule_id": "R1"}
    if rate is None or (sat is None and act is None):
        return {"state": "cant_say", "rule_id": "R2"}
    s25, s75 = _num(college.get("sat25")), _num(college.get("sat75"))
    a25, a75 = _num(college.get("act25")), _num(college.get("act75"))
    if sat is not None and s25 is not None and s75 is not None:
        score, kind, lo, hi = sat, "SAT", s25, s75
    elif act is not None and a25 is not None and a75 is not None:
        score, kind, lo, hi = act, "ACT", a25, a75
    elif act is not None and s25 is not None and s75 is not None:
        conv = _colleges.act_to_sat(int(act))
        if conv is None:
            return {"state": "cant_say", "rule_id": "R2"}
        score, kind, lo, hi = conv, "ACT converted to SAT", s25, s75
    else:
        return {"state": "cant_say", "rule_id": "R2"}
    if score < lo:
        state, rule = "reach", "R3"
    elif score >= hi and rate >= 0.40:
        state, rule = "likely", "R5"
    else:
        state, rule = "target", "R4"
    return {"state": state, "rule_id": rule, "score_used": score, "score_kind": kind}


def _get_labeller():
    """engine.labels.label_college if it imports, else the inline copy. Imported lazily, once per assess call."""
    try:
        from engine.labels import label_college  # type: ignore
    except Exception:
        return _inline_label

    def safe(student, college):
        try:
            out = label_college(student, college)
            if isinstance(out, dict) and out.get("state"):
                return out
        except Exception:
            pass
        return _inline_label(student, college)

    return safe


def _has_score_range(c: dict) -> bool:
    return (_num(c.get("sat25")) is not None and _num(c.get("sat75")) is not None) or (
        _num(c.get("act25")) is not None and _num(c.get("act75")) is not None)


# ---------------------------------------------------------------- text builders

def _tuition_note(college: dict, home: str) -> str:
    if college.get("control") == "public":
        if not home:
            return "Public: in-state and out-of-state tuition differ, and the home state is not known"
        if str(college.get("state") or "").upper() == home:
            return "In-state tuition applies"
        return "Out-of-state tuition applies"
    return "Private: one tuition for all"


def _why(would_be: str, label: dict, college: dict, student: dict) -> str:
    kind = str(label.get("score_kind") or "")
    score = label.get("score_used")
    if score is None:
        sat, act = _student_scores(student)
        score, kind = (sat, "SAT") if sat is not None else (act, "ACT")
    if kind == "ACT":
        lo, hi, shown = college.get("act25"), college.get("act75"), "ACT"
    else:
        lo, hi, shown = college.get("sat25"), college.get("sat75"), "SAT"
    if kind.startswith("ACT converted"):
        score_txt = "The student's ACT, converted to about {} on the SAT scale,".format(int(round(score)))
    else:
        score_txt = "The student's {} of {}".format(kind or shown, int(round(score)))
    pct = int(round(float(college["admit_rate"]) * 100))
    admit_txt = "the college admits about {}% of applicants".format(pct)
    if would_be == "likely":
        return "{} is at or above the college's 75th percentile ({}), and {}.".format(score_txt, int(hi), admit_txt)
    return "{} is inside the college's middle range ({} to {}), and {}.".format(
        score_txt, int(lo), int(hi), admit_txt)


def _rank_key(c: dict, home: str):
    in_state = bool(home) and str(c.get("state") or "").upper() == home
    if in_state and c.get("control") == "public":
        tier = 0
    elif in_state:
        tier = 1
    else:
        tier = 2
    grad = _num(c.get("grad_rate"))
    size = _num(c.get("undergrads"))
    return (tier,
            0 if grad is not None else 1, -(grad if grad is not None else 0.0),
            0 if size is not None else 1, -(size if size is not None else 0.0),
            str(c.get("name") or ""))


def _suggest(entries: list, student: dict) -> list:
    sat, act = _student_scores(student)
    if sat is None and act is None:
        return []
    home = _home_state(student)
    listed_ids, listed_names = set(), set()
    for e in entries:
        c = _college_of(e)
        if c:
            listed_ids.add(str(c.get("id")))
            listed_names.add(_norm(c.get("name")))
        listed_names.add(_norm(e.get("name")))
        found = _colleges.find_college(e.get("name")) if e.get("name") else None
        if found:
            listed_ids.add(str(found["id"]))
    label_fn = _get_labeller()
    pools = {"likely": [], "target": []}
    for c in _colleges.load_colleges():
        rate = _num(c.get("admit_rate"))
        if rate is None or rate < MIN_ADMIT_RATE_FOR_SUGGESTION or not _has_score_range(c):
            continue
        if str(c["id"]) in listed_ids or _norm(c["name"]) in listed_names:
            continue
        label = label_fn(student, c)
        if label.get("state") in pools:
            pools[label["state"]].append((c, label))
    out = []
    for would_be in ("likely", "target"):
        ranked = sorted(pools[would_be], key=lambda p: _rank_key(p[0], home))[:MAX_PER_BUCKET]
        for c, label in ranked:
            out.append({
                "id": c["id"], "name": c["name"], "would_be": would_be,
                "admit_rate": c["admit_rate"], "sat25": c["sat25"], "sat75": c["sat75"],
                "cost_year": c["cost_year"], "tuition_note": _tuition_note(c, home),
                "why": _why(would_be, label, c, student),
            })
    return out


def _cost_notes(entries: list, student: dict) -> list:
    home = _home_state(student)
    notes, seen = [], set()
    for e in entries:
        c = _college_of(e)
        if not c:
            continue
        key = str(c.get("id") or _norm(c.get("name")))
        if key in seen:
            continue
        seen.add(key)
        cost = _num(c.get("cost_year"))
        t_in, t_out = _num(c.get("tuition_in")), _num(c.get("tuition_out"))
        if c.get("control") == "public":
            if home and str(c.get("state") or "").upper() == home:
                tuition, which = t_in, "the in-state rate"
            elif home:
                tuition, which = t_out, "the out-of-state rate"
            else:
                tuition, which = None, ""
        else:
            tuition, which = (t_in if t_in is not None else t_out), "the same for every student"
        parts = []
        if tuition is not None:
            parts.append("Tuition and fees are about {} a year ({})".format(_money(tuition), which))
        elif c.get("control") == "public" and not home and (t_in is not None or t_out is not None):
            parts.append("Tuition and fees are about {} a year in-state and {} out-of-state".format(
                _money(t_in) if t_in is not None else "not published",
                _money(t_out) if t_out is not None else "not published"))
        if cost is not None:
            parts.append("the full sticker cost of attendance is about {} a year".format(_money(cost)))
        if not parts:
            continue
        text = ", and ".join(parts) if len(parts) == 2 else parts[0]
        if len(parts) == 1 and parts[0].startswith("the full"):
            text = "The full sticker cost of attendance is about {} a year".format(_money(cost))
        notes.append({"name": _entry_name(e), "text": "{}. {}".format(text, RECALC_NOTE)})
    return notes


def _warnings(entries: list, counts: dict) -> list:
    labellable = counts["reach"] + counts["target"] + counts["likely"]
    warns = []
    if labellable and counts["reach"] * 2 > labellable:
        r = counts["reach"]
        warns.append({"id": "reach_heavy", "text": "{} of the {} labelled {} {} {}.".format(
            r, labellable, _plural(labellable, "college", "colleges"),
            _plural(r, "is", "are"), _plural(r, "a reach", "reaches"))})
    if labellable and counts["likely"] == 0:
        warns.append({"id": "no_likely", "text": "There is no likely college on this list."})
    if labellable and counts["target"] == 0:
        warns.append({"id": "no_target", "text": "There is no target college on this list."})
    selective = sum(1 for e in entries if (_entry_admit_rate(e) is not None and _entry_admit_rate(e) < 0.15))
    if selective >= 4:
        warns.append({"id": "prestige_pile", "text": (
            "{} colleges on this list admit fewer than 15 in 100 applicants. "
            "Colleges that selective are a reach for any student.").format(selective)})
    if labellable < 5:
        warns.append({"id": "short_list", "text": "Only {} {} on this list could be labelled.".format(
            labellable, _plural(labellable, "college", "colleges"))})
    if entries and labellable == 0 and counts["cant_say"] >= 1:
        warns.append({"id": "all_cant_say", "text": (
            "None of the {} {} on this list could be labelled with the numbers given.").format(
            len(entries), _plural(len(entries), "college", "colleges"))})
    return warns


# ---------------------------------------------------------------- public API

def assess(labelled: list, student: dict) -> dict:
    """Balance of the list: counts, warnings, suggested fills and sticker-cost notes. Never raises."""
    try:
        entries = _clean_list(labelled)
        student = student if isinstance(student, dict) else {}
        counts = {k: 0 for k in STATES}
        for e in entries:
            counts[_state_of(e)] += 1
        result = {
            "counts": counts,
            "warnings": _warnings(entries, counts),
            "suggestions": _suggest(entries, student),
            "cost_notes": _cost_notes(entries, student),
        }
        sat, act = _student_scores(student)
        if sat is None and act is None:
            result["suggestions_note"] = NO_SCORE_NOTE
        return result
    except Exception as exc:  # last resort: a normal, empty answer, not a crash
        return {"counts": {k: 0 for k in STATES}, "warnings": [], "suggestions": [], "cost_notes": [],
                "error": "Balance could not be computed: {}".format(type(exc).__name__)}


# ---------------------------------------------------------------- self-check

def _demo() -> None:
    student = {"label": "Demo (SYNTHETIC)", "sat": 1450, "act": None, "home_state": "NJ"}
    names = ["Harvard University", "Yale University", "Princeton University",
             "Massachusetts Institute of Technology", "Stanford University", "Cornell University"]
    label_fn = _get_labeller()
    labelled = []
    for n in names:
        c = _colleges.find_college(n)
        labelled.append({"college": c, "name": n, "label": label_fn(student, c) if c else {"state": "outside_data"}})
    out = assess(labelled, student)
    print("Student: 1450 SAT, home state NJ. List:", ", ".join(names))
    print("\nCounts:", out["counts"])
    print("\nWarnings:")
    for w in out["warnings"]:
        print("  [{}] {}".format(w["id"], w["text"]))
    print("\nSuggestions:")
    for s in out["suggestions"]:
        print("  {} -> {} ({}; admit {:.0%}; SAT {}-{}; sticker {})".format(
            s["would_be"].upper(), s["name"], s["tuition_note"], s["admit_rate"], s["sat25"], s["sat75"],
            s["cost_year"]))
        print("      " + s["why"])
    print("\nCost notes:")
    for c in out["cost_notes"]:
        print("  {}: {}".format(c["name"], c["text"]))


if __name__ == "__main__":
    _demo()
