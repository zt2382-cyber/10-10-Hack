"""Reach / target / likely labels, set by code from published numbers.

No model is called here and nothing is a personal probability. The label compares the student's test score with
the college's published middle range (25th to 75th percentile) and looks at the college's overall admit rate.
Rules R0 to R5 are listed in RULES_TEXT. Missing or odd input never raises: it becomes "Can't say".
"""
from __future__ import annotations

try:  # the helpers live next to this file; keep the module importable on its own
    from engine.colleges import act_to_sat, find_college, load_colleges
except Exception:  # pragma: no cover
    act_to_sat = find_college = load_colleges = None  # type: ignore

REACH_FOR_EVERYONE_BELOW = 0.15
LIKELY_MIN_ADMIT_RATE = 0.40
SAT_STEP = 30
ACT_STEP = 1
RATE_STEP = 0.05

TEXTS = {
    "outside_data": "Outside our data",
    "reach_for_everyone": "Reach for everyone",
    "cant_say": "Can't say",
    "reach": "Reach",
    "target": "Target",
    "likely": "Likely",
}
NOT_USED = ["GPA", "activities", "essay"]
RANGE_CAVEAT = "The score range covers only students who sent scores."

RULES_TEXT = [
    "R0. If the college is not in our college file, we say \"Outside our data\" and do not guess.",
    "R1. If the college admits fewer than 15% of all applicants, it is \"Reach for everyone\", whatever the score.",
    "R2. If the admit rate is missing, the student has no SAT or ACT score, or the college publishes no score range "
    "we can compare with, we say \"Can't say\" and name what is missing.",
    "R3. Reach: the student's score is below the college's 25th percentile (the bottom of its middle range).",
    "R4. Target: the score is inside the middle range, or above it at a college that admits under 40% of applicants.",
    "R5. Likely: the score is at or above the college's 75th percentile and the college admits 40% or more of applicants.",
    "Which score: the SAT when the college publishes an SAT range, otherwise the ACT against its ACT range, otherwise "
    "the ACT converted to SAT with the official 2018 table.",
    "Edge test: we redo the label with the score 30 SAT points lower and higher (1 ACT point when the ACT is compared "
    "directly) and with the admit rate 5 points lower. Any change is shown, so a label that sits on a line is flagged.",
    "Published rulebooks: we also run the reach / target / likely rules of BigFuture, Princeton Review, Scoir, Appily and "
    "CollegeVine (their score-only parts) and flag any that disagree with ours.",
    "Not used: GPA, activities and the essay. The college's score range covers only students who sent scores. "
    "This is a label for the college, not a prediction for one student.",
]


# ---------------------------------------------------------------- input cleaning
def _num(x):
    if isinstance(x, bool) or x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def _clean_student_scores(student):
    """Returns (sat, act, notes). Out-of-scale scores are dropped and noted."""
    notes = []
    s = student if isinstance(student, dict) else {}
    sat = _num(s.get("sat"))
    act = _num(s.get("act"))
    if s.get("sat") not in (None, "") and (sat is None or not 400 <= sat <= 1600):
        notes.append("The SAT score entered (%s) is not on the 400 to 1600 scale, so it was not used." % s.get("sat"))
        sat = None
    if s.get("act") not in (None, "") and (act is None or not 1 <= act <= 36 or act != int(act)):
        notes.append("The ACT score entered (%s) is not a whole number from 1 to 36, so it was not used." % s.get("act"))
        act = None
    return (int(round(sat)) if sat is not None else None, int(act) if act is not None else None, notes)


def _range(college, lo_key, hi_key):
    lo, hi = _num(college.get(lo_key)), _num(college.get(hi_key))
    if lo is None or hi is None or lo > hi:
        return None
    return lo, hi


def _rate(college):
    r = _num(college.get("admit_rate"))
    if r is None or not 0 <= r <= 1:
        return None
    return round(r, 6)


def _pct(rate):
    t = "%.1f" % (rate * 100)
    if t.endswith(".0"):
        t = t[:-2]
    return t + "%"


def _i(v):
    return int(v) if float(v) == int(v) else v


def _n(v):
    return str(_i(v))


# ---------------------------------------------------------------- the core decision
def _decide(rate, score, p25, p75):
    """The R1, R3, R4, R5 part, shared by the label and the edge test. Returns (state, rule_id)."""
    if rate is not None and rate < REACH_FOR_EVERYONE_BELOW:
        return "reach_for_everyone", "R1"
    if score < p25:
        return "reach", "R3"
    if score >= p75 and rate is not None and rate >= LIKELY_MIN_ADMIT_RATE:
        return "likely", "R5"
    return "target", "R4"


