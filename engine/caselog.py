"""The counselor's own finished cases: add one, import a spreadsheet, load them all.

Plain files, no model needed. A model may only help to guess what an unfamiliar column header means
(`map_headers_with_model`); code checks every guess. Anything that looks like a name, email, phone number
or date of birth is refused or dropped, because privacy is the point of this tool.

Store: data/local/school_cases.csv, created on first use by copying data/synthetic/SYNTHETIC_school_cases.csv.
The store path can be changed with `set_store_path(path)` or the environment variable COUNSELOR_CASES_PATH.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import shutil
import sys
from pathlib import Path

try:
    from engine import colleges as _colleges
except Exception:  # pragma: no cover - the module must import even if siblings are absent
    _colleges = None
try:
    from engine import privacy as _privacy
except Exception:  # pragma: no cover
    _privacy = None

ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_PATH = ROOT / "data" / "synthetic" / "SYNTHETIC_school_cases.csv"
DEFAULT_STORE = ROOT / "data" / "local" / "school_cases.csv"

FIELDS = ["case_id", "cycle_year", "sat", "act", "gpa", "major_group", "hooks", "home_state",
          "activities_note", "essay_theme", "college", "outcome", "verified_by"]
STORE_COLUMNS = ["synthetic"] + FIELDS
# Fields a spreadsheet column may be mapped to (case_id and verified_by are assigned by code).
MAPPABLE = ["cycle_year", "sat", "act", "gpa", "major_group", "hooks", "home_state",
            "activities_note", "essay_theme", "college", "outcome"]
MAJOR_GROUPS = ["CS", "ENG", "BIO", "PREMED", "BUSINESS", "POLISCI", "PSYCH", "MATH", "PHYSICS",
                "ECON", "HUMANITIES", "ARTS", "OTHER"]
HOOK_VALUES = ["none", "first_gen", "legacy", "urm", "recruited_athlete"]
OUTCOMES = ["admitted", "denied", "waitlisted"]
STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
             "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())

_store_override: Path | None = None


# ---------------------------------------------------------------- store path

def set_store_path(path) -> None:
    """Point the store somewhere else (tests use a temporary folder). None goes back to the default."""
    global _store_override
    _store_override = Path(path) if path else None


def store_path() -> Path:
    if _store_override is not None:
        return _store_override
    env = os.environ.get("COUNSELOR_CASES_PATH")
    return Path(env) if env else DEFAULT_STORE


def _ensure_store() -> Path:
    p = store_path()
    if p.exists():
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    if not SYNTHETIC_PATH.exists():
        make_synthetic()
    shutil.copyfile(SYNTHETIC_PATH, p)
    return p


# ---------------------------------------------------------------- small parsers

def _clean(v) -> str:
    return "" if v is None else str(v).strip()


def _to_number(v):
    """'1,450', '1450 (superscore)', 1450.0 -> 1450.0. Blank, '-', 'n/a' -> None. Raises ValueError otherwise."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return None if (isinstance(v, float) and math.isnan(v)) else float(v)
    s = str(v).strip().replace(",", "")
    if s == "" or s.lower() in {"-", "--", "n/a", "na", "none", "null", "unknown", "?", "-1"}:
        return None
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        raise ValueError(s)
    return float(m.group(0))


def normalize_outcome(v) -> str | None:
    s = _clean(v).lower()
    if not s:
        return None
    toks = set(re.findall(r"[a-z]+", s))
    if toks & {"wl", "waitlist", "waitlisted", "wait"}:
        return "waitlisted"
    if toks & {"rejected", "reject", "deny", "denied", "denial", "rej"}:
        return "denied"
    if toks & {"accepted", "accept", "admit", "admitted", "admission", "acc"}:
        return "admitted"
    return None


def normalize_hooks(v) -> str | None:
    """Returns hooks as ';'-joined lowercase values, or None when something is not understood."""
    if v is None:
        return "none"
    items = v if isinstance(v, (list, tuple)) else re.split(r"[;,/|]", str(v))
    out = []
    for it in items:
        s = re.sub(r"[^a-z]+", "", str(it).lower())
        if s in ("", "none", "na", "nohook", "nohooks"):
            continue
        mapped = {"firstgen": "first_gen", "firstgeneration": "first_gen", "legacy": "legacy", "urm": "urm",
                  "recruitedathlete": "recruited_athlete", "athlete": "recruited_athlete"}.get(s)
        if not mapped:
            return None
        if mapped not in out:
            out.append(mapped)
    return ";".join(out) if out else "none"


