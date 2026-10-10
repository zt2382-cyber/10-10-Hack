"""The one flow: mask the text, look things up, label, find cases, check the balance, record the run.

Order of the visible steps: retrieve, score, bucket, explain, log.
Code sets every label, count and number. A model only reads the essay, and only after masking.
Every part is optional at import time: a missing or failing part turns into a plain "off" note, never a crash.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from engine import colleges as C

ROOT = Path(__file__).resolve().parent.parent
AGENT_NAME = os.environ.get("PRISM_AGENT_NAME", "counselor-copilot")

REFUSALS = [
    "No personal chance of admission is given. The counts are examples from finished cases, shown beside the official admit rate.",
    "The essay is never rated and never changes a label.",
]


def _part(name):
    """Import engine.<name> if it exists and loads; otherwise None."""
    try:
        return __import__(f"engine.{name}", fromlist=[name])
    except Exception:  # a part that is absent or broken must not stop the run
        return None


def _ms(t0):
    return int((time.perf_counter() - t0) * 1000)


def _safe(fn, fallback, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # report, do not hide
        if isinstance(fallback, dict):
            return {**fallback, "error": f"{type(e).__name__}: {e}"}
        return fallback


def _fallback_label(college):
    if college is None:
        return {"state": "outside_data", "text": "Outside our data", "rule_id": "R0",
                "rule_text": "This college is not in our college file, so nothing is said about it.",
                "score_used": None, "score_kind": None, "inputs": {}, "not_used": [], "caveats": [],
                "steady": True, "flips": [], "publishers": [], "publishers_disagree": False}
    return {"state": "cant_say", "text": "Can't say", "rule_id": "R2",
            "rule_text": "The label rules are not available, so no label is given.",
            "score_used": None, "score_kind": None, "inputs": {}, "not_used": [], "caveats": [],
            "steady": True, "flips": [], "publishers": [], "publishers_disagree": False}


def _cost_note(college, student):
    cost = college.get("cost_year")
    if not cost:
        return None
    rounded = int(round(cost / 1000.0) * 1000)
    where = ""
    if college.get("control") == "public":
        where = " in-state" if (student.get("home_state") or "").upper() == college.get("state") else " (out-of-state students pay more)"
    return f"Sticker cost is about ${rounded:,} a year{where}. What this family would actually pay is not known here."


def _confirm(claim, hits):
    """A statement is "confirmed" only when PRISM's Knowledge Base returns a passage that holds the same sentence.
    The search score never decides: the search is keyword overlap and will happily return the wrong college."""
    want = " ".join(str(claim.get("text", "")).split())
    for h in hits or []:
        body = " ".join(str(h.get("text") or h.get("content") or "").split())
        if want and want in body:
            return {"status": "confirmed", "text": want, "score": h.get("score") or h.get("relevance_score"),
                    "doc": h.get("doc") or h.get("doc_name")}
    return {"status": "not confirmed", "text": "", "score": None, "doc": None,
            "why": "PRISM's Knowledge Base returned no passage holding this statement."}


def kb_check(text: str) -> dict:
    """Check any one statement against the Knowledge Base. Used by the screen's 'check a statement' box and by tests."""
    prism_mod = _part("prism")
    if not prism_mod or not _safe(prism_mod.status, {"on": False}).get("on"):
        return {"status": "off", "why": "PRISM's Knowledge Base is not switched on in this run."}
    return _confirm({"text": text}, _safe(prism_mod.kb_search, [], text, 3))


RANK = {"reach_for_everyone": 0, "reach": 0, "target": 1, "likely": 2}
_RATING = re.compile(r"rates (.+?) as (Very Important|Important|Considered|Not Considered)")


