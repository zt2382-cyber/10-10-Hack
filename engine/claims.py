"""What each college itself says: sentences built by code from the college's own Common Data Set (CDS).

The CDS is the form a college publishes about itself. Nothing here is a model call and nothing is a prediction.
Every sentence comes from a template filled with numbers copied from one row of data/cds/cds_outcomes_sample.csv,
and is then run through check_sentence (numbers, college names, quotes, forbidden phrases, required clauses).
Fields that the row's sanity flags mark as unreliable are skipped, never guessed.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

try:  # works as `python -m engine.claims` and as `import engine.claims`
    from engine.colleges import CASE_NAME_TO_SCORECARD, DATA, find_college, load_colleges
except ImportError:  # pragma: no cover
    from .colleges import CASE_NAME_TO_SCORECARD, DATA, find_college, load_colleges  # type: ignore

CDS_DIR = DATA / "cds"
CDS_CSV = CDS_DIR / "cds_outcomes_sample.csv"
FORBIDDEN_FILE = CDS_DIR / "forbidden_phrases.txt"

REQUIRED_CAVEATS = [
    "These are the college's own published statements (its Common Data Set). They are not a prediction for any student.",
    "A rating such as Very Important is the college's own word. It does not say how much that factor counts.",
    "Test score ranges describe enrolled first-year students who submitted scores, not everyone who applied or was admitted.",
    "Admit counts cover all applicants together. They are not admit rates for any grade or score band.",
    "A field that could not be read reliably from the college's form is left out, not guessed.",
]

C7_LEVELS = {
    "Very Important": "the top of the form's four levels",
    "Important": "the second of the form's four levels",
    "Considered": "the third of the form's four levels",
    "Not Considered": "the lowest of the form's four levels",
}

# column -> (how the sentence names the factor, claim id)
C7_FACTORS = {
    "c7_essay": "the application essay",
    "c7_test_scores": "standardized test scores",
    "c7_demonstrated_interest": "demonstrated interest in the college",
    "c7_alumni": "a family link to an alumnus or alumna",
    "c7_class_rank": "class rank",
}

# belief -> C7 column
BELIEFS = [
    ("Showing interest in the college improves the result.", "c7_demonstrated_interest"),
    ("Test scores are required.", "c7_test_scores"),
    ("The essay does not matter.", "c7_essay"),
    ("Being related to a graduate helps.", "c7_alumni"),
    ("Class rank matters.", "c7_class_rank"),
]
DOES_NOT_SAY = "This college's form does not say."
UNREADABLE = "We could not read this college's rating reliably from its form, so none is shown."

# Short names used inside sentences, keyed by the CDS row id.
DISPLAY = {
    "arizona-state-university-campus-immersion": "Arizona State University",
    "georgia-tech": "Georgia Tech",
    "penn-state": "Penn State",
    "texas-am": "Texas A&M",
    "uc-berkeley": "UC Berkeley",
    "ucla": "UCLA",
    "umich": "University of Michigan",
    "mit": "MIT",
    "virginia-tech": "Virginia Tech",
    "cornell": "Cornell",
    "duke": "Duke",
    "harvard": "Harvard",
    "stanford": "Stanford",
    "yale": "Yale",
    "tufts": "Tufts",
    "northwestern": "Northwestern",
    "purdue": "Purdue",
    "university-of-washington-seattle-campus": "University of Washington",
    "university-of-virginia-main-campus": "University of Virginia",
    "university-of-minnesota-twin-cities": "University of Minnesota",
}

# Extra spellings of a college name -> CDS row id (matched after lower-casing and dropping punctuation).
ALIASES = {
    "arizona state university": "arizona-state-university-campus-immersion",
    "arizona state": "arizona-state-university-campus-immersion",
    "pennsylvania state university main campus": "penn-state",
    "penn state": "penn-state",
    "georgia tech": "georgia-tech",
    "georgia institute of technology": "georgia-tech",
    "texas a m university college station": "texas-am",
    "texas a m": "texas-am",
    "university of california berkeley": "uc-berkeley",
    "uc berkeley": "uc-berkeley",
    "berkeley": "uc-berkeley",
    "university of california los angeles": "ucla",
    "university of michigan ann arbor": "umich",
    "university of michigan": "umich",
    "michigan state university": "michigan-state-university",
    "massachusetts institute of technology": "mit",
    "virginia polytechnic institute and state university": "virginia-tech",
    "university of illinois urbana champaign": "university-of-illinois-urbana-champaign",
    "university of illinois": "university-of-illinois-urbana-champaign",
    "university of minnesota twin cities": "university-of-minnesota-twin-cities",
    "university of virginia main campus": "university-of-virginia-main-campus",
    "university of virginia": "university-of-virginia-main-campus",
    "university of washington seattle campus": "university-of-washington-seattle-campus",
    "university of washington": "university-of-washington-seattle-campus",
    "university of arizona": "university-of-arizona",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower().replace("&", " ")).strip()


# ---------------------------------------------------------------- data

def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


@lru_cache(maxsize=1)
def _rows() -> dict:
    out = {}
    with open(CDS_CSV, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["school_id"]] = r
    return out


@lru_cache(maxsize=1)
def _row_index() -> dict:
    idx = {}
    for sid, r in _rows().items():
        idx[_norm(r["school_name"])] = sid
        idx[_norm(sid)] = sid
    for alias, sid in ALIASES.items():
        if sid in _rows():
            idx[_norm(alias)] = sid
    return idx


def row_for(college) -> dict | None:
    """The CDS row for a College dict (or a name string), or None."""
    if not college:
        return None
    name = college if isinstance(college, str) else college.get("name")
    sid = _row_index().get(_norm(name or ""))
    return _rows().get(sid) if sid else None


def unmatched_rows() -> list[str]:
    """CDS rows that no Scorecard college resolves to through find_college (self-check helper)."""
    return [sid for sid, r in _rows().items() if find_college(r["school_name"]) is None]


def _flags(row: dict) -> list[str]:
    return [f for f in (row.get("sanity_flags") or "").split(";") if f]


def _year(row: dict) -> str:
    for f in _flags(row):
        m = re.match(r"year_key_[\d-]+_but_file_is_CDS_(\d{4}-\d{2})", f)
        if m:
            return m.group(1)
    return row.get("cds_year") or ""


def _display(row: dict) -> str:
    return DISPLAY.get(row["school_id"]) or row["school_name"]


def _fmt_int(v: float) -> str:
    return f"{int(round(v)):,}"


def _fmt_pct(v: float) -> str:
    """The percent exactly as the source has it (83.84 stays 83.84; 78.0 becomes 78)."""
    return f"{v:g}"


# ---------------------------------------------------------------- the checker

_FORBIDDEN_CACHE: list | None = None


def _forbidden() -> list[tuple[str, str]]:
    global _FORBIDDEN_CACHE
    if _FORBIDDEN_CACHE is None:
        items = []
        try:
            for line in FORBIDDEN_FILE.read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                phrase, _, reason = line.partition("\t")
                if phrase.strip():
                    items.append((phrase.strip().lower(), reason.strip()))
        except OSError:
            items = []
        _FORBIDDEN_CACHE = items
    return _FORBIDDEN_CACHE


def _phrase_regex(phrase: str):
    pat = re.escape(phrase)
    if phrase[0].isalnum():
        pat = r"(?<!\w)" + pat
    if phrase[-1].isalnum():
        pat = pat + r"(?!\w)"
    return re.compile(pat, re.I)


_YEAR_RE = re.compile(r"(?<![\w.])((?:19|20)\d\d)\s*[-–—]\s*((?:19|20)?\d\d)(?![\w])")
_NUM = r"\d[\d,]*(?:\.\d+)?"
_NUM_RE = re.compile(r"(?<![A-Za-z\d.])(\$)?(" + _NUM + r")(\s*%)?")
_RANGE_RE = re.compile(r"(?<![A-Za-z\d.])(" + _NUM + r")\s*[-–—]\s*(" + _NUM + r")(?![\d])")


def _to_float(tok: str) -> float | None:
    try:
        return float(tok.replace(",", ""))
    except ValueError:
        return None


def extract_numbers(text: str) -> list[dict]:
    """Every number in text: {"value": float, "pct": bool, "raw": str}. Handles commas, %, $, ranges, academic years.

    An academic year such as 2025-26 gives 2025 and 2026. A letter-digit tag such as C7 is not a number.
    """
    found = []
    work = text
    for m in _YEAR_RE.finditer(text):
        a, b = m.group(1), m.group(2)
        end = int(b) if len(b) == 4 else int(a[:2] + b)
        found.append({"value": float(a), "pct": False, "raw": m.group(0)})
        found.append({"value": float(end), "pct": False, "raw": m.group(0)})
        work = work[:m.start()] + " " * (m.end() - m.start()) + work[m.end():]
    for m in _NUM_RE.finditer(work):
        v = _to_float(m.group(2).rstrip(","))
        if v is None:
            continue
        found.append({"value": v, "pct": bool(m.group(3)), "raw": m.group(0).strip()})
    return found


def _num_allowed(item: dict, allowed: list[float]) -> bool:
    v = item["value"]
    for a in allowed:
        if abs(a - v) < 1e-9:
            return True
        if item["pct"] and abs(a * 100.0 - v) <= 0.05 + 1e-9:  # a percent may match its fraction
            return True
    return False


def _allowed_floats(allowed_numbers) -> list[float]:
    out = []
    for a in allowed_numbers or ():
        if isinstance(a, (int, float)):
            out.append(float(a))
        else:
            for it in extract_numbers(str(a)):
                out.append(it["value"])
    return out


@lru_cache(maxsize=1)
def _name_aliases() -> list[tuple[str, str]]:
    """(normalised spelling, canonical key) for every college name we can recognise, longest spelling first."""
    pairs = {}
    for c in load_colleges():
        pairs[_norm(c["name"])] = _norm(c["name"])
    for short, full in CASE_NAME_TO_SCORECARD.items():
        pairs[_norm(short)] = _norm(full)
        pairs[_norm(full)] = _norm(full)
    for sid, r in _rows().items():
        canon = _norm(r["school_name"])
        pairs[canon] = canon
        pairs[_norm(DISPLAY.get(sid, r["school_name"]))] = canon
    for alias, sid in ALIASES.items():
        if sid in _rows():
            pairs[_norm(alias)] = _norm(_rows()[sid]["school_name"])
    # Aliases that are not a whole college name but would be ambiguous words are not added.
    pairs.pop("", None)
    return sorted(pairs.items(), key=lambda kv: -len(kv[0]))


def _canon(name: str) -> str:
    n = _norm(name)
    for alias, canon in _name_aliases():
        if alias == n:
            return canon
    return n


def names_in(text: str) -> set[str]:
    """Canonical keys of every college name found in text."""
    padded = " " + _norm(text) + " "
    found = set()
    for alias, canon in _name_aliases():
        needle = " " + alias + " "
        if needle in padded:
            found.add(canon)
            padded = padded.replace(needle, " # ")
    return found


def _quotes_in(text: str) -> list[str]:
    spans = re.findall(r'"([^"]+)"', text)
    spans += re.findall(r"“([^”]+)”", text)
    spans += re.findall(r"(?<![\w])'([^']+)'(?![\w])", text)
    return spans


def _gives_score_range(text: str) -> bool:
    low = text.lower()
    for m in _RANGE_RE.finditer(_YEAR_RE.sub(" ", text)):
        a, b = _to_float(m.group(1)), _to_float(m.group(2))
        if a is None or b is None:
            continue
        if 200 <= a <= 1600 and 200 <= b <= 1600:
            return True
        if re.search(r"\bact\b", low) and 1 <= a <= 36 and 1 <= b <= 36:
            return True
    return False


def check_sentence(text, allowed_numbers, allowed_names, quotes=()) -> dict:
    """Code check on one sentence. Returns {"ok": bool, "reason": str}; reason is plain words."""
    text = text or ""
    if not text.strip():
        return {"ok": False, "reason": "The sentence is empty."}
    low = text.lower()

    for phrase, why in _forbidden():
        if _phrase_regex(phrase).search(low):
            return {"ok": False, "reason": f'It uses a phrase we do not allow ("{phrase}"): {why}'}

    allowed = _allowed_floats(allowed_numbers)
    for item in extract_numbers(text):
        if not _num_allowed(item, allowed):
            return {"ok": False, "reason": f"The number {item['raw']} is not one of the numbers we were given for this sentence."}

    ok_names = {_canon(n) for n in (allowed_names or ())}
    for n in sorted(names_in(text)):
        if n not in ok_names:
            return {"ok": False, "reason": f"It names a college that is not allowed here ({n})."}

    ok_quotes = {q.strip().lower() for q in quotes or ()}
    for q in _quotes_in(text):
        if q.strip().lower() not in ok_quotes:
            return {"ok": False, "reason": f'The quoted words "{q}" are not in the source text.'}

    if _gives_score_range(text) and "sent scores" not in low and "submitted" not in low:
        return {"ok": False, "reason": "It gives a test score range without saying that only students who submitted scores are counted."}

    return {"ok": True, "reason": "Every number, college name and quote matches the source; no banned phrase."}


# ---------------------------------------------------------------- claims

def _skip_c1(row: dict) -> bool:
    return any(f.startswith("C1_REJECTED") for f in _flags(row))


def _skip_c7(row: dict) -> bool:
    return any(f.startswith("C7_") for f in _flags(row))


def _c7_readable(row: dict) -> bool:
    cols = [k for k in row if k.startswith("c7_")]
    vals = [row[k] for k in cols if row[k]]
    if len(cols) != 18 or len(vals) < 15:
        return False
    if len(vals) >= 15 and len(set(vals)) == 1:  # every factor identical = extraction artefact
        return False
    return all(v in C7_LEVELS for v in vals)


def _c7_value(row: dict, col: str) -> str | None:
    if _skip_c7(row) or not _c7_readable(row):
        return None
    v = row.get(col) or ""
    return v if v in C7_LEVELS else None


def _claim(row, claim_id, field, text, allowed_extra):
    year = _year(row)
    name = _display(row)
    allowed = _allowed_floats(allowed_extra) + [float(year[:4]), float(int(year[:2] + year[5:7]))] if year else _allowed_floats(allowed_extra)
    res = check_sentence(text, allowed, {row["school_name"], name})
    return {
        "claim_id": claim_id,
        "text": text,
        "field": field,
        "year": year,
        "source_url": row.get("source_url_school_cds") or "",
        "numbers": [it["value"] if it["value"] != int(it["value"]) else int(it["value"]) for it in extract_numbers(text)],
        "kb": None,
        "checked": bool(res["ok"]),
        "_check": res,
    }


def _build_all(row: dict) -> list[dict]:
    """Every claim the row supports, each already checked (failures included, checked False)."""
    out = []
    name = _display(row)
    year = _year(row)
    if not year:
        return out

    # C7 factor ratings
    for col, label in C7_FACTORS.items():
        v = _c7_value(row, col)
        if v:
            text = f"{name} rates {label} as {v} ({C7_LEVELS[v]}) in its own Common Data Set, section C7, {year}."
            out.append(_claim(row, col, "CDS C7", text, []))

    # C1 admitted of applied
    ap, ad = _num(row.get("applied_total")), _num(row.get("admitted_total"))
    if not _skip_c1(row) and ap and ad and 0 < ad <= ap:
        rate = round(100.0 * ad / ap, 1)
        text = f"In {year}, {name} admitted {_fmt_int(ad)} of {_fmt_int(ap)} first-year applicants ({_fmt_pct(rate)}%)."
        out.append(_claim(row, "admit_total", "CDS C1", text, [ap, ad, rate, ad / ap]))

    # C1 residency split: all six present, each admitted <= applied, and the three parts add up to the total
    keys = ["in_state_applied", "in_state_admitted", "out_of_state_applied", "out_of_state_admitted",
            "nonresident_applied", "nonresident_admitted"]
    vals = {k: _num(row.get(k)) for k in keys}
    if not _skip_c1(row) and all(v is not None and v > 0 for v in vals.values()):
        parts_ok = all(vals[a.replace("applied", "admitted")] <= vals[a] for a in keys[0::2])
        sums_ok = True
        if ap and ad:
            sums_ok = abs(sum(vals[k] for k in keys[0::2]) - ap) <= 0.01 * ap and abs(sum(vals[k] for k in keys[1::2]) - ad) <= 0.01 * ad
        if parts_ok and sums_ok:
            text = (f"{name} ({year}) admitted {_fmt_int(vals['in_state_admitted'])} of {_fmt_int(vals['in_state_applied'])} in-state, "
                    f"{_fmt_int(vals['out_of_state_admitted'])} of {_fmt_int(vals['out_of_state_applied'])} out-of-state and "
                    f"{_fmt_int(vals['nonresident_admitted'])} of {_fmt_int(vals['nonresident_applied'])} international applicants.")
            out.append(_claim(row, "admit_residency", "CDS C1 (residency)", text, list(vals.values())))

    # C2 wait list
    wo, wa, wd = (_num(row.get(k)) for k in ("wl_offered", "wl_accepted", "wl_admitted"))
    if None not in (wo, wa, wd) and wo > 0 and 0 <= wd <= wa <= wo:
        if not (wd == 1 and wa >= 100):  # a lone "1" beside hundreds of accepted places looks like a yes/no mark, not a count
            text = (f"{name} ({year}) offered {_fmt_int(wo)} students a wait-list place; "
                    f"{_fmt_int(wa)} accepted and {_fmt_int(wd)} were later admitted.")
            out.append(_claim(row, "waitlist", "CDS C2", text, [wo, wa, wd]))

    # C9 SAT range, with the share of enrolled students who sent scores
    p25, p75, pct = (_num(row.get(k)) for k in ("sat_p25", "sat_p75", "sat_submit_pct"))
    if None not in (p25, p75, pct) and 400 <= p25 < p75 <= 1600 and 0 < pct <= 100:
        text = (f"Among {name} enrolled first-year students who submitted SAT scores ({_fmt_pct(pct)}% of them did), "
                f"the middle 50% scored {int(round(p25))}-{int(round(p75))} ({year}).")
        out.append(_claim(row, "test_range", "CDS C9", text, [p25, p75, pct, 50]))
    return out


def college_says(college) -> list[dict]:
    """Checked claims from this college's own Common Data Set row. [] when it has no row."""
    row = row_for(college)
    if not row:
        return []
    return [{k: v for k, v in c.items() if not k.startswith("_")} for c in _build_all(row) if c["checked"]]


