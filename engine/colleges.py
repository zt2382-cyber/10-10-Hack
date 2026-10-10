"""College facts: the one loader every other module uses.

Source: US College Scorecard, 300 colleges (data/colleges/scorecard_top300_admissions.csv).
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
# Four have no row in the 300-college file (Caltech, Fordham, Harvey Mudd, UC Merced): find_college returns None for them.
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


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def _int(x):
    v = _num(x)
    return None if v is None else int(round(v))


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


@lru_cache(maxsize=1)
def load_colleges() -> list[dict]:
    """All 300 colleges as plain dicts. Keys are listed in CONTRACT.md under 'College'."""
    out = []
    with open(DATA / "colleges" / "scorecard_top300_admissions.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            v25, m25, v75, m75 = (_num(r[k]) for k in ("SATVR25", "SATMT25", "SATVR75", "SATMT75"))
            out.append({
                "id": r["UNITID"],
                "name": r["INSTNM"],
                "city": r["CITY"],
                "state": r["STABBR"],
                "control": {"1": "public", "2": "private", "3": "private for-profit"}.get(r["CONTROL"], "unknown"),
                "admit_rate": _num(r["ADM_RATE"]),
                "sat25": int(v25 + m25) if None not in (v25, m25) else None,
                "sat75": int(v75 + m75) if None not in (v75, m75) else None,
                "act25": _int(r["ACTCM25"]),
                "act75": _int(r["ACTCM75"]),
                "undergrads": _int(r["UGDS"]),
                "cost_year": _int(r["COSTT4_A"]),
                "tuition_in": _int(r["TUITIONFEE_IN"]),
                "tuition_out": _int(r["TUITIONFEE_OUT"]),
                "pell_share": _num(r["PCTPELL"]),
                "grad_rate": _num(r["C150_4"]),
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
    for short, full in CASE_NAME_TO_SCORECARD.items():
        if _norm(full) in idx:
            idx[_norm(short)] = idx[_norm(full)]
    return idx


def find_college(name_or_id: str) -> dict | None:
    """Exact (case-insensitive) name, Scorecard id, or a case-file short name. None when not in the 300."""
    if not name_or_id:
        return None
    return _index().get(str(name_or_id).strip()) or _index().get(_norm(str(name_or_id)))


def case_name_for(college: dict) -> str | None:
    """The short name the self-reported case file uses for this college, or None when it has no cases."""
    for short, full in CASE_NAME_TO_SCORECARD.items():
        if _norm(full) == _norm(college["name"]):
            return short
    return None


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