def _major_group(v) -> str | None:
    s = _clean(v)
    if not s:
        return None
    if s.upper() in MAJOR_GROUPS:
        return s.upper()
    try:
        from engine import cases as _cases
        g = _cases.major_group_for(s)
    except Exception:
        g = None
    return g or "OTHER"


# ---------------------------------------------------------------- privacy checks

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,2}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
_DOB = [
    re.compile(r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:\d{4}|\d{2})\b"),
    re.compile(r"\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\b(?:%s)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+(?:19|20)\d{2}\b" % _MONTHS, re.I),
    re.compile(r"\b(?:dob|date of birth|born on|birthday|birthdate|birth date)\b", re.I),
]
_NAME_VALUE = re.compile(r"\bmy name is\b|\bname\s*:", re.I)

_CONTACT_TOKENS = {"email", "mail", "phone", "mobile", "cell", "tel", "telephone", "address", "street", "dob",
                   "birth", "birthday", "birthdate", "ssn", "zip", "postal", "contact", "parent", "guardian",
                   "mom", "dad", "mother", "father"}
_NAME_TOKENS = {"name", "names", "firstname", "lastname", "fullname", "surname", "fname", "lname", "nickname",
                "middlename", "givenname", "familyname"}
_COLLEGE_TOKENS = {"college", "university", "institution", "campus", "school"}


def _tokens(key: str) -> list[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(key))
    return re.findall(r"[a-z]+", spaced.lower())


def sensitive_key_kind(key: str) -> str | None:
    """'name' or 'contact' when a field or column name looks like it holds personal details, else None."""
    toks = _tokens(key)
    s = set(toks)
    if not s:
        return None
    if s & _CONTACT_TOKENS:
        return "contact"
    if s & _NAME_TOKENS:
        # "college name" / "school name" is a place, "high school name" is not worth keeping.
        if s & _COLLEGE_TOKENS and "high" not in s and not (s & {"first", "last", "full", "student", "parent"}):
            return None
        return "name"
    if toks in (["student"], ["applicant"], ["person"], ["who"]):
        return "name"
    return None


def sensitive_value_kind(value) -> str | None:
    """'email', 'phone', 'date of birth' or 'name' when text looks like personal details, else None."""
    if not isinstance(value, str):
        return None
    if _EMAIL.search(value):
        return "email"
    if any(p.search(value) for p in _DOB):
        return "date of birth"
    if _PHONE.search(value):
        return "phone"
    if _NAME_VALUE.search(value):
        return "name"
    return None


_FREE_TEXT_FIELDS = ("activities_note", "essay_theme")
_FREE_TEXT_LABEL = {"activities_note": "activities note", "essay_theme": "essay theme"}


def _free_text_problem(case: dict):
    """Plain-words reason when a free-text field carries a personal detail, else None. Fails closed: if the
    shared privacy check is unavailable, free text is refused."""
    for field in _FREE_TEXT_FIELDS:
        val = case.get(field)
        if val is None or _clean(val) == "":
            continue
        if _privacy is None:
            return "The privacy check is not available, so free text in '%s' cannot be stored." % field
        kinds = _privacy.looks_personal(_clean(val))
        if kinds:
            what = ", ".join("an instruction to an AI" if k == "instruction" else k for k in kinds)
            return ("The %s looks like it contains personal details (%s). This tool does not store names, "
                    "schools, addresses, emails, phone numbers or dates of birth. Remove them and try again."
                    % (_FREE_TEXT_LABEL[field], what))
    return None


def _num_text(v, as_float=False):
    try:
        if _clean(v) == "":
            return ""
        return "%.2f" % float(v) if as_float else str(int(round(float(v))))
    except (TypeError, ValueError):
        return _clean(v)


