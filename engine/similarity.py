"""Closeness: does this student look more like the people admitted at a college, or the people denied?

A distance, never a probability. Each part (score, activities rating, major group, hooks, residency, GPA) is 0
(same) to 1 (far); the total is a weighted mean over the parts both sides have. Per college and per pool the
student is compared with the nearest admitted and the nearest denied cases; the gap between those two means
sets the lean. The two pools (national self-reported, own school) are never merged.

Everything here is counting and sorting in code. No model is called. Hooks, race, gender and income are matched
on where the data has them, never suggested as things to change.

    python -m engine.similarity            prints the block for one demo student at one college
    python -m engine.similarity --spread   the gap for every demo student at every listed college (to set LEAN_GAP)
    python -m engine.similarity --check    the holds-up table (R5), written to docs/closeness_check.json
"""
from __future__ import annotations

from functools import lru_cache

from engine import cases as _cases
from engine import colleges as _colleges

NEIGHBOURS = 7
NEEDED = _cases.NEEDED
# Checked with `--spread` on the six demo students (no activities rating given, so score carries most of the
# weight): of 20 colleges with status ok, 11 leaned denied, 3 admitted, 6 in between, and the direction matched
# the list (a 1450 leans denied at MIT and Stanford, a converted 29 ACT leans admitted at Purdue). Kept at 0.03.
LEAN_GAP = 0.03
POINTS_CAP = 300
MAX_NEAREST = 3
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
NEVER_USED = ["essay", "activity descriptions"]   # text is never part of a distance

LEAN_TEXT = {
    "closer_to_admitted": "Looks more like the people admitted here than the people denied.",
    "closer_to_denied": "Looks more like the people denied here than the people admitted.",
    "in_between": "About as close to the people admitted as to the people denied.",
}
STATUS_TEXT = {
    "not_enough": "Not enough finished cases in one of the two groups to say which the student is closer to.",
    "none": "No finished cases for this college in this pool.",
    "cant_say": "No test score, so there is nothing to measure distance from.",
}
CLOSE, FAR = 0.15, 0.5   # per-part words: at or under CLOSE is "close", at or over FAR is "far"

# the steady test: recompute with other neighbour counts and a slightly different score
STEADY_K = (5, 10)
STEADY_SCORE = (-30, 30)


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


# ---------------------------------------------------------------- R2. the two groups at one college

def _split(views):
    """(admitted, denied, waitlisted), scored cases only, each sorted by case number."""
    scored = sorted((v for v in views if v["score"] is not None), key=lambda v: v["num"])
    return ([v for v in scored if v["outcome"] == "admitted"],
            [v for v in scored if v["outcome"] == "denied"],
            [v for v in scored if v["outcome"] == "waitlisted"])


@lru_cache(maxsize=None)
def _national_groups(case_name):
    return _split(_case_view(r) for r in _cases._national()[0].get(case_name, []))


def _own_groups(college):
    """Not cached: the school's store can change while the server runs. GPA is joined in from the store."""
    rows = _cases._own_rows(college)
    gpa = {}
    if rows:
        try:
            from engine import caselog
            gpa = {r["case_id"]: r.get("gpa") for r in caselog.load_cases()}
        except Exception:
            gpa = {}
    return _split(_case_view(r, gpa.get(r["case_id"])) for r in rows)


def _nearest(sv, group, k, college, exclude=None):
    """The k nearest cases: [(distance, case_view, parts)], nearest first, ties by case number."""
    scored = []
    for cv in group:
        if exclude is not None and cv["case_id"] == exclude:
            continue
        parts = part_distances(sv, cv, college)
        d = total(parts)
        if d is not None:
            scored.append((d, cv["num"], cv, parts))
    scored.sort(key=lambda t: (t[0], t[1]))
    return [(d, cv, parts) for d, _, cv, parts in scored[:k]]


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def _gap(sv, groups, college, k=NEIGHBOURS, exclude=None):
    """(d_admitted, d_denied, gap, nearest_admitted, nearest_denied). Lean, steady and changes all go through here."""
    adm, den, _ = groups
    na, nd = _nearest(sv, adm, k, college, exclude), _nearest(sv, den, k, college, exclude)
    da, dd = _mean(t[0] for t in na), _mean(t[0] for t in nd)
    gap = None if (da is None or dd is None) else dd - da
    return da, dd, gap, na, nd


