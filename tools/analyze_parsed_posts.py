"""What the parsed public posts can and cannot tell us. Prints counts only; no post text.

    python tools/analyze_parsed_posts.py > findings.json

Everything here describes people who chose to post their results. It is not a sample of applicants.
"""
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import colleges as C  # noqa: E402

P = ROOT / "data" / "cases" / "parsed"


def rows(name):
    fh = open(P / f"{name}.csv", encoding="utf-8", newline="")
    fh.readline()
    return list(csv.DictReader(fh))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def tier(rate):
    if rate is None:
        return None
    return "under 15%" if rate < 0.15 else ("15% to 40%" if rate < 0.40 else "40% and over")


def share(adm, den):
    n = adm + den
    return round(100 * adm / n) if n else None


apps = {r["record_id"]: r for r in rows("applicants")}
decs = [d for d in rows("decisions") if d["college_id"]]
rate = {c["id"]: c["admit_rate"] for c in C.load_colleges()}
name = {c["id"]: c["name"] for c in C.load_colleges()}
by_app = defaultdict(list)
for d in decs:
    d["tier"] = tier(rate.get(d["college_id"]))
    by_app[d["record_id"]].append(d)

out = {"note": "People who chose to post their results. Not a sample of applicants. Counts only.",
       "applicants": len(apps), "decisions_mapped": len(decs),
       "colleges": len({d["college_id"] for d in decs})}

# 1. how far the posted results sit from the official admit rate
ratios, by_tier = [], defaultdict(list)
per_college = defaultdict(lambda: Counter())
for d in decs:
    per_college[d["college_id"]][d["outcome"]] += 1
for cid, c in per_college.items():
    n = c["admitted"] + c["denied"] + c["waitlisted"]
    if n >= 30 and rate.get(cid):
        r = (c["admitted"] / n) / rate[cid]
        ratios.append(r)
        by_tier[tier(rate[cid])].append(r)
out["overcount"] = {"colleges_with_30_plus": len(ratios), "median_ratio": round(statistics.median(ratios), 2),
                    "by_selectivity": {t: {"colleges": len(v), "median_ratio": round(statistics.median(v), 2)} for t, v in by_tier.items()}}

# 2. the lists people applied to
shape = Counter()
no_safe, no_safe_shut, all_reach = 0, 0, 0
sizes, reach_share = [], []
for rid, ds in by_app.items():
    tiers = [d["tier"] for d in ds if d["tier"]]
    if len(tiers) < 4:
        continue
    sizes.append(len(tiers))
    r = sum(1 for t in tiers if t == "under 15%") / len(tiers)
    reach_share.append(r)
    has_open = any(t == "40% and over" for t in tiers)
    if r > 0.5:
        shape["more than half very selective"] += 1
    if not has_open:
        no_safe += 1
        if not any(d["outcome"] == "admitted" for d in ds):
            no_safe_shut += 1
    if r == 1:
        all_reach += 1
with_list = len(sizes)
shut_all = sum(1 for rid, ds in by_app.items() if len([d for d in ds if d["tier"]]) >= 4 and not any(d["outcome"] == "admitted" for d in ds))
out["lists"] = {"applicants_with_4_plus_colleges": with_list, "median_list_length": statistics.median(sizes),
                "median_share_very_selective": round(100 * statistics.median(reach_share)),
                "more_than_half_very_selective": shape["more than half very selective"],
                "no_college_admitting_40_or_more": no_safe, "of_those_admitted_nowhere": no_safe_shut,
                "every_college_very_selective": all_reach, "admitted_nowhere_overall": shut_all}

# 3. where the decisions pile up
top = Counter(d["college_id"] for d in decs).most_common(20)
out["concentration"] = {"top_20_colleges_share_of_decisions": round(100 * sum(n for _, n in top) / len(decs)),
                        "top_10": [name.get(cid, cid) for cid, _ in top[:10]]}

# 4. does the score separate admitted from denied inside one tier? (posted results only)
bands = defaultdict(lambda: Counter())
for d in decs:
    a = apps.get(d["record_id"])
    sat = num(a.get("sat_total")) if a else None
    if sat is None or d["tier"] != "under 15%" or d["outcome"] == "waitlisted":
        continue
    b = "under 1400" if sat < 1400 else ("1400 to 1490" if sat < 1500 else ("1500 to 1540" if sat < 1550 else "1550 and over"))
    bands[b][d["outcome"]] += 1
out["score_at_very_selective"] = {b: {"admitted": c["admitted"], "denied": c["denied"], "admitted_per_100": share(c["admitted"], c["denied"])}
                                  for b, c in sorted(bands.items())}


# 5. essay themes, activities, hooks, self-rating: admitted per 100 decided, at very selective colleges only
def by_tag(field, sep=";"):
    t = defaultdict(lambda: Counter())
    for d in decs:
        if d["tier"] != "under 15%" or d["outcome"] == "waitlisted":
            continue
        a = apps.get(d["record_id"]) or {}
        tags = [x.strip() for x in (a.get(field) or "").split(sep) if x.strip()] or ["(none stated)"]
        for tag in set(tags):
            t[tag][d["outcome"]] += 1
    return {k: {"decisions": c["admitted"] + c["denied"], "admitted_per_100": share(c["admitted"], c["denied"])}
            for k, c in sorted(t.items(), key=lambda kv: -(kv[1]["admitted"] + kv[1]["denied"])) if c["admitted"] + c["denied"] >= 150}


out["essay_themes_at_very_selective"] = by_tag("essay_themes")
out["activities_at_very_selective"] = by_tag("activities_tags")
rating = defaultdict(lambda: Counter())
hooks = defaultdict(lambda: Counter())
for d in decs:
    if d["tier"] != "under 15%" or d["outcome"] == "waitlisted":
        continue
    a = apps.get(d["record_id"]) or {}
    r = num(a.get("essay_self_rating"))
    if r is not None:
        rating["rated 8 or more" if r >= 8 else ("rated 6 to 7.9" if r >= 6 else "rated under 6")][d["outcome"]] += 1
    for h, label in (("hook_first_gen", "first in family"), ("hook_legacy", "legacy"), ("hook_low_income", "low income")):
        hooks[label if (a.get(h) or "").strip() else "not " + label][d["outcome"]] += 1
out["essay_self_rating_at_very_selective"] = {k: {"decisions": c["admitted"] + c["denied"], "admitted_per_100": share(c["admitted"], c["denied"])} for k, c in rating.items()}
out["hooks_at_very_selective"] = {k: {"decisions": c["admitted"] + c["denied"], "admitted_per_100": share(c["admitted"], c["denied"])} for k, c in sorted(hooks.items())}

# 6. rounds, where stated
rounds = defaultdict(lambda: Counter())
for d in decs:
    if d["tier"] == "under 15%" and d["round"] and d["outcome"] != "waitlisted":
        rounds[d["round"]][d["outcome"]] += 1
out["rounds_at_very_selective"] = {k: {"decisions": c["admitted"] + c["denied"], "admitted_per_100": share(c["admitted"], c["denied"])} for k, c in rounds.items()}

# 7. coverage a product could use
n_by_college = Counter(d["college_id"] for d in decs)
out["coverage"] = {"colleges_with_15_plus": sum(1 for n in n_by_college.values() if n >= 15),
                   "colleges_with_30_plus": sum(1 for n in n_by_college.values() if n >= 30),
                   "colleges_with_100_plus": sum(1 for n in n_by_college.values() if n >= 100)}
print(json.dumps(out, indent=1))