def fingerprint(case: dict) -> str:
    """A stable identity for a case's contents (never its case_id, provenance or who verified it)."""
    import hashlib
    parts = [_num_text(case.get("cycle_year")), _num_text(case.get("sat")), _num_text(case.get("act")),
             _num_text(case.get("gpa"), True), _clean(case.get("major_group")).upper(),
             ";".join(sorted(x for x in _clean(case.get("hooks") or "none").lower().split(";") if x)),
             _clean(case.get("home_state")).upper(), " ".join(_clean(case.get("activities_note")).lower().split()),
             " ".join(_clean(case.get("essay_theme")).lower().split()), _clean(case.get("college")).lower(),
             _clean(case.get("outcome")).lower()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


# ---------------------------------------------------------------- validation

def _validate(case: dict):
    """Returns (clean_case_without_id, None) or (None, plain-words error)."""
    if not isinstance(case, dict):
        return None, "A case must be a set of named fields."
    for key in case:
        kind = sensitive_key_kind(key)
        if kind:
            return None, ("The field '%s' looks like a person's %s. This tool does not store names or contact "
                          "details. Remove it and try again." % (key, "name" if kind == "name" else "contact detail"))
    for key, val in case.items():
        kind = sensitive_value_kind(val)
        if kind:
            return None, ("The value in '%s' looks like a %s. This tool does not store emails, phone numbers, "
                          "dates of birth or names. Remove it and try again." % (key, kind))

    problem = _free_text_problem(case)
    if problem:
        return None, problem

    out = {}
    college_in = _clean(case.get("college"))
    if not college_in:
        return None, "A college is required."
    col = _colleges.find_college(college_in) if _colleges else None
    if col is None:
        return None, "The college '%s' is not in the 300-college file, so it cannot be added." % college_in
    out["college"] = col["name"]

    outcome = normalize_outcome(case.get("outcome"))
    if outcome is None:
        return None, "The outcome must be admitted, denied or waitlisted."
    out["outcome"] = outcome

    def number(field, lo, hi, as_int):
        try:
            v = _to_number(case.get(field))
        except ValueError:
            return None, "%s must be a number." % field.upper()
        if v is None:
            return "", None
        if not (lo <= v <= hi):
            return None, "%s %s is outside the allowed range of %s to %s." % (
                field.upper() if field != "cycle_year" else "Cycle year", case.get(field), lo, hi)
        return (int(round(v)) if as_int else round(v, 2)), None

    for field, lo, hi, as_int in (("sat", 400, 1600, True), ("act", 1, 36, True), ("gpa", 0, 5, False),
                                  ("cycle_year", 2000, 2035, True)):
        val, err = number(field, lo, hi, as_int)
        if err:
            return None, err
        out[field] = val

    mg = _major_group(case.get("major_group"))
    out["major_group"] = mg or ""

    hooks = normalize_hooks(case.get("hooks"))
    if hooks is None:
        return None, "Hooks must be from: none, first_gen, legacy, urm, recruited_athlete."
    out["hooks"] = hooks

    st = _clean(case.get("home_state")).upper()
    if st in ("", "-1"):
        out["home_state"] = ""
    elif st in STATES or st == "INTERNATIONAL":
        out["home_state"] = st
    else:
        return None, "The home state '%s' is not a two-letter US state code." % case.get("home_state")

    out["activities_note"] = _clean(case.get("activities_note"))[:300]
    out["essay_theme"] = _clean(case.get("essay_theme"))[:200]
    out["verified_by"] = _clean(case.get("verified_by")) or "counselor"
    out["synthetic"] = "SYNTHETIC" if _clean(case.get("synthetic")).upper() == "SYNTHETIC" else ""
    return out, None


# ---------------------------------------------------------------- reading and writing the store

def _typed(row: dict) -> dict:
    def i(v):
        try:
            return int(round(float(v))) if _clean(v) != "" else None
        except ValueError:
            return None

    def f(v):
        try:
            return float(v) if _clean(v) != "" else None
        except ValueError:
            return None

    return {
        "case_id": _clean(row.get("case_id")),
        "cycle_year": i(row.get("cycle_year")),
        "sat": i(row.get("sat")),
        "act": i(row.get("act")),
        "gpa": f(row.get("gpa")),
        "major_group": _clean(row.get("major_group")) or None,
        "hooks": _clean(row.get("hooks")) or "none",
        "home_state": _clean(row.get("home_state")) or None,
        "activities_note": _clean(row.get("activities_note")),
        "essay_theme": _clean(row.get("essay_theme")),
        "college": _clean(row.get("college")),
        "outcome": _clean(row.get("outcome")),
        "verified_by": _clean(row.get("verified_by")) or "counselor",
        "synthetic": _clean(row.get("synthetic")),
    }


def _read_raw() -> list[dict]:
    p = _ensure_store()
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_cases() -> list[dict]:
    """Every finished case in the counselor's store (created from the SYNTHETIC file on first use)."""
    return [_typed(r) for r in _read_raw()]


def _next_id_number(rows: list[dict]) -> int:
    best = 0
    for r in rows:
        m = re.fullmatch(r"S-(\d+)", _clean(r.get("case_id")))
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


def count_cases() -> int:
    """How many cases are in the store (the store is created from the invented demo file on first use)."""
    return len(_read_raw())


def reset_demo() -> int:
    """Remove every row marked DEMO (made by a demo action). Returns how many were removed."""
    p = _ensure_store()
    rows = _read_raw()
    keep = [r for r in rows if _clean(r.get("synthetic")).upper() != "DEMO"]
    removed = len(rows) - len(keep)
    if removed:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=STORE_COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(keep)
    return removed


def _append(clean_cases: list[dict], mark: str | None = None) -> list[dict]:
    p = _ensure_store()
    rows = _read_raw()
    n = _next_id_number(rows)
    stored = []
    with open(p, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=STORE_COLUMNS, extrasaction="ignore")
        # make sure we start on a fresh line
        if p.stat().st_size and not _ends_with_newline(p):
            fh.write("\n")
        for c in clean_cases:
            row = dict(c)
            row["case_id"] = "S-%d" % n
            row["synthetic"] = mark if mark is not None else (c.get("synthetic") or "")
            n += 1
            w.writerow(row)
            stored.append(_typed(row))
    return stored


def _ends_with_newline(p: Path) -> bool:
    with open(p, "rb") as fh:
        fh.seek(-1, os.SEEK_END)
        return fh.read(1) in (b"\n", b"\r")


def add_case(case: dict, demo: bool = False) -> dict:
    """Validate and store one finished case. Returns the stored case, or {"error": "plain words"}.
    A case is real unless the caller passes synthetic="SYNTHETIC"; demo=True stores it as DEMO (invented)."""
    clean, err = _validate(case)
    if err:
        return {"error": err}
    return _append([clean], "DEMO" if demo else None)[0]


# ---------------------------------------------------------------- spreadsheet import

# (field, words that mark it, words that rule it out). Checked in this order; first match wins.
_HEADER_RULES = [
    ("college", {"college", "university", "institution", "campus", "school", "applied"}, {"high", "type", "year"}),
    ("outcome", {"decision", "result", "outcome", "admitted", "accepted", "admission", "status"}, set()),
    ("cycle_year", {"year", "cycle", "class"}, set()),
    ("sat", {"sat"}, {"math", "ebrw", "verbal", "reading", "writing", "evidence", "section", "subscore", "subject"}),
    ("act", {"act"}, {"math", "english", "science", "reading", "writing", "subscore"}),
    ("gpa", {"gpa", "grade"}, set()),
    ("major_group", {"major", "intended", "field", "program", "study"}, set()),
    ("hooks", {"hook", "hooks", "legacy", "urm", "firstgen", "athlete"}, set()),
    ("home_state", {"state", "residence", "residency"}, set()),
    ("activities_note", {"activities", "activity", "extracurricular", "extracurriculars", "ec", "ecs"}, set()),
    ("essay_theme", {"essay", "theme", "topic"}, set()),
]


def map_header(header: str) -> str | None:
    """Keyword table: one spreadsheet column title -> a case field, or None when it cannot be placed."""
    toks = set(_tokens(header))
    joined = "".join(_tokens(header))
    if "first" in toks and ("gen" in toks or "generation" in toks):
        toks.add("firstgen")
    if joined == "firstgen":
        toks.add("firstgen")
    if re.match(r"(sat|act)(total|score|composite|combined|superscore)", joined):
        toks.add(joined[:3])
    for field, words, excluded in _HEADER_RULES:
        if toks & words and not (toks & excluded):
            return field
    return None


def map_headers_with_model(headers):
    """Ask a model to place column titles the keyword table could not. Returns {header: field or None}, or None
    when the model helper is missing, has no key, or fails. Only the titles are sent, never any row values.
    Code checks every answer: a target that is not a real case field is thrown away."""
    headers = [h for h in (headers or []) if _clean(h)]
    if not headers:
        return {}
    try:
        import importlib
        nicrron = importlib.import_module("engine.nicrron")  # lazy: this module works without it
    except Exception:
        return None
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"mapping": {"type": "object", "additionalProperties": {"type": ["string", "null"]}}},
              "required": ["mapping"]}
    system = ("You match spreadsheet column titles to fields of a college-admissions case record. "
              "Allowed fields: %s. For each title answer one allowed field, or null if none fits. "
              "Answer only JSON: {\"mapping\": {title: field_or_null}}." % ", ".join(MAPPABLE))
    try:
        res = nicrron.chat([{"role": "system", "content": system},
                            {"role": "user", "content": json.dumps(headers)}],
                           json_schema=schema, max_tokens=900)
    except Exception:
        return None
    if not isinstance(res, dict) or not res.get("ok"):
        return None
    data = res.get("json")
    if not isinstance(data, dict):
        try:
            data = json.loads(res.get("text") or "")
        except Exception:
            return None
    mapping = data.get("mapping", data) if isinstance(data, dict) else None
    if not isinstance(mapping, dict):
        return None
    out = {}
    for h in headers:
        target = mapping.get(h)
        out[h] = target if target in MAPPABLE else None
    return out