def _lean(gap):
    if gap is None:
        return None
    if gap >= LEAN_GAP:
        return "closer_to_admitted"
    if gap <= -LEAN_GAP:
        return "closer_to_denied"
    return "in_between"


def _shifted(sv, points):
    return dict(sv, score=max(400, min(1600, sv["score"] + points)))


def _steady(sv, groups, college, base_lean):
    """Same idea as the label edge test: other neighbour counts, score a little lower and higher."""
    flips = []
    for k in STEADY_K:
        to = _lean(_gap(sv, groups, college, k)[2])
        if to != base_lean:
            flips.append({"cause": f"{k} nearest instead of {NEIGHBOURS}", "to": to})
    for pts in STEADY_SCORE:
        to = _lean(_gap(_shifted(sv, pts), groups, college)[2])
        if to != base_lean:
            flips.append({"cause": f"score {abs(pts)} points {'lower' if pts < 0 else 'higher'}", "to": to})
    return not flips, flips


def _part_word(d):
    return "close" if d <= CLOSE else ("far" if d >= FAR else "some way off")


def _parts_summary(near):
    """Mean distance per part over the nearest cases, so the screen can say 'close on score, far on activities'."""
    out = []
    for p in WEIGHTS:
        vals = [parts[p] for _, _, parts in near if p in parts]
        if vals:
            m = _mean(vals)
            out.append({"part": p, "distance": round(m, 3), "text": _part_word(m)})
    return out


def _not_used(near_a, near_d, college):
    used = {p for _, _, parts in near_a + near_d for p in parts}
    private = (college or {}).get("control") != "public"
    out = [PART_WORD[p] for p in WEIGHTS if p not in used and not (p == "residency" and private)]
    if private:
        out.append("residency (private college)")
    return out + NEVER_USED


def _example(d, cv, parts, own):
    ex = _cases._example(cv["row"], own)
    ex["distance"] = round(d, 3)
    ex["parts"] = {p: round(v, 3) for p, v in parts.items()}
    return ex


def _points(groups, kind_of=None):
    """Up to POINTS_CAP scored cases for the scatter, spread evenly through the file order when there are more."""
    adm, den, wl = groups
    allv = sorted(adm + den + wl, key=lambda v: v["num"])
    n = len(allv)
    if n > POINTS_CAP:
        allv = [allv[round(i * (n - 1) / (POINTS_CAP - 1))] for i in range(POINTS_CAP)]
    return [{"case_id": v["case_id"], "sat": v["score"], "activities": v["activities"], "outcome": v["outcome"],
             "kind_id": (kind_of or {}).get(v["case_id"])} for v in allv]


# ---------------------------------------------------------------- R3. kinds of admitted student (k-medoids)

KINDS = 3
KINDS_MIN = 30          # fewer admitted cases than this: no kinds
KINDS_CAP = 300         # more than this: a seeded sample
KINDS_ROUNDS = 20
KINDS_SEED = 20261010
KIND_PARTS = ("score", "activities", "major")
KIND_SCORE_BAND = 40    # medoid median this far above / below the college's admitted median: "High" / "Lower"
KIND_RATING_BAND = 1.0


def _kind_distance(a, b):
    """Distance between two admitted cases over score, activities and major only; same spans and weights as R1."""
    w = WEIGHTS["score"]
    d = w * min(abs(a["score"] - b["score"]) / SCORE_SPAN, 1.0)
    if a["activities"] is not None and b["activities"] is not None:
        d += WEIGHTS["activities"] * min(abs(a["activities"] - b["activities"]) / RATING_SPAN, 1.0)
        w += WEIGHTS["activities"]
    if a["major_group"] is not None and b["major_group"] is not None:
        d += WEIGHTS["major"] * (0.0 if a["major_group"] == b["major_group"] else 1.0)
        w += WEIGHTS["major"]
    return d / w


def _score_word(value, centre, band):
    if value >= centre + band:
        return "High"
    if value <= centre - band:
        return "Lower"
    return "Mid"


