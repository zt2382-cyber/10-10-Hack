"""Finished cases like this student: counts, with n, from two pools that are never mixed.

  own       the counselor's school's verified finished cases (engine/caselog.py)
  national  self-reported public posts (data/cases/), real people, no names, NOT verified

Everything here is counting. No model is called and no probability is produced. The official admit rate
sits beside every count, and "not enough" is a normal answer.

Matching order (fixed): SAT within 50 (ACT converted) + same major group + same hook status;
then drop hook status; then drop major group; then widen SAT to within 100. Never wider than 100.
Home state is shown on each case but is not a matching rule.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from engine import colleges as _colleges
from engine import labels as _labels

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "data" / "cases"

NEEDED = 15
MAX_EXAMPLES = 6
OWN_SOURCE = "Your school's finished cases"
INVENTED_SOURCE = "Invented demo school history (not real students)"
NATIONAL_SOURCE = "Public posts on Reddit (r/collegeresults), self-reported"
NATIONAL_SKEW_NOTE = ("People who post skew high-scoring, computer-science-heavy and toward selective colleges. "
                      "This is not a national sample of applicants.")
_INVENTED_MARKS = {"SYNTHETIC", "DEMO"}
CAVEAT = ("People who post their results are admitted far more often than applicants overall. "
          "Read these as examples, not as a forecast for this student.")
_OUTCOME_WORD = {"accepted": "admitted", "admitted": "admitted", "rejected": "denied", "denied": "denied",
                 "waitlisted": "waitlisted"}
_FORBIDDEN = ("chance", "probab", "odds")

MAJOR_GROUPS = ["CS", "ENG", "BIO", "PREMED", "BUSINESS", "POLISCI", "PSYCH", "MATH", "PHYSICS", "ECON",
                "HUMANITIES", "ARTS", "OTHER"]

# Ordered keyword table: first group with a matching word wins. Words are matched at the start of a word.
_MAJOR_RULES = [
    ("PREMED", ["pre-?med", "pre-?health", "medic", "nursing", "health sci", "pre-?dental", "pre-?vet"]),
    ("CS", ["computer sci", "software", "data sci", "computing", "informatics", "machine learning",
            "artificial intel", "cyber", "programming", "information tech", "information sys"]),
    ("ENG", ["engineer", "mechanical", "electrical", "civil", "aerospace", "chemical eng", "robotics"]),
    ("CS", ["computer", "cs\\b", "cis\\b", "comp sci", "ai\\b"]),
    ("BIO", ["bio", "neuro", "genetic", "ecolog", "zoolog", "marine", "microbio"]),
    ("MATH", ["math", "statistic", "actuar", "applied math"]),
    ("PHYSICS", ["physic", "chemistry", "astronom", "geolog", "physical sci", "materials sci"]),
    ("ECON", ["econ"]),
    ("BUSINESS", ["business", "finance", "account", "marketing", "management", "entrepreneur", "commerce"]),
    ("POLISCI", ["polit", "polisci", "government", "international rel", "public policy", "law\\b", "pre-?law",
                 "social sci", "sociolog", "anthropolog", "public affairs"]),
    ("PSYCH", ["psych", "cognitive"]),
    ("HUMANITIES", ["humanit", "history", "english", "philosoph", "literature", "language", "media", "communicat",
                    "journalism", "education", "religio", "linguist", "classics", "writing"]),
    ("ARTS", ["arts?\\b", "music", "design", "theat", "film", "architect", "dance", "studio"]),
    ("OTHER", ["environment", "sustainab", "agricult", "hospitality", "sport", "kinesiolog"]),
]
_MAJOR_COMPILED = [(g, [re.compile(r"\b" + w, re.I) for w in ws]) for g, ws in _MAJOR_RULES]
_NO_MAJOR = {"", "-1", "undecided", "undeclared", "unknown", "none", "n/a", "na", "exploratory", "open"}

# hook status: student values and case-file values meet on one vocabulary
_STUDENT_HOOK = {"first_gen": "FIRST-GEN", "legacy": "LEGACY", "urm": "URM", "recruited_athlete": "ATHLETE"}
_CASE_HOOK = {"first-gen": "FIRST-GEN", "first_gen": "FIRST-GEN", "firstgen": "FIRST-GEN", "legacy": "LEGACY",
              "urm": "URM", "lgbt": "LGBT", "recruited_athlete": "ATHLETE", "athlete": "ATHLETE"}
_STOP = {"the", "and", "for", "with", "from", "about", "her", "his", "their", "was", "that", "this", "into", "own"}


def major_group_for(text) -> str | None:
    """Free-text major -> a major group, or None when blank/undecided/not recognised."""
    s = str(text or "").strip()
    if s.lower() in _NO_MAJOR:
        return None
    if s.upper() in MAJOR_GROUPS:
        return s.upper()
    if s.upper() in ("ENG", "POLISCI", "PREMED"):
        return s.upper()
    for group, pats in _MAJOR_COMPILED:
        if any(p.search(s) for p in pats):
            return group
    return None


def _case_major_group(raw) -> str | None:
    """Group for a case's major: a known group, a recognised word, else OTHER; blank/undecided -> None."""
    s = str(raw or "").strip()
    if s.lower() in _NO_MAJOR:
        return None
    return major_group_for(s) or "OTHER"


