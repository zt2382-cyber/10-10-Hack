"""Acceptance run: the hand-written answer sheet plus whole-system checks.

Run from the repo root:  python tests\\acceptance\\run_acceptance.py
Exit code: 0 only when 60 of 60 cells match and no whole-system check fails; 1 otherwise; 2 when
engine.labels is missing.

Standard library only. Written without reading engine/labels.py, engine/cases.py or engine/balance.py.
Assumption (CONTRACT.md does not give the signature): engine.pipeline.run(student_input: dict) -> Result dict.
"""
from __future__ import annotations

import contextlib
import csv
import glob
import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

OUT = io.StringIO()


def say(line: str = "") -> None:
    print(line)
    OUT.write(line + "\n")


def _int(x):
    x = (x or "").strip()
    return int(x) if x else None


def student_for(sid: str, sat, act) -> dict:
    return {"label": f"{sid} (SYNTHETIC)", "sat": sat, "act": act, "gpa": None, "gpa_scale": None,
            "home_state": None, "intended_major": None, "hooks": [], "activities": [], "essay": "",
            "college_list": []}


def run_sheet(label_college, find_college) -> tuple[int, int]:
    with open(HERE / "answer_sheet.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    mism = []
    for r in rows:
        stu = student_for(r["student_id"], _int(r["sat"]), _int(r["act"]))
        college = find_college(r["college"])
        try:
            lab = label_college(stu, college)
            got_state, got_rule = lab.get("state"), lab.get("rule_id")
        except Exception as e:  # a crash is a mismatch, not a stop
            got_state, got_rule = f"ERROR {type(e).__name__}: {e}", None
        if got_state != r["expected_state"] or got_rule != r["expected_rule_id"]:
            mism.append((r, got_state, got_rule))
    if mism:
        say("MISMATCHES")
        say(f"{'student':<7} {'college':<34} {'expected':<24} {'got':<24} working")
        for r, gs, gr in mism:
            exp = f"{r['expected_state']}/{r['expected_rule_id']}"
            got = f"{gs}/{gr}"
            say(f"{r['student_id']:<7} {r['college'][:34]:<34} {exp:<24} {got:<24} {r['working']}")
        say("")
    n_ok = len(rows) - len(mism)
    say(f"ACCEPTANCE: {n_ok} of {len(rows)} match the hand-written sheet")
    return n_ok, len(rows)


# ---------------------------------------------------------------- whole-system checks
BANNED = ["chance of", "probability", "odds of", "% chance", "likely to get in"]
NEGATION = re.compile(r"\b(no|not|never|without|n't)\b[^.]{0,60}\b(chance|probability|odds)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}|\b\d{3}[-.\s]\d{4}\b")


def walk_strings(obj, path="$"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")


def walk_dicts(obj, path="$"):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk_dicts(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from walk_dicts(v, f"{path}[{i}]")


def clear_keys():
    for k in ("NICRRON_API_KEY", "NICRRON_KEY_FILE", "PRISM_API_KEY", "PRISM_KEY_FILE", "PRISM_SEND"):
        os.environ.pop(k, None)


def base_input(essay: str) -> dict:
    return {"label": "Check student (SYNTHETIC)", "sat": 1450, "act": None, "gpa": 3.9, "gpa_scale": 4.0,
            "home_state": "NJ", "intended_major": "Computer Science", "hooks": ["first_gen"],
            "activities": [{"type": "Research", "role": "Student researcher", "description": "Lab work"}],
            "essay": essay,
            "college_list": ["Cornell University", "University of Michigan-Ann Arbor",
                             "Rutgers University-New Brunswick", "Purdue University-Main Campus",
                             "University of Lynchburg", "Example College Not In File"]}


def pipeline_runner():
    try:
        from engine import pipeline  # noqa: WPS433
    except ImportError as e:
        return None, f"engine.pipeline not importable ({e})"
    except Exception as e:
        return None, f"engine.pipeline failed on import ({type(e).__name__}: {e})"
    if not hasattr(pipeline, "run"):
        return None, "engine.pipeline has no run()"
    return pipeline.run, ""


def quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def check_banned(results):
    bad = []
    allowed = 0
    for name, res in results.items():
        for path, s in walk_strings(res):
            low = s.lower()
            hits = [b for b in BANNED if b in low]
            if not hits:
                continue
            if path.startswith("$.refusals") or NEGATION.search(s):
                allowed += 1
                continue
            bad.append(f"{name} {path}: {hits} in {s[:80]!r}")
    return bad, allowed


def check_pools(results):
    bad = []
    checked = 0
    for name, res in results.items():
        for path, d in walk_dicts(res):
            n, st = d.get("n"), d.get("status")
            if isinstance(n, int) and not isinstance(n, bool) and "status" in d and st in (
                    "ok", "not_enough", "none"):
                checked += 1
                if n < 15 and st == "ok":
                    bad.append(f"{name} {path}: n={n} status=ok")
                if n >= 15 and st != "ok":
                    bad.append(f"{name} {path}: n={n} status={st} (needs ok at 15 or more)")
                if n == 0 and st != "none":
                    bad.append(f"{name} {path}: n=0 status={st} (needs none)")
    return bad, checked


def label_view(res):
    out = {}
    for c in res.get("colleges", []) or []:
        out[str(c.get("name"))] = c.get("label")
    return out


def main() -> int:
    say(f"Acceptance run {datetime.now().isoformat(timespec='seconds')} (repo {ROOT})")
    try:
        from engine.labels import label_college
    except ImportError as e:
        say(f"engine.labels.label_college is missing ({e}). Cannot run the answer sheet.")
        say("ACCEPTANCE: 0 of 60 match the hand-written sheet (not run)")
        (HERE / "last_run.txt").write_text(OUT.getvalue(), encoding="utf-8")
        return 2
    from engine.colleges import find_college

    n_ok, total = run_sheet(label_college, find_college)
    say("")
    say("WHOLE-SYSTEM CHECKS")
    fails = 0

    clear_keys()  # model reader and PRISM stay off
    run, why = pipeline_runner()
    essays = sorted(glob.glob(str(ROOT / "data" / "synthetic" / "SYNTHETIC_essay_*.txt")))
    names = ["no banned wording anywhere in a Result", "pools under 15 are not_enough or none",
             "labels identical across the five essays", "injection essay is blocked",
             "personal details of essay 5 absent from Result", "same input twice gives same colleges and balance"]

    if run is None or len(essays) < 5:
        reason = why or f"only {len(essays)} essay files found"
        for nme in names:
            say(f"SKIPPED  {nme}  ({reason})")
        return finish(n_ok, total, fails)

    results = {}
    errors = {}
    for p in essays:
        key = Path(p).name
        text = Path(p).read_text(encoding="utf-8")
        try:
            results[key] = quiet(run, base_input(text))
        except Exception as e:
            errors[key] = f"{type(e).__name__}: {e}"
    if errors:
        for k, v in errors.items():
            say(f"FAIL     pipeline.run raised for {k}: {v}")
        fails += 1
    if not results:
        for nme in names:
            say(f"SKIPPED  {nme}  (pipeline.run raised for every essay)")
        return finish(n_ok, total, fails)

    # 1 banned wording
    bad, allowed = check_banned(results)
    if bad:
        fails += 1
        say(f"FAIL     {names[0]}")
        for b in bad[:10]:
            say(f"           {b}")
    else:
        say(f"PASS     {names[0]} ({len(results)} Results searched; {allowed} refusal/negation sentences allowed)")

    # 2 pools
    bad, checked = check_pools(results)
    if bad:
        fails += 1
        say(f"FAIL     {names[1]}")
        for b in bad[:10]:
            say(f"           {b}")
    elif checked == 0:
        say(f"SKIPPED  {names[1]}  (no case pools found in the Result; engine.cases not wired in)")
    else:
        say(f"PASS     {names[1]} ({checked} pools checked)")

    # 3 labels identical across essays
    views = {k: label_view(r) for k, r in results.items()}
    first_k = next(iter(views))
    ref = views[first_k]
    diff = [k for k, v in views.items() if v != ref]
    if not ref or all(v is None for v in ref.values()):
        say(f"SKIPPED  {names[2]}  (Result has no colleges[].label)")
    elif diff:
        fails += 1
        say(f"FAIL     {names[2]}: differs from {first_k}: {diff}")
    else:
        say(f"PASS     {names[2]} ({len(ref)} colleges x {len(views)} essays)")

    # 4 injection essay
    k4 = next((k for k in results if "_4_" in k), None)
    if k4 is None:
        say(f"SKIPPED  {names[3]}  (essay 4 not in results)")
    else:
        blocked = (results[k4].get("privacy") or {}).get("blocked")
        if blocked is True:
            say(f"PASS     {names[3]}")
        else:
            fails += 1
            say(f"FAIL     {names[3]} (privacy.blocked = {blocked!r})")

    # 5 personal details of essay 5
    k5 = next((k for k in results if "_5_" in k), None)
    if k5 is None:
        say(f"SKIPPED  {names[4]}  (essay 5 not in results)")
    else:
        text5 = Path(next(p for p in essays if Path(p).name == k5)).read_text(encoding="utf-8")
        found = set(EMAIL.findall(text5)) | set(PHONE.findall(text5))
        found = {f.strip() for f in found}
        norm = lambda s: re.sub(r"[-.()\s+]", "", s)
        leaks = []
        for path, s in walk_strings(results[k5]):
            for f in found:
                if f in s or (len(norm(f)) >= 7 and norm(f) in norm(s)):
                    leaks.append(f"{path} contains {f!r}")
        if leaks:
            fails += 1
            say(f"FAIL     {names[4]}")
            for b in leaks[:10]:
                say(f"           {b}")
        else:
            say(f"PASS     {names[4]} ({len(found)} emails/phone numbers looked for: "
                f"{len([f for f in found if '@' in f])} email, {len([f for f in found if '@' not in f])} phone)")

    # 6 determinism
    try:
        a = quiet(run, base_input(""))
        b = quiet(run, base_input(""))
        same = all(json.dumps(a.get(s), sort_keys=True, default=str) ==
                   json.dumps(b.get(s), sort_keys=True, default=str) for s in ("colleges", "balance"))
        if same:
            say(f"PASS     {names[5]}")
        else:
            fails += 1
            say(f"FAIL     {names[5]}")
    except Exception as e:
        fails += 1
        say(f"FAIL     {names[5]} (pipeline.run raised {type(e).__name__}: {e})")

    return finish(n_ok, total, fails)


def finish(n_ok, total, fails) -> int:
    say("")
    code = 0 if (n_ok == total and fails == 0) else 1
    say(f"EXIT {code}: sheet {n_ok}/{total}, whole-system failures {fails}")
    (HERE / "last_run.txt").write_text(OUT.getvalue(), encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