def myth_checks(college) -> list[dict]:
    """What this college's own form rates for each common belief. Never says whether the belief is true in general."""
    row = row_for(college)
    out = []
    for belief, col in BELIEFS:
        item = {"belief": belief, "college_says": DOES_NOT_SAY, "source_url": None, "year": None, "status": "no_row"}
        if row:
            item["source_url"] = row.get("source_url_school_cds") or None
            item["year"] = _year(row) or None
            name = _display(row)
            label = C7_FACTORS[col]
            v = _c7_value(row, col)
            if v:
                item["college_says"] = f"{name}'s own form rates {label} as {v} ({C7_LEVELS[v]})."
                item["status"] = "stated"
            elif _skip_c7(row) or not _c7_readable(row):
                item["college_says"] = UNREADABLE if any(f.startswith("C7_REJECTED") for f in _flags(row)) else DOES_NOT_SAY
                item["status"] = "unreadable" if item["college_says"] == UNREADABLE else "not_stated"
            else:
                item["status"] = "not_stated"
        out.append(item)
    return out


def kb_query_for(claim: dict) -> str:
    """Short text to search the knowledge base with for this claim. No college name: the documents are about the forms."""
    cid = (claim or {}).get("claim_id", "")
    if cid in C7_FACTORS:
        return f"Common Data Set section C7 {C7_FACTORS[cid]} Very Important Important Considered Not Considered meaning"
    return {
        "admit_total": "Common Data Set section C1 first-year applicants admitted counts definition",
        "admit_residency": "Common Data Set applicants admitted in-state out-of-state international split",
        "waitlist": "Common Data Set section C2 wait list offered accepted admitted",
        "test_range": "Common Data Set section C9 test scores middle 50% enrolled students who submitted scores",
    }.get(cid, "Common Data Set " + str((claim or {}).get("field", "")))