@lru_cache(maxsize=None)
def _kinds(case_name):
    """(kinds, {case_id: kind_id}) for one college's admitted national cases. Pure Python, fixed seed."""
    import random
    import statistics
    from collections import Counter

    adm = _national_groups(case_name)[0]
    if len(adm) < KINDS_MIN:
        return [], {}
    rng = random.Random(KINDS_SEED)
    pop = adm if len(adm) <= KINDS_CAP else sorted(rng.sample(adm, KINDS_CAP), key=lambda v: v["num"])
    n = len(pop)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            D[i][j] = D[j][i] = _kind_distance(pop[i], pop[j])
    medoids = sorted(rng.sample(range(n), KINDS))
    for _ in range(KINDS_ROUNDS):
        assign = [min(medoids, key=lambda m: (D[i][m], m)) for i in range(n)]
        new = sorted(min((i for i in range(n) if assign[i] == m),
                         key=lambda c: (sum(D[c][j] for j in range(n) if assign[j] == m), c))
                     for m in medoids)
        if new == medoids:
            break
        medoids = new
    assign = [min(medoids, key=lambda m: (D[i][m], m)) for i in range(n)]

    centre_score = statistics.median(v["score"] for v in adm)
    rated = [v["activities"] for v in adm if v["activities"] is not None]
    centre_rating = statistics.median(rated) if rated else None
    described = []
    for m in medoids:
        members = [pop[i] for i in range(n) if assign[i] == m]
        med_score = statistics.median(v["score"] for v in members)
        acts = [v["activities"] for v in members if v["activities"] is not None]
        med_act = round(statistics.median(acts), 1) if acts else None
        majors = Counter(v["major_group"] for v in members if v["major_group"])
        top = majors.most_common(1)[0][0] if majors else None
        bits = [f"{_score_word(med_score, centre_score, KIND_SCORE_BAND)} score", top or "mixed majors"]
        if med_act is not None and centre_rating is not None:
            bits.append(f"activities {med_act:g}")
        described.append({"name": ", ".join(bits), "size": len(members), "median_sat": int(round(med_score)),
                          "median_activities": med_act, "top_major": top, "medoid_case_id": pop[m]["case_id"],
                          "_medoid": pop[m], "_members": [v["case_id"] for v in members]})
    described.sort(key=lambda k: (-k["median_sat"], k["medoid_case_id"]))
    names = Counter(k["name"] for k in described)
    for k in described:   # two kinds that read the same are told apart by their median score
        if names[k["name"]] > 1:
            k["name"] += f" (SAT {k['median_sat']})"
    kind_of = {}
    for i, k in enumerate(described, 1):
        k["kind_id"] = f"K{i}"
        for cid in k.pop("_members"):
            kind_of[cid] = k["kind_id"]
    return described, kind_of


def _kinds_for(sv, kinds, college):
    """The contract's `kinds` list: each kind with the student's distance to its medoid, nearest marked."""
    out = []
    for k in kinds:
        parts = {p: v for p, v in part_distances(sv, k["_medoid"], college).items() if p in KIND_PARTS}
        d = total(parts)
        out.append({"kind_id": k["kind_id"], "name": k["name"], "size": k["size"], "median_sat": k["median_sat"],
                    "median_activities": k["median_activities"], "top_major": k["top_major"],
                    "medoid_case_id": k["medoid_case_id"], "distance": None if d is None else round(d, 3),
                    "nearest": False})
    with_d = [k for k in out if k["distance"] is not None]
    if with_d:
        min(with_d, key=lambda k: (k["distance"], k["kind_id"]))["nearest"] = True
    return out


# ---------------------------------------------------------------- R4. what would bring the student closer

CHANGE_GAIN = 0.02        # a change is kept only if it raises the gap by this much
MAX_CHANGES = 3
SCORE_STEPS = (30, 60, 100)
RATING_STEPS = (1, 2)
NOTHING_HELPS = "Nothing we can measure here would move this."


def _tries(sv):
    """The changes R4 allows, each alone. Never hooks, home state, GPA, or anything about who the student is."""
    tried, seen = [], set()
    for pts in SCORE_STEPS:
        s2 = min(1600, sv["score"] + pts)
        if s2 == sv["score"] or ("score", s2) in seen:
            continue
        seen.add(("score", s2))
        tried.append((f"Score {s2 - sv['score']} points higher", dict(sv, score=s2)))
    if sv["activities"] is not None:
        for up in RATING_STEPS:
            r2 = min(10.0, sv["activities"] + up)
            if r2 == sv["activities"] or ("activities", r2) in seen:
                continue
            seen.add(("activities", r2))
            tried.append((f"Activities rating {r2 - sv['activities']:g} higher "
                          "(deeper involvement in the activities already listed)", dict(sv, activities=r2)))
    if len(sv["major_interests"]) > 1:
        for g in sv["major_interests"]:
            if g != sv["major_group"]:
                tried.append((f"Intended major in the {g} group (an interest the student named)",
                              dict(sv, major_group=g)))
    return tried