# ---------------------------------------------------------------- published rulebooks (ported from D_run_rulebooks.py)
# Each takes (score, admit_rate, p25, p75) and returns "R", "T", "L" or "-" (cannot label).
def _bigfuture(s, rate, p25, p75):
    if p25 is None or s is None:
        return "-"
    return "R" if s < p25 else ("T" if s <= p75 else "L")


def _princeton_review(s, rate, p25, p75):
    if p25 is None or s is None:
        return "-"
    lower_end = p25 + 0.25 * (p75 - p25)
    return "R" if s < lower_end else ("T" if s <= p75 else "L")


def _scoir(s, rate, p25, p75):
    if p25 is None or s is None:
        return "-"
    mid = (p25 + p75) / 2
    return "R" if s < p25 else ("L" if s > mid else "T")


def _appily(s, rate, p25, p75):
    if rate is not None and rate < 0.25:
        return "R"
    if p25 is None or s is None:
        return "-"
    if s < p25:
        return "R"
    if rate is not None and s >= p75 and rate > 0.70:
        return "L"
    return "T"


def _collegevine(s, rate, p25, p75):
    if rate is not None and rate < 0.10:
        return "R"
    if p25 is None or s is None:
        return "-"
    return "R" if s < p25 else ("L" if s > p75 else "T")


PUBLISHERS = [("BigFuture", _bigfuture), ("Princeton Review", _princeton_review), ("Scoir", _scoir),
              ("Appily", _appily), ("CollegeVine", _collegevine)]
_LETTER = {"R": "reach", "T": "target", "L": "likely"}


def _publisher_labels(rate, score, p25, p75):
    out = []
    for name, fn in PUBLISHERS:
        try:
            letter = fn(score, rate, p25, p75)
        except Exception:
            letter = "-"
        if letter in _LETTER:
            out.append({"name": name, "label": _LETTER[letter]})
    return out


# ---------------------------------------------------------------- result builder
def _result(state, rule_id, rule_text, **kw):
    r = {
        "state": state, "text": TEXTS[state], "rule_id": rule_id, "rule_text": rule_text,
        "score_used": None, "score_kind": None, "inputs": {},
        "not_used": list(NOT_USED), "caveats": [], "steady": True, "flips": [],
        "publishers": [], "publishers_disagree": False,
    }
    r.update(kw)
    return r


def label_college(student, college) -> dict:
    """Label one college for one student. Never raises."""
    try:
        return _label(student, college)
    except Exception as exc:  # last-resort guard: odd input must not break the screen
        return _result("cant_say", "R2", "The label could not be set because the input was not readable (%s)." % type(exc).__name__)