def _read_csv_rows(path):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=enc, newline="") as fh:
                reader = csv.reader(fh)
                rows = list(reader)
            return rows
        except UnicodeDecodeError:
            continue
    raise ValueError("The file could not be read as text.")


def import_csv(path, demo: bool = False) -> dict:
    """Add many cases from a spreadsheet saved as CSV, with whatever column titles it has.
    Importing the same rows again adds nothing: a row whose contents (not its id) are already stored is skipped
    and counted in "skipped_duplicates". Rows are real unless demo=True (stored as DEMO).
    Returns {"added", "skipped_duplicates", "rejected": [{"row", "reason"}], "dropped_columns", "mapped_columns", "unmapped_columns",
    "mapped_by_model"}; an unreadable file returns the same keys plus "error"."""
    result = {"added": 0, "skipped_duplicates": 0, "rejected": [], "dropped_columns": [], "mapped_columns": {}, "unmapped_columns": [],
              "mapped_by_model": []}
    try:
        rows = _read_csv_rows(path)
    except (OSError, ValueError) as e:
        result["error"] = "Could not read that file: %s" % e
        return result
    if not rows:
        result["error"] = "The file is empty."
        return result
    headers = [_clean(h) for h in rows[0]]
    col_field: dict[int, str] = {}
    for i, h in enumerate(headers):
        if not h:
            continue
        if sensitive_key_kind(h):
            result["dropped_columns"].append(h)
            continue
        f = map_header(h)
        if f and f not in col_field.values():
            col_field[i] = f
            result["mapped_columns"][h] = f
        else:
            result["unmapped_columns"].append(h)

    # A model may help with titles the table could not place (titles only; code validates).
    if result["unmapped_columns"]:
        guess = map_headers_with_model(result["unmapped_columns"])
        if guess:
            for h, f in guess.items():
                if f and f in MAPPABLE and f not in col_field.values() and h in headers:
                    col_field[headers.index(h)] = f
                    result["mapped_columns"][h] = f
                    result["mapped_by_model"].append(h)
            result["unmapped_columns"] = [h for h in result["unmapped_columns"] if h not in result["mapped_columns"]]

    if "college" not in col_field.values() or "outcome" not in col_field.values():
        result["error"] = ("Could not find a college column and an outcome (decision) column in this file, "
                           "so nothing was added.")
        return result

    good = []
    try:
        seen = {fingerprint(r) for r in load_cases()}
    except Exception:
        seen = set()
    for rno, row in enumerate(rows[1:], start=2):
        if not any(_clean(c) for c in row):
            continue
        case = {col_field[i]: row[i] for i in col_field if i < len(row)}
        clean, err = _validate(case)
        if err:
            result["rejected"].append({"row": rno, "reason": err})
        else:
            fp = fingerprint(clean)
            if fp in seen:
                result["skipped_duplicates"] += 1
                continue
            seen.add(fp)
            good.append(clean)
    if good:
        _append(good, "DEMO" if demo else None)
    result["added"] = len(good)
    return result