def _hooks_from_student(hooks) -> set:
    out = set()
    for h in hooks or []:
        k = _STUDENT_HOOK.get(re.sub(r"[^a-z_]", "", str(h).lower().replace("-", "_").replace(" ", "_")))
        if k:
            out.add(k)
    return out or {"NONE"}


def _hooks_from_case(raw) -> set:
    out = set()
    for h in re.split(r"[;,/|]", str(raw or "")):
        k = _CASE_HOOK.get(h.strip().lower().replace(" ", "_")) or _CASE_HOOK.get(h.strip().lower())
        if k:
            out.add(k)
    return out or {"NONE"}


def _valid_sat(v):
    """The SAT as the labels module cleans it (400 to 1600, else no score)."""
    return _labels._clean_student_scores({"sat": v})[0]


def _valid_act(v):
    """The ACT as the labels module cleans it (a whole number 1 to 36, else no score), and convertible."""
    act = _labels._clean_student_scores({"act": v})[1]
    return act if (act is not None and _colleges.act_to_sat(act) is not None) else None


def _score(sat, act):
    """(score on the SAT scale, was it converted from ACT)"""
    if sat is not None:
        return sat, False
    if act is not None:
        c = _colleges.act_to_sat(act)
        return (c, True) if c is not None else (None, False)
    return None, False


# ---------------------------------------------------------------- the two pools, as comparable rows