def _levers(student, col, label, says, labels_mod):
    """What could change the picture at this college. Every line is a published fact or the label rule re-run
    with a different score. Nothing here is a prediction."""
    out = []
    state, name = label.get("state"), col["name"]
    sat, act = student.get("sat"), student.get("act")
    # 1. the test score: re-run the same rule at higher scores and report the first one that moves the label
    if state == "reach_for_everyone":
        out.append({"kind": "score", "moves": False,
                    "text": "No test score changes this label. The college admits fewer than 15 in 100 applicants, so it stays a reach for everyone."})
    elif state == "cant_say" and not sat and not act:
        out.append({"kind": "score", "moves": True, "text": "A test score would let this college be labelled."})
    elif state in ("reach", "target") and labels_mod and (sat or act):
        key, top, step = ("sat", 1600, 10) if sat else ("act", 36, 1)
        base = student[key]
        for s in range(base + step, top + 1, step):
            trial = labels_mod.label_college({**student, key: s}, col)
            if RANK.get(trial.get("state"), -1) > RANK.get(state, -1):
                out.append({"kind": "score", "moves": True, "points": s - base, "new_score": s, "to": trial.get("state"),
                            "text": f"A{'n' if key == 'act' else 'n'} {key.upper()} of {s} ({s - base} point{'s' if s - base != 1 else ''} higher) would make this a {trial.get('text', '').lower()} under the same rule."})
                break
        else:
            out.append({"kind": "score", "moves": False, "text": "No higher test score changes this label under the rule."})
    elif state == "likely":
        out.append({"kind": "score", "moves": False, "text": "Already a likely. A higher score does not change the label."})
    # 2. what the college itself says matters most
    rated = {}
    src = None
    short = name
    for c in says or []:
        m = _RATING.search(c.get("text", ""))
        if m:
            rated.setdefault(m.group(2), []).append(m.group(1))
            src = src or c.get("source_url")
            short = c.get("text", "")[:m.start()].strip() or name  # the name the college's own statement uses
    if rated.get("Very Important") or rated.get("Important"):
        top = rated.get("Very Important") or rated.get("Important")
        word = "Very Important" if rated.get("Very Important") else "Important"
        out.append({"kind": "says", "factors": top, "rating": word, "source_url": src,
                    "not_considered": rated.get("Not Considered", []),
                    "text": f"{short} rates as {word}: {', '.join(top)}." +
                            (f" It rates as Not Considered: {', '.join(rated['Not Considered'])}." if rated.get("Not Considered") else "")})
    # 3. sending a score or not, and where the applicant lives: published counts only
    for c in says or []:
        if c.get("claim_id") in ("test_range", "admit_residency"):
            out.append({"kind": "sent_scores" if c["claim_id"] == "test_range" else "residency", "text": c["text"], "source_url": c.get("source_url")})
    return out


FIT_FACTORS = {
    "c7_essay": "the application essay",
    "c7_test_scores": "test scores",
    "c7_class_rank": "class rank",
    "c7_demonstrated_interest": "shown interest (visits, contact)",
    "c7_alumni": "a family link to a graduate",
}


def _fit(student, says, essay_words):
    """What the college says it reads, beside what is in this profile. Three neutral states and no total:
    this is not a score, and a factor being present does not predict anything."""
    looks, skips, src, year = [], [], None, None
    for c in says or []:
        cid = c.get("claim_id")
        m = _RATING.search(c.get("text", ""))
        if cid not in FIT_FACTORS or not m:
            continue
        src, year = src or c.get("source_url"), year or c.get("year")
        rating, factor = m.group(2), FIT_FACTORS[cid]
        if rating == "Not Considered":
            skips.append(factor)
            continue
        if cid == "c7_essay":
            state, note = ("in_profile", "A draft essay is in this profile.") if essay_words else ("not_yet", "No essay in this profile yet.")
        elif cid == "c7_test_scores":
            state, note = ("in_profile", "A test score is in this profile.") if (student.get("sat") or student.get("act")) else ("not_yet", "No test score in this profile yet.")
        elif cid == "c7_alumni":
            state, note = ("in_profile", "The profile lists a family link.") if "legacy" in (student.get("hooks") or []) else ("cant_see", "No family link is listed in this profile.")
        else:
            state, note = "cant_see", "We can't see this here. Ask your counselor."
        looks.append({"factor": factor, "rating": rating, "state": state, "note": note})
    if not looks and not skips:
        return None
    order = {"Very Important": 0, "Important": 1, "Considered": 2}
    looks.sort(key=lambda x: (order.get(x["rating"], 9), x["factor"]))
    return {"looks_for": looks, "does_not_consider": skips, "source_url": src, "year": year,
            "note": "This is what the college says it reads. It is not a score, and it does not predict admission."}