def _changes(sv, groups, college, base_gap):
    out = []
    for change, sv2 in _tries(sv):
        _, _, gap, na, _ = _gap(sv2, groups, college)
        if gap is None or gap - base_gap < CHANGE_GAIN:
            continue
        out.append({"change": change, "gap_before": round(base_gap, 3), "gap_after": round(gap, 3),
                    "lean_after": _lean(gap), "because": [cv["case_id"] for _, cv, _ in na[:MAX_NEAREST]]})
    out.sort(key=lambda c: -c["gap_after"])
    return out[:MAX_CHANGES]


def _pool(sv, groups, college, source, verified, own, kinds=((), {})):
    adm, den, wl = groups
    kind_list, kind_of = kinds
    out = {"source": source, "verified": verified, "status": None,
           "n_admitted": len(adm), "n_denied": len(den), "n_waitlisted": len(wl)}
    if not (adm or den or wl):
        out["status"] = "none"
    elif sv["score"] is None:
        out["status"] = "cant_say"
    elif not adm or not den:
        out["status"] = "none"
    elif len(adm) < NEEDED or len(den) < NEEDED:
        out["status"] = "not_enough"
    else:
        out["status"] = "ok"
    if out["status"] in ("none", "cant_say"):
        out["text"] = STATUS_TEXT[out["status"]]
        return out

    da, dd, gap, na, nd = _gap(sv, groups, college)
    lean = _lean(gap) if out["status"] == "ok" else None
    out.update({"d_admitted": round(da, 3), "d_denied": round(dd, 3), "gap": round(gap, 3), "lean": lean,
                "text": LEAN_TEXT[lean] if lean else STATUS_TEXT["not_enough"]})
    if lean:
        out["steady"], out["flips"] = _steady(sv, groups, college, lean)
    else:
        out["steady"], out["flips"] = None, []
    out["parts"] = _parts_summary(na)
    out["not_used"] = _not_used(na, nd, college)
    out["nearest_admitted"] = [_example(d, cv, p, own) for d, cv, p in na[:MAX_NEAREST]]
    out["nearest_denied"] = [_example(d, cv, p, own) for d, cv, p in nd[:MAX_NEAREST]]
    out["kinds"] = _kinds_for(sv, kind_list, college)
    out["changes"] = _changes(sv, groups, college, gap) if lean else []
    out["changes_note"] = "" if out["changes"] or not lean else NOTHING_HELPS
    out["points"] = _points(groups, kind_of)
    return out


def closeness(student, college, tags=None) -> dict:
    """The contract's `closeness` block for one student at one college. Deterministic; code only."""
    sv = _student_view(student, college, tags)
    short = _colleges.case_name_for(college) if college else None
    nat = _national_groups(short) if short else ([], [], [])
    kinds = _kinds(short) if short else ([], {})
    own = _own_groups(college) if college else ([], [], [])
    return {"needed": NEEDED, "neighbours": NEIGHBOURS,
            "student": {"score": sv["score"], "converted": sv["converted"], "activities": sv["activities"]},
            "national": _pool(sv, nat, college, NATIONAL_SOURCE, False, own=False, kinds=kinds),
            "own": _pool(sv, own, college, OWN_SOURCE, True, own=True),
            "caveat": CAVEAT}


# ---------------------------------------------------------------- command line

def _spread():
    from engine import pipeline
    for st in pipeline.demo_students():
        print(st["label"])
        for name in st["college_list"]:
            col = _colleges.find_college(name)
            n = closeness(st, col)["national"] if col else {"status": "outside"}
            if n["status"] == "ok":
                print(f"   {name[:40]:40} gap {n['gap']:+.3f}  d_adm {n['d_admitted']:.3f} d_den {n['d_denied']:.3f}"
                      f"  {n['lean']:20} steady={n['steady']} flips={len(n['flips'])}")
            else:
                print(f"   {name[:40]:40} {n['status']}")


if __name__ == "__main__":
    import json
    import sys

    if "--spread" in sys.argv:
        _spread()
    elif "--check" in sys.argv:
        print("--check is not built yet.")
    else:
        from engine import pipeline
        st = pipeline.demo_students()[0]
        col = _colleges.find_college(st["college_list"][0])
        print(json.dumps(closeness(st, col), indent=2, ensure_ascii=False))