# ---------------------------------------------------------------- the invented school (seeded, reproducible)
# One imaginary New Jersey public high school, cycles 2021 to 2026. Nothing here is a real student.

_SYN_COLLEGES = [  # (Scorecard name, weight): where such a school really sends students; a few very selective rows
    ("Rutgers University-New Brunswick", 24), ("Pennsylvania State University-Main Campus", 11),
    ("Boston University", 8), ("Purdue University-Main Campus", 8), ("Northeastern University", 7),
    ("New York University", 7), ("Virginia Polytechnic Institute and State University", 6),
    ("Cornell University", 6), ("Binghamton University", 5), ("University of Delaware", 4),
    ("University of Maryland-College Park", 4), ("Montclair State University", 3),
    ("University of Michigan-Ann Arbor", 2), ("Georgia Institute of Technology-Main Campus", 2),
    ("Carnegie Mellon University", 1.5), ("University of Pennsylvania", 1), ("Princeton University", 0.7),
    ("Columbia University in the City of New York", 0.7),
]
# (college, student SAT the demo will look for): each must have at least _SYN_MIN_FOCAL cases within 100 points.
_SYN_FOCAL = [
    ("Rutgers University-New Brunswick", 1450), ("Purdue University-Main Campus", 1450), ("Cornell University", 1450),
    ("Rutgers University-New Brunswick", 1250), ("Pennsylvania State University-Main Campus", 1250),
    ("Boston University", 1250),
]
_SYN_MIN_FOCAL = 20
_SYN_NOTES = ["Robotics club captain", "Summer research at a university lab", "Varsity soccer", "Part-time job at a grocery store",
              "Volunteer tutor for younger students", "School orchestra first chair", "Debate team", "Coding club founder",
              "Hospital volunteer", "Theater stage crew", "Cares for younger siblings after school", "Student newspaper editor",
              "Model UN delegate", "Art portfolio and school gallery show", "Church youth group leader", "Math team",
              "Varsity track", "Food pantry volunteer", "Family business helper", "Science Olympiad"]