def _score_ladder(student, found, labels_mod):
    """How many colleges on the list move up a bucket at 30, 50 and 100 more SAT points (or 1, 2, 3 ACT points)."""
    if not labels_mod or not (student.get("sat") or student.get("act")):
        return []
    key, steps, top = ("sat", (30, 50, 100), 1600) if student.get("sat") else ("act", (1, 2, 3), 36)
    base, ladder = student[key], []
    now = {n: labels_mod.label_college(student, c) for n, c in found if c}
    for d in steps:
        if base + d > top:
            continue
        moves = []
        for n, c in found:
            if not c:
                continue
            t = labels_mod.label_college({**student, key: base + d}, c)
            if RANK.get(t.get("state"), -1) > RANK.get(now[n].get("state"), -1):
                moves.append({"name": c["name"], "from": now[n].get("text"), "to": t.get("text")})
        ladder.append({"points": d, "new_score": base + d, "kind": key.upper(), "moves": moves})
    return ladder


HOOKS = ("first_gen", "legacy", "urm", "recruited_athlete", "none")


def _text(v, limit):
    return str(v).strip()[:limit] if isinstance(v, (str, int, float)) and str(v).strip() else None


def _normalize(student_input, labels_mod, privacy_mod):
    """Clean the input once, at the door. Returns (student, essay, college names, notes).
    Unknown fields are dropped: nothing a caller adds (a name, a school, gender, race, income) is carried along."""
    raw = student_input if isinstance(student_input, dict) else {}
    notes = []
    essay = raw.get("essay") if isinstance(raw.get("essay"), str) else ""

    def hide(text, limit):
        """Free text a person typed is masked before it is kept, shown or sent anywhere."""
        t = _text(text, limit)
        if not t:
            return None
        if not privacy_mod:
            return "[hidden: the privacy check is not available]"
        try:
            return privacy_mod.mask(t).get("text", "")[:limit]
        except Exception:
            return "[hidden: the privacy check could not run]"

    # scores: one rule for labels, cases, balance and levers
    scores = {"sat": raw.get("sat"), "act": raw.get("act")}
    if labels_mod and hasattr(labels_mod, "_clean_student_scores"):
        sat, act, score_notes = labels_mod._clean_student_scores(scores)
        notes += score_notes
    else:
        sat = act = None
    if sat and act:
        as_sat = C.act_to_sat(act)
        if as_sat and abs(as_sat - sat) > 150:
            notes.append(f"The SAT ({sat}) and the ACT ({act}, about {as_sat} on the SAT scale) point in different directions. The SAT was used. Check which score will be sent.")
    try:
        gpa = float(raw.get("gpa")) if raw.get("gpa") not in (None, "") else None
        gpa = gpa if gpa is not None and 0 <= gpa <= 5 else None
    except (TypeError, ValueError):
        gpa = None
    state = _text(raw.get("home_state"), 2)
    hooks = [h for h in (raw.get("hooks") if isinstance(raw.get("hooks"), list) else []) if h in HOOKS]

    # colleges: a list of names, each counted once
    cl = raw.get("college_list")
    if isinstance(cl, str):
        cl = [cl]
    if not isinstance(cl, list):
        if cl not in (None, ""):
            notes.append("The college list could not be read, so no colleges were labelled.")
        cl = []
    names, seen, dupes = [], set(), 0
    for n in cl[:30]:
        n = _text(n, 120) if isinstance(n, str) else None
        if not n:
            continue
        col = C.find_college(n)
        key = col["id"] if col else " ".join(n.lower().split())
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        names.append(col["name"] if col else n)
    if dupes:
        notes.append(f"{dupes} college{'s were' if dupes != 1 else ' was'} on the list more than once and counted once.")

    acts = []
    for a in (raw.get("activities") if isinstance(raw.get("activities"), list) else [])[:8]:
        if isinstance(a, dict):
            item = {k: hide(a.get(k), 200) for k in ("type", "role", "description")}
            if any(item.values()):
                acts.append(item)
    student = {"label": hide(raw.get("label"), 80) or "Student", "sat": sat, "act": act, "gpa": gpa,
               "gpa_scale": 4.0, "home_state": state.upper() if state and state.isalpha() else None,
               "intended_major": hide(raw.get("intended_major"), 60), "hooks": hooks or ["none"],
               "activities": acts, "college_list": names}
    return student, essay, names, notes