def _label(student, college):
    # R0
    if not isinstance(college, dict):
        return _result("outside_data", "R0",
                       "This college is not in our college file, so we have no published numbers for it.")

    rate = _rate(college)
    sat, act, notes = _clean_student_scores(student)
    sat_rng = _range(college, "sat25", "sat75")
    act_rng = _range(college, "act25", "act75")

    # Pick the score and the range to compare (contract step 4).
    score = kind = rng = None
    step = SAT_STEP
    conv_note = None
    if sat is not None and sat_rng:
        score, kind, rng = sat, "SAT", sat_rng
    elif act is not None and act_rng:
        score, kind, rng, step = act, "ACT", act_rng, ACT_STEP
    elif act is not None and sat_rng and act_to_sat is not None and act_to_sat(act) is not None:
        score, kind, rng = act_to_sat(act), "ACT converted to SAT", sat_rng
        conv_note = "The ACT score of %d was converted to an SAT score of %d with the official 2018 table." % (act, score)
    p25, p75 = (rng if rng else (None, None))

    inputs = {}
    if rng:
        keys = ("act25", "act75") if kind == "ACT" else ("sat25", "sat75")
        inputs = {keys[0]: _i(rng[0]), keys[1]: _i(rng[1])}
    inputs["admit_rate"] = rate

    pubs = _publisher_labels(rate, score, p25, p75)

    # R1
    if rate is not None and rate < REACH_FOR_EVERYONE_BELOW:
        return _result(
            "reach_for_everyone", "R1",
            "The college admits %s of applicants, which is under 15%%, so it is a reach for every student." % _pct(rate),
            score_used=score, score_kind=kind, inputs=inputs, publishers=pubs,
            caveats=["The admit rate is the share of all applicants admitted, not a prediction for one student."] + notes,
            publishers_disagree=any(p["label"] != "reach" for p in pubs))

    # R2
    reasons = []
    if rate is None:
        reasons.append("The college's admit rate is missing from our data.")
    if sat is None and act is None:
        reasons.append(notes[0] if notes else "No SAT or ACT score was entered for this student.")
    elif rng is None:
        if sat is not None and act is None and act_rng:
            reasons.append("The student has only an SAT score and this college publishes only an ACT range, so they cannot be compared.")
        elif act is not None and sat is None and sat_rng and (act_to_sat is None or act_to_sat(act) is None):
            reasons.append("The ACT score of %d cannot be converted to SAT with the official table." % act)
        elif sat_rng is None and act_rng is None:
            reasons.append("This college publishes no usable SAT or ACT range.")
        else:
            reasons.append("This college publishes no score range that matches the student's test.")
    if reasons:
        return _result("cant_say", "R2", " ".join(reasons) + " So we cannot label it.",
                       score_used=score, score_kind=kind, inputs=inputs, publishers=pubs, caveats=list(notes))

    # R3 / R4 / R5
    state, rule_id = _decide(rate, score, p25, p75)
    if kind == "SAT":
        subject = "The score of %d" % score
    elif kind == "ACT":
        subject = "The ACT score of %d" % score
    else:
        subject = "The ACT score of %d (about %d on the SAT)" % (act, score)
    span = "%s to %s" % (_n(p25), _n(p75))
    if state == "reach":
        text = "%s is below the college's middle range, %s." % (subject, span)
    elif state == "likely":
        text = ("%s is at or above the top of the college's middle range, %s, and the college admits %s of applicants "
                "(40%% or more)." % (subject, span, _pct(rate)))
    elif score >= p75:
        text = ("%s is at or above the top of the college's middle range, %s, but the college admits only %s of "
                "applicants (under 40%%), so it is not marked likely." % (subject, span, _pct(rate)))
    else:
        text = "%s is inside the college's middle range, %s." % (subject, span)

    # Edge test (contract step 6).
    unit = "points" if step != 1 else "point"
    scenarios = [
        ("score %d %s lower" % (step, unit), rate, score - step),
        ("score %d %s higher" % (step, unit), rate, score + step),
        ("admit rate 5 points lower", None if rate is None else round(max(rate - RATE_STEP, 0.0), 6), score),
    ]
    flips = []
    for cause, r2, s2 in scenarios:
        new_state, _ = _decide(r2, s2, p25, p75)
        if new_state != state:
            flips.append({"cause": cause, "to": new_state})

    caveats = [RANGE_CAVEAT]
    if conv_note:
        caveats.append(conv_note)
    caveats += notes
    return _result(
        state, rule_id, text, score_used=score, score_kind=kind, inputs=inputs, caveats=caveats,
        steady=not flips, flips=flips, publishers=pubs,
        publishers_disagree=any(p["label"] != ("reach" if state == "reach_for_everyone" else state) for p in pubs))


# ---------------------------------------------------------------- self-check
def _demo():
    students = [
        {"label": "Student A (SYNTHETIC)", "sat": 1450, "act": None},
        {"label": "Student B (SYNTHETIC)", "sat": None, "act": 30},
        {"label": "Student C (SYNTHETIC)", "sat": 1250, "act": None},
    ]
    names = ["Cornell University", "Purdue University-Main Campus", "University of Michigan-Ann Arbor",
             "College of the Holy Cross", "University of California-Los Angeles", "Caltech"]
    short = {"Cornell University": "Cornell", "Purdue University-Main Campus": "Purdue",
             "University of Michigan-Ann Arbor": "Michigan", "College of the Holy Cross": "Holy Cross",
             "University of California-Los Angeles": "UCLA", "Caltech": "Caltech"}
    print("%-22s %-11s %-19s %-5s %-6s %-9s %s" % ("student", "college", "label", "rule", "steady", "pubs differ", "why"))
    for s in students:
        for n in names:
            c = find_college(n) if find_college else None
            r = label_college(s, c)
            print("%-22s %-11s %-19s %-5s %-6s %-11s %s" % (
                s["label"][:21], short[n], r["text"], r["rule_id"], "yes" if r["steady"] else "no",
                "yes" if r["publishers_disagree"] else "no", r["rule_text"]))
            for f in r["flips"]:
                print("%62s flips to %s if %s" % ("", f["to"], f["cause"]))
    print()
    print("How labels are set:")
    for line in RULES_TEXT:
        print(" -", line)


if __name__ == "__main__":
    _demo()
