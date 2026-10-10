"""College facts: the one loader every other module uses.

Source: US College Scorecard (data/colleges/). Preferred file: scorecard_colleges.csv, built by tools/build_college_file.py
from the full federal institution file (admissions, cost and net price). When it is absent the loader falls back to the two
older files: 300 colleges with cost data, plus more colleges with admissions data only.
Nothing here is a model call. Missing values stay None; nothing is guessed.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCORECARD_SOURCE = "US Department of Education, College Scorecard (most recent institution file)"

# Names used in the self-reported case file -> the Scorecard name.
# With only the old 300-college file, four had no row (Caltech, Fordham, Harvey Mudd, UC Merced); the full file has all four.
CASE_NAME_TO_SCORECARD = {
    "ARIZONA STATE": "Arizona State University Campus Immersion",
    "BERKELEY": "University of California-Berkeley",
    "BOSTON COLLEGE": "Boston College",
    "BOSTON UNIVERSITY": "Boston University",
    "BROWN": "Brown University",
    "CALTECH": "California Institute of Technology",
    "CASE WESTERN": "Case Western Reserve University",
    "CLAREMONT MCKENNA": "Claremont McKenna College",
    "CMU": "Carnegie Mellon University",
    "COLGATE": "Colgate University",
    "COLUMBIA": "Columbia University in the City of New York",
    "CORNELL": "Cornell University",
    "DARTMOUTH": "Dartmouth College",
    "DUKE": "Duke University",
    "EMORY": "Emory University",
    "FORDHAM": "Fordham University",
    "GEORGIA TECH": "Georgia Institute of Technology-Main Campus",
    "HARVARD": "Harvard University",
    "HARVEY MUDD": "Harvey Mudd College",
    "JOHNS HOPKINS": "Johns Hopkins University",
    "MIT": "Massachusetts Institute of Technology",
    "NORTHEASTERN": "Northeastern University",
    "NORTHWESTERN": "Northwestern University",
    "NYU": "New York University",
    "POMONA": "Pomona College",
    "PRINCETON": "Princeton University",
    "PURDUE": "Purdue University-Main Campus",
    "RICE": "Rice University",
    "RUTGERS": "Rutgers University-New Brunswick",
    "STANFORD": "Stanford University",
    "SWARTHMORE": "Swarthmore College",
    "San Jose State University": "San Jose State University",
    "TAMU": "Texas A&M University-College Station",
    "TUFTS": "Tufts University",
    "TULANE": "Tulane University of Louisiana",
    "UCD": "University of California-Davis",
    "UCHICAGO": "University of Chicago",
    "UCI": "University of California-Irvine",
    "UCLA": "University of California-Los Angeles",
    "UCM": "University of California-Merced",
    "UCR": "University of California-Riverside",
    "UCSB": "University of California-Santa Barbara",
    "UCSC": "University of California-Santa Cruz",
    "UCSD": "University of California-San Diego",
    "UIUC": "University of Illinois Urbana-Champaign",
    "UMICH": "University of Michigan-Ann Arbor",
    "UNC CHAPEL HILL": "University of North Carolina at Chapel Hill",
    "UPENN": "University of Pennsylvania",
    "USC": "University of Southern California",
    "UT-AUSTIN": "The University of Texas at Austin",
    "UT-DALLAS": "The University of Texas at Dallas",
    "UVA": "University of Virginia-Main Campus",
    "UW MADISON": "University of Wisconsin-Madison",
    "VANDERBILT": "Vanderbilt University",
    "VIRGINIA TECH": "Virginia Polytechnic Institute and State University",
    "WASHU": "Washington University in St Louis",
    "WILLIAMS": "Williams College",
    "YALE": "Yale University",
}


# Other names people commonly type. Each maps to a full Scorecard name.
EXTRA_ALIASES = {
    "penn state": "Pennsylvania State University-Main Campus", "psu": "Pennsylvania State University-Main Campus",
    "penn": "University of Pennsylvania", "university of pennsylvania": "University of Pennsylvania",
    "georgia tech": "Georgia Institute of Technology-Main Campus", "gatech": "Georgia Institute of Technology-Main Campus",
    "ut austin": "The University of Texas at Austin", "university of texas": "The University of Texas at Austin",
    "texas": "The University of Texas at Austin", "ut dallas": "The University of Texas at Dallas",
    "michigan": "University of Michigan-Ann Arbor", "university of michigan": "University of Michigan-Ann Arbor",
    "uc berkeley": "University of California-Berkeley", "cal": "University of California-Berkeley",
    "ucla": "University of California-Los Angeles", "uc san diego": "University of California-San Diego",
    "uc davis": "University of California-Davis", "uc irvine": "University of California-Irvine",
    "uc santa barbara": "University of California-Santa Barbara", "uc santa cruz": "University of California-Santa Cruz",
    "uc riverside": "University of California-Riverside",
    "carnegie mellon": "Carnegie Mellon University", "texas a&m": "Texas A&M University-College Station",
    "texas a and m": "Texas A&M University-College Station", "a&m": "Texas A&M University-College Station",
    "virginia": "University of Virginia-Main Campus", "university of virginia": "University of Virginia-Main Campus",
    "vt": "Virginia Polytechnic Institute and State University",
    "illinois": "University of Illinois Urbana-Champaign", "university of illinois": "University of Illinois Urbana-Champaign",
    "wisconsin": "University of Wisconsin-Madison", "university of wisconsin": "University of Wisconsin-Madison",
    "unc": "University of North Carolina at Chapel Hill", "north carolina": "University of North Carolina at Chapel Hill",
    "chicago": "University of Chicago", "university of chicago": "University of Chicago",
    "wash u": "Washington University in St Louis", "washington university": "Washington University in St Louis",
    "hopkins": "Johns Hopkins University", "jhu": "Johns Hopkins University", "bu": "Boston University",
    "bc": "Boston College", "columbia university": "Columbia University in the City of New York",
    "purdue university": "Purdue University-Main Campus", "rutgers university": "Rutgers University-New Brunswick",
    "tulane university": "Tulane University of Louisiana", "arizona state": "Arizona State University Campus Immersion",
    "asu": "Arizona State University Campus Immersion", "ohio state": "Ohio State University-Main Campus",
    "osu": "Ohio State University-Main Campus", "pitt": "University of Pittsburgh-Pittsburgh Campus",
    "university of washington": "University of Washington-Seattle Campus", "uw": "University of Washington-Seattle Campus",
    "minnesota": "University of Minnesota-Twin Cities", "maryland": "University of Maryland-College Park",
    "umd": "University of Maryland-College Park", "stony brook": "Stony Brook University",
}


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def _int(x):
    v = _num(x)
    return None if v is None else int(round(v))


INCOME_BANDS = ("0-30k", "30-48k", "48-75k", "75-110k", "110k+")
_BAND_TEXT = {"0-30k": "families earning up to $30,000", "30-48k": "families earning $30,000 to $48,000",
              "48-75k": "families earning $48,000 to $75,000", "75-110k": "families earning $75,000 to $110,000",
              "110k+": "families earning $110,000 or more"}
OLD_FILES = ("scorecard_top300_admissions.csv", "scorecard_more_colleges.csv")  # the fallback, in this order
FULL_FILE = "scorecard_colleges.csv"


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def _read_rows(names) -> list[dict]:
    rows = []
    for name in names:  # a file that is not there is skipped
        path = DATA / "colleges" / name
        if path.exists():
            with open(path, encoding="utf-8", newline="") as fh:
                rows += list(csv.DictReader(fh))
    return rows


@lru_cache(maxsize=1)
def load_colleges() -> list[dict]:
    """All colleges as plain dicts. Keys are listed in CONTRACT.md under 'College'.

    Reads scorecard_colleges.csv when it exists, else the two older files. "NA", "NULL", "PrivacySuppressed" and blanks
    are all None.
    """
    out = []
    rows = _read_rows((FULL_FILE,)) if (DATA / "colleges" / FULL_FILE).exists() else _read_rows(OLD_FILES)
    for r in rows:
        v25, m25, v75, m75 = (_num(r[k]) for k in ("SATVR25", "SATMT25", "SATVR75", "SATMT75"))
        control = {"1": "public", "2": "private", "3": "private for-profit"}.get(r["CONTROL"], "unknown")
        # the average net price is published per sector: public colleges in the _PUB columns, private in _PRIV
        sector = "PUB" if control == "public" else "PRIV" if control == "private" else None
        by_income = {band: (_int(r.get(f"NPT4{i}_{sector}")) if sector else None)
                     for i, band in enumerate(INCOME_BANDS, start=1)}
        out.append({
            "id": r["UNITID"],
            "name": r["INSTNM"],
            "city": r["CITY"],
            "state": r["STABBR"],
            "control": control,
            "admit_rate": _num(r["ADM_RATE"]),
            "sat25": int(v25 + m25) if None not in (v25, m25) else None,
            "sat75": int(v75 + m75) if None not in (v75, m75) else None,
            "act25": _int(r["ACTCM25"]),
            "act75": _int(r["ACTCM75"]),
            "undergrads": _int(r["UGDS"]),
            "cost_year": _int(r.get("COSTT4_A")),
            "tuition_in": _int(r.get("TUITIONFEE_IN")),
            "tuition_out": _int(r.get("TUITIONFEE_OUT")),
            "pell_share": _num(r.get("PCTPELL")),
            "grad_rate": _num(r["C150_4"]),
            "net_price": _int(r.get(f"NPT4_{sector}")) if sector else None,
            "net_price_by_income": by_income,
            "median_debt": _int(r.get("GRAD_DEBT_MDN")),
            "loan_share": _num(r.get("PCTFLOAN")),
            "url": r["INSTURL"],
            "source": SCORECARD_SOURCE,
        })
    return out


@lru_cache(maxsize=1)
def _index() -> dict:
    idx = {}
    for c in load_colleges():
        idx[_norm(c["name"])] = c
        idx[c["id"]] = c
    # A name the older files used keeps pointing at the same college (matched by id), including after a rename in the
    # newer federal file and where two colleges share a name.
    for r in _read_rows(OLD_FILES):
        if r["UNITID"] in idx:
            idx[_norm(r["INSTNM"])] = idx[r["UNITID"]]
    for short, full in list(CASE_NAME_TO_SCORECARD.items()) + list(EXTRA_ALIASES.items()):
        if _norm(full) in idx:
            idx.setdefault(_norm(short), idx[_norm(full)])
    return idx


def find_college(name_or_id: str) -> dict | None:
    """Exact (case-insensitive) name, Scorecard id, or a case-file short name. None when not in the college file."""
    if not name_or_id:
        return None
    return _index().get(str(name_or_id).strip()) or _index().get(_norm(str(name_or_id)))


def case_name_for(college: dict) -> str | None:
    """The short name the self-reported case file uses for this college, or None when it has no cases."""
    for short, full in CASE_NAME_TO_SCORECARD.items():
        if _norm(full) == _norm(college["name"]):
            return short
    return None



def _dollars(x: float) -> str:
    """Round to the nearest $1,000 and format, e.g. 13620 -> "$14,000"."""
    return "${:,}".format(int(x / 1000 + 0.5) * 1000)


def cost_sentence(college: dict | None, home_state: str | None = None, income_band: str | None = None) -> str | None:
    """Plain sentence(s) about cost, or None when the college has no cost data at all.

    Sticker cost (cost of attendance) first. At a public college that figure is the in-state one; for a student from
    another state it is that figure with out-of-state tuition swapped in. Then, when `income_band` ("0-30k", "30-48k",
    "48-75k", "75-110k", "110k+") is given and the federal file has that band, what families in the band paid on average
    after grants; otherwise the overall average. A public college's net price is not stated for an out-of-state student
    (the federal figure is not split by residency). Rounded to the nearest $1,000. Never says what this family will pay.
    """
    if not college:
        return None
    sticker = college.get("cost_year")
    public = college.get("control") == "public"
    out_of_state = bool(public and home_state and str(home_state).strip().upper() != (college.get("state") or "").upper())
    parts = []
    if sticker:
        if out_of_state:
            if college.get("tuition_in") and college.get("tuition_out"):
                parts.append(f"Sticker cost is about {_dollars(sticker - college['tuition_in'] + college['tuition_out'])} "
                             "a year for students from out of state.")
        elif public:
            parts.append(f"Sticker cost is about {_dollars(sticker)} a year in-state.")
        else:
            parts.append(f"Sticker cost is about {_dollars(sticker)} a year.")
    if not out_of_state:
        band_value = (college.get("net_price_by_income") or {}).get(income_band) if income_band else None
        if band_value is not None and income_band in _BAND_TEXT:
            parts.append(f"Families like yours paid about {_dollars(band_value)} on average after grants "
                         f"(federal data, {_BAND_TEXT[income_band]}).")
        elif college.get("net_price") is not None:
            parts.append(f"The average family paid about {_dollars(college['net_price'])} after grants.")
    if not parts:
        return None
    parts.append("What your family would pay can differ; use the college's own net price calculator.")
    return " ".join(parts)


def suggest(name: str) -> str | None:
    """A "did you mean" for a name we could not find. Never used to pick a college silently."""
    import difflib
    if not name or find_college(name):
        return None
    pool = {c["name"].lower(): c["name"] for c in load_colleges()}
    hit = difflib.get_close_matches(str(name).lower().strip(), list(pool), n=1, cutoff=0.82)
    if hit:
        return pool[hit[0]]
    starts = [full for low, full in pool.items() if low.startswith(str(name).lower().strip() + " ")]
    return starts[0] if len(starts) == 1 else None


@lru_cache(maxsize=1)
def _concordance() -> dict:
    table = {}
    with open(DATA / "colleges" / "sat_act_concordance.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["table"] == "A2_ACT_to_SAT":
                table[int(r["act_composite"])] = int(r["sat_total_single_point"])
    return table


def act_to_sat(act: int | None) -> int | None:
    """Official 2018 ACT/SAT concordance, single-point value. None when the score is outside the table."""
    if act is None:
        return None
    return _concordance().get(int(act))


if __name__ == "__main__":
    cs = load_colleges()
    print(len(cs), "colleges")
    missing = [s for s, f in CASE_NAME_TO_SCORECARD.items() if find_college(s) is None]
    print("case-file names with no Scorecard match:", missing)
    print(find_college("CORNELL"))
    print("ACT 29 ->", act_to_sat(29))