def run(student_input: dict, use_model: bool = True) -> dict:
    labels_mod, cases_mod, balance_mod = _part("labels"), _part("cases"), _part("balance")
    privacy_mod, reader_mod, claims_mod, prism_mod = _part("privacy"), _part("reader"), _part("claims"), _part("prism")
    student, essay, names, input_notes = _normalize(student_input, labels_mod, privacy_mod)
    is_demo = isinstance(student_input, dict) and str(student_input.get("label", "")) in _demo_labels()
    if not is_demo:
        student["label"] = "Student"  # a typed label could be a real name; it is never kept, shown or sent
    session_id = "s-" + uuid.uuid4().hex[:12]
    steps = []

    # ---- privacy first: nothing identifying reaches a model. If the check cannot run, the essay is not read. ----
    masked = {"text": "", "masked": [], "blocked": False, "reason": ""}
    if essay:
        try:
            if not privacy_mod:
                raise RuntimeError("privacy check missing")
            masked = privacy_mod.mask(essay)
            if not isinstance(masked, dict) or "text" not in masked:
                raise RuntimeError("privacy check gave no answer")
        except Exception:
            masked = {"text": "", "masked": [], "blocked": True,
                      "reason": "The privacy check could not run, so the essay was not read by anything."}
    n_masked = sum(m.get("count", 0) for m in masked.get("masked", []))
    guard = "our own check"
    verdicts = [{"by": "Our own check (code)", "blocked": bool(masked.get("blocked")), "detail": masked.get("reason", "")}] if essay else []
    if essay and masked.get("blocked"):
        # Stopped here. The text is not sent to PRISM or to any model: nothing leaves this computer.
        verdicts.append({"by": "PRISM guardrail", "blocked": None,
                         "detail": "Not asked. Our own check had already stopped the essay, so nothing was sent anywhere."})
    elif prism_mod and essay:
        scr = _safe(prism_mod.screen, {"blocked": False, "how": "off", "detail": ""}, masked.get("text", ""))
        if scr.get("how") == "prism-proxy":
            guard = "our own check, then PRISM's guardrail"
            verdicts.append({"by": "PRISM guardrail", "blocked": bool(scr.get("blocked")), "detail": str(scr.get("detail", ""))[:200]})
            if scr.get("blocked"):
                masked["blocked"] = True
                masked["reason"] = str(scr.get("detail", ""))[:200]
    privacy = {
        "masked": masked.get("masked", []), "blocked": bool(masked.get("blocked")), "reason": masked.get("reason", ""),
        "guard": guard, "verdicts": verdicts,
        "note": ("This essay was stopped. The essay reader did not read it." if masked.get("blocked") else
                 f"{n_masked} personal detail{'s were' if n_masked != 1 else ' was'} masked before any model read the essay."
                 if essay else "No essay was given, so no model read anything."),
    }

    # ---- retrieve ----
    t0 = time.perf_counter()
    found = [(n, C.find_college(n)) for n in names]
    pool = _safe(cases_mod.pool_summary, {}) if cases_mod and hasattr(cases_mod, "pool_summary") else {}
    in_file = sum(1 for _, c in found if c)
    steps.append({"step": "retrieve", "by": "code", "ms": _ms(t0),
                  "what": f"Looked up {len(found)} college{'s' if len(found) != 1 else ''} ({in_file} in our file of {len(C.load_colleges()):,} colleges) and the finished-case pools"})

    # ---- explain (the only model call), done before scoring so its tags can order the cases ----
    t0 = time.perf_counter()
    reader = {"status": "off", "model": None, "tags": {}, "notes": [], "dropped": 0}
    if masked.get("blocked"):
        reader["status"] = "blocked"
    elif reader_mod and use_model:
        reader = _safe(reader_mod.read, reader, masked.get("text", ""), student.get("activities") or [], student.get("intended_major"))
    elif not essay:
        reader["status"] = "empty"
    trace_payloads = reader.pop("trace_payloads", []) if isinstance(reader, dict) else []
    explain_ms = _ms(t0)
    tags = reader.get("tags") or {}

    # ---- score and bucket ----
    t0 = time.perf_counter()
    tracker_mod = _part("tracker")
    student_key = (student_input.get("label") if is_demo else "current") if isinstance(student_input, dict) else "current"
    tracked = _safe(tracker_mod.get, {}, student_key) if tracker_mod else {}
    out, labelled = [], []
    for name, col in found:
        label = _safe(labels_mod.label_college, _fallback_label(col), student, col) if labels_mod else _fallback_label(col)
        labelled.append({"college": col, "name": col["name"] if col else name, "label": label})
        if col is None:
            out.append({"id": None, "name": name, "suggestion": C.suggest(name), "state": None, "control": None, "admit_rate": None, "sat25": None,
                        "sat75": None, "act25": None, "act75": None, "cost_year": None, "source": None, "in_data": False,
                        "label": label, "cases": None, "says": [], "myths": [], "levers": [], "cost_note": None, "flags": []})
            continue
        cases = _safe(cases_mod.find_similar, None, student, col, tags) if cases_mod else None
        says = _safe(claims_mod.college_says, [], col) if claims_mod else []
        myths = _safe(claims_mod.myth_checks, [], col) if claims_mod and hasattr(claims_mod, "myth_checks") else []
        flags = []
        if "recruited_athlete" in (student.get("hooks") or []):
            flags.append("Recruited athletes are admitted through a separate process. Ask the coach and the admissions office.")
        out.append({**{k: col.get(k) for k in ("id", "name", "state", "control", "admit_rate", "sat25", "sat75", "act25", "act75", "cost_year", "source")},
                    "in_data": True, "label": label, "cases": cases, "says": says, "myths": myths,
                    "levers": _safe(_levers, [], student, col, label, says, labels_mod),
                    "fit": _safe(_fit, None, student, says, len(essay.split())),
                    "tracker": tracked.get(col["id"]) or {"status": "considering", "outcome": None},
                    "cost_note": _cost_note(col, student), "flags": flags})
    score_ms = _ms(t0)
    have = "SAT of %s" % student["sat"] if student.get("sat") else ("ACT of %s" % student["act"] if student.get("act") else "no test score")
    steps.append({"step": "score", "by": "code", "ms": score_ms,
                  "what": f"Compared the student's {have} with each college's published range, and found finished cases like this student"})

    t0 = time.perf_counter()
    balance = _safe(balance_mod.assess, {"counts": {}, "warnings": [], "suggestions": [], "cost_notes": []}, labelled, student) if balance_mod else {"counts": {}, "warnings": [], "suggestions": [], "cost_notes": []}
    counts = balance.get("counts") or {}
    said = sum(v for k, v in counts.items() if k in ("reach", "target", "likely"))
    steps.append({"step": "bucket", "by": "code", "ms": _ms(t0),
                  "what": f"Labelled {said} college{'s' if said != 1 else ''}; {counts.get('cant_say', 0)} can't be labelled and {counts.get('outside_data', 0)} are outside our data"})

    kept, dropped = len(reader.get("notes") or []), reader.get("dropped", 0)
    explain_what = {"ok": f"Read the essay for themes and exact quotes; {kept} note{'s' if kept != 1 else ''} kept, {dropped} dropped",
                    "blocked": "Did not read the essay: it was stopped by the privacy screen",
                    "empty": "No essay to read", "off": "The essay reader is off (no model key), so no model was used"}.get(reader.get("status"), "The essay reader did not finish")
    steps.append({"step": "explain", "by": reader.get("model") or "code", "ms": explain_ms, "what": explain_what})

    # ---- knowledge base: back one statement per college from PRISM, when it is on ----
    kb_state = "off"
    if prism_mod and claims_mod:
        st = _safe(prism_mod.status, {"on": False})
        if st.get("on"):
            kb_state = "on"
            todo = [claim for col in out for claim in (col.get("says") or [])[:3]][:12]
            with ThreadPoolExecutor(max_workers=8) as ex:
                hits = list(ex.map(lambda cl: _safe(prism_mod.kb_search, [], cl.get("text", ""), 3), todo))
            for claim, found_hits in zip(todo, hits):
                claim["kb"] = _confirm(claim, found_hits)

    # ---- log: sent in the background so PRISM can never slow down or break an answer ----
    prism = {"status": "off", "why": "PRISM is not set up in this run.", "session_id": None, "records_sent": 0,
             "guardrail": guard, "evaluator": None, "kb": kb_state}
    log_what = "Run not recorded: PRISM is off"
    if prism_mod:
        st = _safe(prism_mod.status, {"on": False, "why": "PRISM did not answer."})
        prism["why"] = st.get("why", "")
        log_what = "Run not recorded: " + (st.get("why") or "PRISM is off")
        if st.get("on"):
            prism.update({"status": "on", "session_id": session_id, "records_sent": len(trace_payloads)})
            log_what = f"Sent {len(trace_payloads)} model call{'s' if len(trace_payloads) != 1 else ''} and the five steps to PRISM"
    steps.append({"step": "log", "by": "code", "ms": 0, "what": log_what})
    if prism["status"] == "on":
        frozen_steps = [dict(x) for x in steps]

        def _send():
            for tp in trace_payloads:
                msgs, outm = tp.get("input_messages"), tp.get("output_message")
                if not is_demo:  # a real student's text is never stored in a third-party record, even masked
                    msgs = [{"role": "user", "content": f"[withheld: {len(json.dumps(msgs or ''))} characters of masked text]"}]
                    outm = {"role": "assistant", "content": f"[withheld: {kept} notes kept, {dropped} dropped]"}
                _safe(prism_mod.trace, {"ok": False}, AGENT_NAME, session_id, tp.get("model"), msgs,
                      outm, tp.get("latency_ms") or 0,
                      {"request_id": tp.get("request_id"), "step": "explain", "synthetic": is_demo,
                       "notes_kept": kept, "notes_dropped": dropped})
            _safe(prism_mod.submit_steps, {"ok": False}, session_id, frozen_steps)

        threading.Thread(target=_send, daemon=True).start()

    shown = sum(len(c.get("says") or []) for c in out) + kept + len(balance.get("warnings") or [])
    hidden = dropped + sum(1 for c in out for s in (c.get("says") or []) if s.get("checked") is False)
    for c in out:  # a statement that failed its own check is never shown
        c["says"] = [s for s in (c.get("says") or []) if s.get("checked") is not False]

    student_view = dict(student)  # already an allowlist: see _normalize
    student_view["essay_words"] = len(essay.split())
    student_view["input_notes"] = input_notes
    return {
        "run_id": session_id, "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "synthetic": is_demo,
        "student": student_view, "steps": sorted(steps, key=lambda s: ["retrieve", "score", "bucket", "explain", "log"].index(s["step"])),
        "privacy": privacy, "reader": reader, "colleges": out, "balance": balance,
        "checks": {"sentences_shown": shown, "sentences_hidden": hidden,
                   "hidden_reasons": (["A quote was not found word for word in the essay."] if dropped else [])},
        "levers": {
            "list": {"text": ("The biggest thing you can change is the list itself."
                              if (balance.get("warnings") or []) else "The list has a reach, a target and a likely."),
                     "warnings": len(balance.get("warnings") or []), "suggestions": len(balance.get("suggestions") or [])},
            "score_ladder": _safe(_score_ladder, [], student, found, labels_mod),
            "note": "These are the same written rule re-run with a different score, and each college's own published statements. They are not predictions.",
            "fit_coverage": {"with": sum(1 for c in out if c.get("fit")), "of": sum(1 for c in out if c.get("in_data"))},
        },
        "student_key": student_key,
        "prism": prism, "pools": pool, "refusals": REFUSALS,
    }


