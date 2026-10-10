"""Add more colleges to the label engine from the federal College Scorecard extract.

    python tools/add_more_colleges.py <path to scorecard_cols_subset.csv>

Writes data/colleges/scorecard_more_colleges.csv: every public or private non-profit college with at least 1,000
undergraduates and a published admit rate that is not already in the first 300. Same columns as the first file;
cost columns are left empty because this extract does not carry them (the screen then says cost is not loaded).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIRST = ROOT / "data" / "colleges" / "scorecard_top300_admissions.csv"
OUT = ROOT / "data" / "colleges" / "scorecard_more_colleges.csv"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(src: str) -> None:
    with open(FIRST, encoding="utf-8", newline="") as fh:
        first = list(csv.DictReader(fh))
    cols = list(first[0].keys())
    have = {r["UNITID"] for r in first}
    names = {r["INSTNM"].lower() for r in first}
    rows = []
    with open(src, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["UNITID"] in have or r["INSTNM"].lower() in names:
                continue
            if r.get("CONTROL") not in ("1", "2") or (num(r.get("UGDS")) or 0) < 1000 or num(r.get("ADM_RATE")) is None:
                continue
            names.add(r["INSTNM"].lower())
            rows.append({c: (r.get(c, "") if num(r.get(c)) is not None or c in ("INSTNM", "CITY", "STABBR") else "") for c in cols})
    rows.sort(key=lambda r: r["INSTNM"])
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with_range = sum(1 for r in rows if (num(r["SATVR25"]) and num(r["SATMT25"])) or num(r["ACTCM25"]))
    print(f"wrote {len(rows)} more colleges ({with_range} with a score range) to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
