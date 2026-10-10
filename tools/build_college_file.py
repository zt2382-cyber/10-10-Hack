"""Build data/colleges/scorecard_colleges.csv from the full federal College Scorecard institution file.

    python tools/build_college_file.py <path to Most-Recent-Cohorts-Institution_*.zip>

Keeps every public or private non-profit college (CONTROL 1 or 2) that mainly awards bachelor's degrees or higher
(PREDDEG 3 or 4 when that column exists) with at least 500 undergraduates and a published admit rate.
"NULL", "NA", "PrivacySuppressed" and blanks are written as empty. Reads the CSV straight out of the zip;
nothing in the zip is executed. Standard library only.
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "colleges" / "scorecard_colleges.csv"

TEXT = ("INSTNM", "CITY", "STABBR", "INSTURL")
OLD_COLS = ["UNITID", "INSTNM", "CITY", "STABBR", "CONTROL", "REGION", "LOCALE", "ADM_RATE", "SATVR25", "SATVR75",
            "SATMT25", "SATMT75", "SAT_AVG", "ACTCM25", "ACTCM75", "ACTCM50", "UGDS", "COSTT4_A", "TUITIONFEE_IN",
            "TUITIONFEE_OUT", "PCTPELL", "C150_4", "RET_FT4", "MD_EARN_WNE_P10", "INSTURL"]
NET_COLS = ["NPT4_PUB", "NPT4_PRIV"] + [f"NPT4{i}_PUB" for i in range(1, 6)] + [f"NPT4{i}_PRIV" for i in range(1, 6)]
EXTRA_COLS = ["PCTFLOAN", "GRAD_DEBT_MDN"]
COLUMNS = OLD_COLS + NET_COLS + EXTRA_COLS
MISSING = {"", "NULL", "NA", "PRIVACYSUPPRESSED"}


def clean(col, v):
    v = (v or "").strip()
    if v.upper() in MISSING:
        return ""
    if col in TEXT:
        return v
    try:
        float(v)
    except ValueError:
        return ""
    return v


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(src: str) -> None:
    with zipfile.ZipFile(src) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX")
                    and "Institution" in n)
        with z.open(name) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            header = reader.fieldnames or []
            has_pred = "PREDDEG" in header
            cols = [c for c in COLUMNS if c in header]
            absent = [c for c in COLUMNS if c not in header]
            rows = []
            for r in reader:
                if (r.get("CONTROL") or "").strip() not in ("1", "2"):
                    continue
                if has_pred and (r.get("PREDDEG") or "").strip() not in ("3", "4"):
                    continue
                if (num(clean("UGDS", r.get("UGDS"))) or 0) < 500:
                    continue
                if num(clean("ADM_RATE", r.get("ADM_RATE"))) is None:
                    continue
                rows.append({c: clean(c, r.get(c)) for c in cols})
    rows.sort(key=lambda r: (r["INSTNM"], r["UNITID"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with_range = sum(1 for r in rows if (num(r["SATVR25"]) is not None and num(r["SATMT25"]) is not None)
                     or num(r["ACTCM25"]) is not None)
    with_cost = sum(1 for r in rows if num(r["COSTT4_A"]) is not None)
    with_net = sum(1 for r in rows if num(r.get("NPT4_PUB")) is not None or num(r.get("NPT4_PRIV")) is not None)
    print(f"source file: {name} (PREDDEG filter {'on' if has_pred else 'off'})")
    print(f"wrote {len(rows)} colleges to {OUT}")
    print(f"  with a score range (SAT or ACT): {with_range}")
    print(f"  with cost of attendance:         {with_cost}")
    print(f"  with average net price:          {with_net}")
    if absent:
        print("  columns not in the source file:", ", ".join(absent))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