# ---------------------------------------------------------------- self-check

def _selfcheck() -> None:
    rows = _rows()
    print(f"CDS rows: {len(rows)}")
    unmatched = unmatched_rows()
    print(f"Rows that match a Scorecard college: {len(rows) - len(unmatched)} of {len(rows)}; no match: {unmatched or 'none'}")
    bad = []
    for sid, r in rows.items():
        c = find_college(r["school_name"])
        if c is None or row_for(c) is None or row_for(c)["school_id"] != sid:
            bad.append(sid)
    print(f"Rows whose Scorecard college does not resolve back to the same row (alias failures): {bad or 'none'}")
    built = passed = 0
    for sid, r in rows.items():
        cl = _build_all(r)
        built += len(cl)
        passed += sum(1 for c in cl if c["checked"])
    print(f"Claims built across all rows: {built}; passed their own check: {passed}")
    for label, name in (("Cornell", "Cornell University"), ("Georgia Tech", "Georgia Institute of Technology-Main Campus"),
                        ("A college with no row", "Rice University")):
        col = find_college(name)
        print(f"\n=== {label} ===")
        claims = college_says(col)
        if not claims:
            print("(no claims: this college has no row in the sample)")
        for c in claims:
            print(f"- [{c['claim_id']}] {c['text']}  | numbers={c['numbers']} checked={c['checked']}")
            print(f"    source: {c['source_url']}")
        for m in myth_checks(col):
            print(f"  myth: {m['belief']} -> {m['college_says']}")
    print("\nRequired caveats:")
    for c in REQUIRED_CAVEATS:
        print(" *", c)


if __name__ == "__main__":
    _selfcheck()