_SYN_THEMES = ["family", "persistence", "curiosity", "immigration", "community", "leadership", "identity",
               "creativity", "mentorship", "resilience", "service", "first-generation experience"]
_SYN_MAJORS = [("CS", 30), ("ENG", 20), ("BIO", 12), ("BUSINESS", 12), ("PREMED", 6), ("POLISCI", 5), ("PSYCH", 5),
               ("MATH", 4), ("HUMANITIES", 3), ("ARTS", 3)]
_SYN_HOOKS = [("none", 70), ("first_gen", 14), ("urm", 8), ("legacy", 5), ("recruited_athlete", 3)]
_SYN_STATES = [("NJ", 95), ("NY", 2), ("PA", 2), ("DE", 1)]


def _wchoice(rng, pairs):
    total = sum(w for _, w in pairs)
    x = rng.random() * total
    for item, w in pairs:
        x -= w
        if x <= 0:
            return item
    return pairs[-1][0]


def _sat_to_act(sat):
    best, gap = None, 10 ** 6
    for act in range(12, 37):
        s = _colleges.act_to_sat(act)
        if s is not None and abs(s - sat) < gap:
            best, gap = act, abs(s - sat)
    return best


def make_synthetic(path=None, seed: int = 20261010, n_rows: int = 720) -> Path:
    """Write the invented school's finished cases (about 720 over 18 colleges). Same seed, same file."""
    path = Path(path) if path else SYNTHETIC_PATH
    rng = random.Random(seed)
    roster = []
    for name, weight in _SYN_COLLEGES:
        c = _colleges.find_college(name)
        if c and c["admit_rate"] and c["sat25"] and c["sat75"]:
            roster.append((c, weight))
    by_name = {c["name"]: c for c, _ in roster}
    rows = []

    def decide(c, sat):
        mid = (c["sat25"] + c["sat75"]) / 2.0
        half = max(40.0, (c["sat75"] - c["sat25"]) / 2.0)
        z = max(-2.0, min(2.0, (sat - mid) / half))
        rate = min(0.97, max(0.02, c["admit_rate"]))
        logit = math.log(rate / (1 - rate)) + 1.4 * z
        p = min(0.97, max(0.01, 1 / (1 + math.exp(-logit))))
        if rng.random() < p:
            return "admitted"
        wl = 0.15 if rate < 0.5 else 0.04
        return "waitlisted" if rng.random() < wl else "denied"

    def new_student(sat=None, sat_only=False):
        if sat is None:
            r = rng.random()
            mean, sd = (1250, 120) if r < 0.5 else ((1450, 70) if r < 0.85 else (1100, 100))
            sat = int(round(min(1590, max(900, rng.gauss(mean, sd))) / 10.0) * 10)
        gpa = round(min(4.0, max(2.6, 3.55 + (sat - 1270) / 700.0 + rng.gauss(0, 0.2))), 2)
        mode = 0.0 if sat_only else rng.random()  # SAT only / ACT only / both
        return {"sat": sat, "gpa": gpa, "major": _wchoice(rng, _SYN_MAJORS), "hook": _wchoice(rng, _SYN_HOOKS),
                "state": _wchoice(rng, _SYN_STATES), "cycle": rng.choice([2021, 2022, 2023, 2024, 2025, 2026]),
                "notes": "; ".join(rng.sample(_SYN_NOTES, rng.choice([1, 2]))), "theme": rng.choice(_SYN_THEMES),
                "show_sat": mode < 0.72 or mode >= 0.9, "show_act": mode >= 0.72}

    def emit(st, c):
        rows.append({"synthetic": "SYNTHETIC", "case_id": "S-%d" % (len(rows) + 1), "cycle_year": st["cycle"],
                     "sat": st["sat"] if st["show_sat"] else "",
                     "act": _sat_to_act(st["sat"]) if st["show_act"] else "", "gpa": st["gpa"],
                     "major_group": st["major"], "hooks": st["hook"], "home_state": st["state"],
                     "activities_note": st["notes"], "essay_theme": st["theme"], "college": c["name"],
                     "outcome": decide(c, st["sat"]), "verified_by": "counselor"})

    def organic(limit):
        while len(rows) < limit:
            st = new_student()
            weights = []
            for c, w in roster:
                mid = (c["sat25"] + c["sat75"]) / 2.0
                weights.append((c, w * math.exp(-0.5 * ((st["sat"] - mid) / 250.0) ** 2)))
            for _ in range(rng.choice([2, 3, 4])):
                if len(rows) >= limit or not weights:
                    break
                c = _wchoice(rng, weights)
                weights = [(x, w) for x, w in weights if x is not c]
                emit(st, c)

    organic(max(0, n_rows - 160))
    # Guarantee enough cases near each demo score so the school's own pool can read a pattern there.
    for name, center in _SYN_FOCAL:
        c = by_name[name]
        have = sum(1 for r in rows if r["college"] == name and r["sat"] != "" and abs(int(r["sat"]) - center) <= 100)
        for _ in range(max(0, _SYN_MIN_FOCAL - have)):
            sat = int(round((center + rng.randint(-100, 100)) / 10.0) * 10)
            emit(new_student(sat=sat, sat_only=True), c)
    organic(n_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=STORE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return path


if __name__ == "__main__":
    if "--make-synthetic" in sys.argv:
        p = make_synthetic()
        n = len(list(csv.DictReader(open(p, encoding="utf-8"))))
        print("Wrote %d invented cases to %s" % (n, p))
    else:
        cs = load_cases()
        by = {}
        for c in cs:
            by.setdefault(c["college"], [0, 0, 0])
            by[c["college"]][["admitted", "denied", "waitlisted"].index(c["outcome"])] += 1
        print("Store: %s" % store_path())
        print("%d finished cases across %d colleges (admitted / denied / waitlisted):" % (len(cs), len(by)))
        for name, (a, d, w) in sorted(by.items(), key=lambda kv: -sum(kv[1])):
            print("  %-55s %2d / %2d / %2d" % (name, a, d, w))