@lru_cache(maxsize=1)
def _national():
    """{case-file college short name: [case, ...]} and totals. Each case is a plain dict."""
    applicants = {}
    with open(CASES_DIR / "applicants_wide.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            sat = _valid_sat(r["SAT"]) if r["SAT"] != "-1" else None
            act = _valid_act(r["ACT"]) if r["ACT"] != "-1" else None
            score, _ = _score(sat, act)
            shown_act = act
            if act is not None and sat is not None:
                conv = _colleges.act_to_sat(act)
                if conv is None or abs(conv - sat) > 250:  # file noise, e.g. ACT 14 beside SAT 1440
                    shown_act = None
            try:
                rating = float(r["EC-AWARDS"])
            except ValueError:
                rating = -1.0
            res = r["Residence"].strip()
            applicants[r["applicant_id"]] = {
                "case_id": "N-" + r["applicant_id"], "num": int(r["applicant_id"]),
                "sat": sat, "act": shown_act, "score": score,
                "major": None if r["Major"].strip() in ("", "-1") else r["Major"].strip(),
                "group": _case_major_group(r["Major"]),
                "hooks_set": _hooks_from_case(r["Hooks"]), "hooks": r["Hooks"].strip() or "NONE",
                "home_state": None if res in ("", "-1") else res,
                "rating": None if rating < 0 else rating,
            }
    # One case per student per college. Some students have two rows at one college (a different school or
    # major inside it, or a waitlist that was later settled). A waitlist is superseded by the other row;
    # if one row is admitted and another denied, the student is counted as admitted (an offer was held).
    pairs: dict = {}
    n_decisions = 0
    with open(CASES_DIR / "decisions_long.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            outcome = _OUTCOME_WORD.get(r["outcome"].strip().lower())
            if r["applicant_id"] not in applicants or outcome is None:
                continue
            n_decisions += 1
            pairs.setdefault((r["college"], r["applicant_id"]), set()).add(outcome)
    by_college: dict = {}
    for (college, aid), outs in pairs.items():
        final = ("admitted" if "admitted" in outs else "denied" if "denied" in outs else "waitlisted")
        c = dict(applicants[aid])
        c["outcome"] = final
        by_college.setdefault(college, []).append(c)
    for rows in by_college.values():
        rows.sort(key=lambda c: c["num"])
    return by_college, len(applicants), n_decisions, len(pairs)


def _own_rows(college) -> list:
    """The school's own cases at this college. Raises if the store cannot be read (the caller says so)."""
    from engine import caselog
    rows = caselog.load_cases()
    out = []
    for r in rows:
        col = _colleges.find_college(r.get("college"))
        if col is None or col["id"] != college["id"] or r.get("outcome") not in _OUTCOME_WORD.values():
            continue
        sat, act = _valid_sat(r.get("sat")), _valid_act(r.get("act"))
        score, _ = _score(sat, act)
        m = re.search(r"\d+", str(r.get("case_id", "")))
        out.append({
            "case_id": r["case_id"], "num": int(m.group(0)) if m else 0, "sat": sat, "act": act, "score": score,
            "major": r.get("major_group"), "group": _case_major_group(r.get("major_group")),
            "hooks_set": _hooks_from_case(r.get("hooks")),
            "hooks": ", ".join(sorted(_hooks_from_case(r.get("hooks")))),
            "home_state": r.get("home_state") or None, "rating": None,
            "outcome": r["outcome"], "activities_note": r.get("activities_note") or "",
            "essay_theme": r.get("essay_theme") or "",
            "invented": str(r.get("synthetic") or "").strip().upper() in _INVENTED_MARKS,
        })
    return out


# ---------------------------------------------------------------- matching

def _steps(has_score: bool, has_group: bool):
    """The fixed relax order, as a list of criteria dicts (sat width, hook, major) and what each dropped."""
    raw = [
        ({"sat": 50 if has_score else None, "hook": True, "major": has_group}, []),
        ({"sat": 50 if has_score else None, "hook": False, "major": has_group}, ["hook status"]),
        ({"sat": 50 if has_score else None, "hook": False, "major": False},
         ["hook status"] + (["major group"] if has_group else [])),
        ({"sat": 100 if has_score else None, "hook": False, "major": False},
         ["hook status"] + (["major group"] if has_group else []) + (["SAT closeness (widened from 50 to 100 points)"] if has_score else [])),
    ]
    out, seen = [], []
    for crit, dropped in raw:
        if crit["sat"] is None and not crit["hook"] and not crit["major"]:
            continue  # nothing left to match on: that would be "everyone", not "like this student"
        key = (crit["sat"], crit["hook"], crit["major"])
        if key in seen:
            continue
        seen.append(key)
        out.append((crit, dropped))
    return out


def _filter(rows, crit, score, group, hooks):
    out = []
    for c in rows:
        if crit["sat"] is not None:
            if c["score"] is None or score is None or abs(c["score"] - score) > crit["sat"]:
                continue
        if crit["major"] and c["group"] != group:
            continue
        if crit["hook"] and not (c["hooks_set"] & hooks):
            continue
        out.append(c)
    return out


def _words(text) -> list:
    return [w for w in re.findall(r"[a-z]+", str(text or "").lower()) if len(w) >= 3 and w not in _STOP]


def _overlap(a, b) -> bool:
    wa, wb = _words(a), _words(b)
    return any(x == y or (len(x) >= 5 and len(y) >= 5 and x[:5] == y[:5]) for x in wa for y in wb)


def _shared(case, tags) -> list:
    out = []
    for t in (tags or {}).get("essay_themes") or []:
        if _overlap(t, case.get("essay_theme")):
            out.append("essay theme: %s" % t)
    for a in (tags or {}).get("activity_types") or []:
        if _overlap(a, case.get("activities_note")):
            out.append("activity: %s" % a)
    return out


def _clean_text(s) -> str:
    s = str(s or "")
    return "" if any(w in s.lower() for w in _FORBIDDEN) else s


def _example(c, own: bool, shared=None) -> dict:
    ex = {"case_id": c["case_id"], "sat": c["sat"], "act": c["act"], "major": c["major"], "hooks": c["hooks"],
          "home_state": c["home_state"], "activities_rating": c["rating"], "outcome": c["outcome"],
          "invented": bool(c.get("invented", False))}
    if own:
        ex["activities_note"] = _clean_text(c.get("activities_note"))
        ex["essay_theme"] = _clean_text(c.get("essay_theme"))
        if shared:
            ex["shared"] = shared
    return ex


def _pick_examples(matched, score, own, tags):
    shared = {c["case_id"]: (_shared(c, tags) if own else []) for c in matched}

    def key(c):
        diff = abs(c["score"] - score) if (c["score"] is not None and score is not None) else 0
        return (-len(shared[c["case_id"]]), diff, c["num"])

    ranked = sorted(matched, key=key)
    picked = ranked[:MAX_EXAMPLES]
    for need in ("denied", "admitted"):
        if any(c["outcome"] == need for c in picked):
            continue
        cand = next((c for c in ranked if c["outcome"] == need), None)
        if cand is None:
            continue
        if len(picked) < MAX_EXAMPLES:
            picked.append(cand)
        else:
            counts = {}
            for c in picked:
                counts[c["outcome"]] = counts.get(c["outcome"], 0) + 1
            drop = next(c for c in reversed(picked) if counts[c["outcome"]] > 1)
            picked.remove(drop)
            picked.append(cand)
    picked.sort(key=key)
    return [_example(c, own, shared[c["case_id"]]) for c in picked], sum(1 for v in shared.values() if v)


def _pool(rows, source, verified, score, converted, group, hooks, own, tags):
    res = {"source": source, "verified": verified, "status": "none", "n": 0, "admitted": 0, "denied": 0,
           "waitlisted": 0, "matched_on": [], "relaxed": [], "examples": []}
    if own:
        res["shared_theme_n"] = 0
    if not rows:
        res["note"] = "This pool has no finished cases for this college."
        return res
    has_score = score is not None
    chosen, crit, dropped = [], None, []
    for crit, dropped in _steps(has_score, group is not None):
        chosen = _filter(rows, crit, score, group, hooks)
        if len(chosen) >= NEEDED:
            break
    matched_on = []
    if crit["sat"] is not None:
        matched_on.append("SAT within %d points" % crit["sat"] + (" (student's ACT converted to SAT)" if converted else ""))
    else:
        matched_on.append("no test score given, so score was not used: matched on major group and hook status only"
                          if group is not None else "no test score or major given: matched on hook status only")
    if crit["major"]:
        matched_on.append("same major group")
    elif group is None:
        matched_on.append("no major given, so major was not used")
    if crit["hook"]:
        if hooks == {"NONE"}:
            matched_on.append("same hook status (neither has a hook)")
        else:
            shared_hooks = sorted({h for c in chosen for h in (c["hooks_set"] & hooks)})
            matched_on.append("shares a hook with the student (%s)" % ", ".join(shared_hooks or sorted(hooks)))
    n = len(chosen)
    res.update({
        "status": "ok" if n >= NEEDED else ("not_enough" if n >= 1 else "none"),
        "n": n,
        "admitted": sum(1 for c in chosen if c["outcome"] == "admitted"),
        "denied": sum(1 for c in chosen if c["outcome"] == "denied"),
        "waitlisted": sum(1 for c in chosen if c["outcome"] == "waitlisted"),
        "matched_on": matched_on, "relaxed": list(dropped),
    })
    res["_matched"] = chosen
    if chosen:
        res["examples"], themed = _pick_examples(chosen, score, own, tags)
        if own:
            res["shared_theme_n"] = themed
    else:
        res["note"] = "No finished cases in this pool match this student closely enough."
    if 0 < n < NEEDED:
        res["note"] = ("Only %d similar finished case%s here, fewer than the %d needed to read a pattern. "
                       "Treat them as individual examples." % (n, "" if n == 1 else "s", NEEDED))
    return res


def _status_for(n: int) -> str:
    return "ok" if n >= NEEDED else ("not_enough" if n >= 1 else "none")


def _unavailable_pool(why: str) -> dict:
    """The school's own pool when its cases could not be read: never 'none', which would mean 'no cases'."""
    return {"source": OWN_SOURCE, "verified": False, "invented": False, "n_invented": 0, "n_real": 0,
            "status": "unavailable", "n": 0, "admitted": 0, "denied": 0, "waitlisted": 0, "matched_on": [],
            "relaxed": [], "examples": [], "shared_theme_n": 0,
            "note": "Your school's finished cases could not be read, so nothing is shown here. "
                    "This does not mean the school has no cases. (%s)" % why[:120],
            "similarity_tool": {"used": False, "mode": None, "rule": "", "why": "the pool was not available"}}


def _plugin_student(student, sat, act, score, group, hooks) -> dict:
    """The allow-listed, de-identified fields a similarity plug-in may see."""
    return {"sat": sat, "act": act, "score": score, "major_group": group,
            "intended_major": student.get("intended_major"), "hooks": sorted(hooks),
            "home_state": student.get("home_state"), "gpa": student.get("gpa")}


def _apply_plugin(res: dict, plugin_student: dict, college, score, own: bool, tags) -> dict:
    """Let a connected similarity tool order (rank) or choose (filter) the matched cases. Code keeps every count."""
    matched = res.pop("_matched", [])
    tool = {"used": False, "mode": None, "rule": "", "why": "no similarity plug-in is connected"}
    res["similarity_tool"] = tool
    try:
        from engine import similarity_plugin as sp
        if not sp.configured():
            return res
        mode = sp.mode()
        tool.update(mode=mode, why="no matched cases to look at")
        if not matched:
            return res
        by_id = {c["case_id"]: c for c in matched}
        answer = sp.rank(plugin_student, [_example(c, own) for c in matched], college or {})
    except Exception as err:  # a plug-in can never break a run
        tool["why"] = "the similarity plug-in could not be used (%s)" % type(err).__name__
        return res
    if not answer.get("ok"):
        tool["why"] = answer.get("why") or "the similarity plug-in returned nothing usable"
        return res
    ranked = answer["ranked"]
    order = {r["case_id"]: i for i, r in enumerate(ranked)}
    reasons = {r["case_id"]: r["reasons"] for r in ranked}
    tool.update(used=True, rule=answer.get("rule", ""), why="")
    if mode == "rank":
        res["examples"] = sorted(res["examples"], key=lambda e: order.get(e["case_id"], len(order)))
    else:
        keep = [by_id[r["case_id"]] for r in ranked if r["similar"] and r["case_id"] in by_id]
        n = len(keep)
        res.update({"n": n, "status": _status_for(n),
                    "admitted": sum(1 for c in keep if c["outcome"] == "admitted"),
                    "denied": sum(1 for c in keep if c["outcome"] == "denied"),
                    "waitlisted": sum(1 for c in keep if c["outcome"] == "waitlisted"),
                    "matched_on": [tool["rule"] or "chosen by the connected similarity tool"], "relaxed": []})
        if own:
            res["n_invented"] = n if res.get("invented") else 0
            res["n_real"] = 0 if res.get("invented") else n
        themed = 0
        if keep:
            res["examples"], themed = _pick_examples(keep, score, own, tags)
            res["examples"].sort(key=lambda e: order.get(e["case_id"], len(order)))
        else:
            res["examples"] = []
        if own:
            res["shared_theme_n"] = themed
        if n == 0:
            res["note"] = "No finished cases were marked similar by the connected tool."
        elif n < NEEDED:
            res["note"] = ("Only %d case%s marked similar by the connected tool, fewer than the %d needed to read "
                           "a pattern. Treat them as individual examples." % (n, "" if n == 1 else "s", NEEDED))
        else:
            res.pop("note", None)
    for e in res["examples"]:
        if reasons.get(e["case_id"]):
            e["why_similar"] = reasons[e["case_id"]]
    return res


def find_similar(student, college, tags=None) -> dict:
    """The contract's `cases` object for one student and one college. Deterministic; counts only."""
    student = student or {}
    tags = tags or {}
    sat = _valid_sat(student.get("sat"))
    act = _valid_act(student.get("act"))
    score, converted = _score(sat, act)
    group = major_group_for(student.get("intended_major"))
    if group is None and tags.get("major_group") in MAJOR_GROUPS:
        group = tags["major_group"]
    hooks = _hooks_from_student(student.get("hooks"))
    pstudent = _plugin_student(student, sat, act, score, group, hooks)

    official = college.get("admit_rate") if college else None
    nat_rows, share = [], None
    own_all, own_error = [], None
    if college:
        short = _colleges.case_name_for(college)
        nat_rows = list(_national()[0].get(short, [])) if short else []
        try:
            own_all = _own_rows(college)
        except Exception as err:
            own_error = type(err).__name__
    if nat_rows:
        share = sum(1 for c in nat_rows if c["outcome"] == "admitted") / len(nat_rows)
    overcount = round(share / official, 1) if (share is not None and official) else None

    if own_error:
        own = _unavailable_pool(own_error)
    else:
        real = [r for r in own_all if not r["invented"]]
        invented = [r for r in own_all if r["invented"]]
        only_invented = bool(invented) and not real
        counted = invented if only_invented else real
        own = _pool(counted, INVENTED_SOURCE if only_invented else OWN_SOURCE, not only_invented, score, converted,
                    group, hooks, True, tags)
        own["invented"] = only_invented
        own["n_invented"] = own["n"] if only_invented else 0
        own["n_real"] = 0 if only_invented else own["n"]
        if real and invented:
            left = ("%d invented demo case%s at this college %s left out of the count; only real cases are counted."
                    % (len(invented), "" if len(invented) == 1 else "s", "was" if len(invented) == 1 else "were"))
            own["note"] = (own["note"] + " " + left) if own.get("note") else left
        elif only_invented:
            demo = "These are invented demo cases, not real or verified students."
            own["note"] = (own["note"] + " " + demo) if own.get("note") else demo
        own = _apply_plugin(own, pstudent, college, score, True, tags)

    national = _pool(nat_rows, NATIONAL_SOURCE, False, score, converted, group, hooks, False, tags)
    national = _apply_plugin(national, pstudent, college, score, False, tags)
    national["note"] = (national["note"] + " " + NATIONAL_SKEW_NOTE) if national.get("note") else NATIONAL_SKEW_NOTE

    return {
        "needed": NEEDED,
        "own": own,
        "national": national,
        "official_admit_rate": official,
        "pool_admit_share_all": None if share is None else round(share, 3),
        "overcount": overcount,
        "caveat": CAVEAT,
    }


def pool_summary() -> dict:
    """How many cases, decisions and colleges are in each pool."""
    by_college, n_cases, n_dec, n_pairs = _national()
    try:
        from engine import caselog
        own = caselog.load_cases()
        invented = sum(1 for c in own if str(c.get("synthetic") or "").strip().upper() in _INVENTED_MARKS)
        own_part = {"source": OWN_SOURCE, "status": "ok", "cases": len(own), "decisions": len(own),
                    "colleges": len({c["college"] for c in own}), "invented_cases": invented,
                    "real_cases": len(own) - invented}
    except Exception as err:
        own_part = {"source": OWN_SOURCE, "status": "unavailable", "cases": None, "decisions": None,
                    "colleges": None, "invented_cases": None, "real_cases": None,
                    "note": "Your school's finished cases could not be read (%s). "
                            "This does not mean the school has no cases." % type(err).__name__}
    return {
        "own": own_part,
        "national": {"source": NATIONAL_SOURCE, "cases": n_cases, "decisions": n_dec, "student_college_cases": n_pairs,
                     "colleges": len(by_college)},
    }


def _show(name, res):
    print("=== %s ===" % name)
    off = res["official_admit_rate"]
    print("Official admit rate: %s | Whole self-reported pool admitted share: %s | Over-count: %s" % (
        "unknown" if off is None else "%.1f%%" % (off * 100), res["pool_admit_share_all"], res["overcount"]))
    for key in ("own", "national"):
        p = res[key]
        print("  [%s] %s (%s)" % (key, p["source"], "verified" if p["verified"] else "not verified"))
        print("    status=%s  n=%d  admitted=%d denied=%d waitlisted=%d" % (
            p["status"], p["n"], p["admitted"], p["denied"], p["waitlisted"]))
        print("    matched on: %s | relaxed: %s" % ("; ".join(p["matched_on"]) or "-", "; ".join(p["relaxed"]) or "-"))
        if p.get("note"):
            print("    note: %s" % p["note"])
        for ex in p["examples"][:3]:
            print("    - %s SAT %s ACT %s %s %s %s -> %s%s" % (
                ex["case_id"], ex["sat"], ex["act"], ex["major"], ex["hooks"], ex["home_state"], ex["outcome"],
                "  shared: " + ", ".join(ex["shared"]) if ex.get("shared") else ""))
    print("  " + res["caveat"])


if __name__ == "__main__":
    demo = {"label": "Demo student (SYNTHETIC)", "sat": 1450, "home_state": "NJ",
            "intended_major": "Computer Science", "hooks": []}
    print(pool_summary())
    for nm in ("Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick"):
        _show(nm, find_similar(demo, _colleges.find_college(nm), tags={"essay_themes": ["family"], "activity_types": ["research"]}))