def _demo_labels() -> set:
    try:
        return {d["label"] for d in demo_students()}
    except Exception:
        return set()


def demo_students() -> list[dict]:
    """SYNTHETIC demo students for the screen's picker."""
    essays = {}
    for p in sorted((ROOT / "data" / "synthetic").glob("SYNTHETIC_essay_*.txt")):
        essays[p.stem] = p.read_text(encoding="utf-8", errors="replace")
    e = lambda key: next((v for k, v in essays.items() if key in k), "")
    return [
        {"label": "Student A (SYNTHETIC): strong scores, reach-heavy list", "sat": 1450, "act": None, "gpa": 3.9, "gpa_scale": 4.0,
         "home_state": "NJ", "intended_major": "Computer Science", "hooks": ["first_gen"],
         "activities": [{"type": "Research", "role": "Student researcher", "description": "Summer lab program; co-author on a poster"},
                        {"type": "Robotics", "role": "Team captain", "description": "State finalist two years"}],
         "essay": e("essay_1"),
         "college_list": ["Cornell University", "Massachusetts Institute of Technology", "Stanford University", "Carnegie Mellon University",
                          "Princeton University", "Georgia Institute of Technology-Main Campus", "Purdue University-Main Campus"]},
        {"label": "Student B (SYNTHETIC): mid scores, in-state list", "sat": 1250, "act": None, "gpa": 3.5, "gpa_scale": 4.0,
         "home_state": "NJ", "intended_major": "Biology", "hooks": ["none"],
         "activities": [{"type": "Volunteering", "role": "Hospital volunteer", "description": "Four hours a week for two years"}],
         "essay": e("essay_2"),
         "college_list": ["Rutgers University-New Brunswick", "Pennsylvania State University-Main Campus", "Boston University",
                          "New York University", "Northeastern University"]},
        {"label": "Student C (SYNTHETIC): ACT only", "sat": None, "act": 29, "gpa": 3.7, "gpa_scale": 4.0,
         "home_state": "TX", "intended_major": "Mechanical Engineering", "hooks": ["none"],
         "activities": [{"type": "Athletics", "role": "Varsity swimmer", "description": "Four years"}],
         "essay": e("essay_3"),
         "college_list": ["The University of Texas at Austin", "Texas A&M University-College Station", "Rice University",
                          "Purdue University-Main Campus", "The University of Texas at Dallas"]},
        {"label": "Student D (SYNTHETIC): no test score", "sat": None, "act": None, "gpa": 3.9, "gpa_scale": 4.0,
         "home_state": "CA", "intended_major": "Political Science", "hooks": ["first_gen"],
         "activities": [{"type": "Debate", "role": "Captain", "description": "State semifinalist"}],
         "essay": "",
         "college_list": ["University of California-Los Angeles", "University of California-Berkeley", "University of Southern California",
                          "University of California-Santa Cruz"]},
        {"label": "Student G (SYNTHETIC): a balanced list", "sat": 1350, "act": None, "gpa": 3.7, "gpa_scale": 4.0,
         "home_state": "NJ", "intended_major": "Psychology", "hooks": ["none"],
         "activities": [{"type": "Peer tutoring", "role": "Founder", "description": "Started a lunchtime tutoring table; 14 regulars by spring"},
                        {"type": "Work", "role": "Barista", "description": "Twelve hours a week since grade 10"}],
         "essay": e("essay_6"),
         "college_list": ["Northeastern University", "Boston University", "Rutgers University-New Brunswick",
                          "Virginia Polytechnic Institute and State University", "Pennsylvania State University-Main Campus",
                          "Rowan University", "Montclair State University"]},
        {"label": "Student H (SYNTHETIC): a lower score and a strong story", "sat": 1080, "act": None, "gpa": 3.4, "gpa_scale": 4.0,
         "home_state": "NJ", "intended_major": "Nursing", "hooks": ["first_gen"],
         "activities": [{"type": "Family care", "role": "Carer", "description": "Looks after two younger siblings every weekday afternoon"},
                        {"type": "Work", "role": "Pharmacy assistant", "description": "Twenty hours a week"}],
         "essay": e("essay_7"),
         "college_list": ["Rutgers University-New Brunswick", "Rowan University", "Montclair State University",
                          "University of Delaware", "Temple University"]},
        {"label": "Student I (SYNTHETIC): recruited athlete", "sat": 1300, "act": None, "gpa": 3.6, "gpa_scale": 4.0,
         "home_state": "PA", "intended_major": "Business", "hooks": ["recruited_athlete"],
         "activities": [{"type": "Athletics", "role": "Club and varsity swimmer", "description": "State finalist; in contact with two college coaches"}],
         "essay": "",
         "college_list": ["Pennsylvania State University-Main Campus", "Virginia Polytechnic Institute and State University",
                          "University of Virginia-Main Campus", "University of Michigan-Ann Arbor", "Purdue University-Main Campus"]},
        {"label": "Student E (SYNTHETIC): essay with a hidden instruction", "sat": 1450, "act": None, "gpa": 3.9, "gpa_scale": 4.0,
         "home_state": "NJ", "intended_major": "Computer Science", "hooks": ["none"], "activities": [],
         "essay": e("essay_4"),
         "college_list": ["Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick"]},
        {"label": "Student F (SYNTHETIC): essay with personal details", "sat": 1350, "act": None, "gpa": 3.6, "gpa_scale": 4.0,
         "home_state": "NY", "intended_major": "Psychology", "hooks": ["none"], "activities": [],
         "essay": e("essay_5"),
         "college_list": ["New York University", "Boston University", "Rutgers University-New Brunswick", "Tufts University"]},
    ]


if __name__ == "__main__":
    import sys
    r = run(demo_students()[0], use_model="--model" in sys.argv)
    for s in r["steps"]:
        print(f"{s['step']:9} {s['ms']:6} ms  {s['by']:28} {s['what']}")
    print()
    for c in r["colleges"]:
        cs = c.get("cases") or {}
        nat, own = (cs.get("national") or {}), (cs.get("own") or {})
        print(f"{c['name'][:44]:44} {c['label']['text']:18} national {nat.get('status', '-'):10} n={nat.get('n', '-')!s:4} own {own.get('status', '-'):10} n={own.get('n', '-')}")
    print()
    print("balance:", json.dumps(r["balance"].get("counts")), [w.get("id") for w in r["balance"].get("warnings", [])])
    print("privacy:", r["privacy"]["note"], "| reader:", r["reader"].get("status"), "| prism:", r["prism"]["status"])
