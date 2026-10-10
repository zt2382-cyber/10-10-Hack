import csv
import json
import tempfile
import unittest
from pathlib import Path

from engine import caselog, cases, colleges

STUDENT = {"label": "Student A (SYNTHETIC)", "sat": 1450, "home_state": "NJ", "intended_major": "Computer Science",
           "hooks": []}
FORBIDDEN = ("chance", "probab", "odds")


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from strings(v)


class FindSimilarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        caselog.set_store_path(Path(self.tmp.name) / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)

    def col(self, name):
        c = colleges.find_college(name)
        self.assertIsNotNone(c, name)
        return c

    def test_status_ok_with_counts_and_official_rate(self):
        r = cases.find_similar(STUDENT, self.col("Cornell University"))
        n = r["national"]
        self.assertEqual(n["status"], "ok")
        self.assertGreaterEqual(n["n"], 15)
        self.assertEqual(n["n"], n["admitted"] + n["denied"] + n["waitlisted"])
        self.assertFalse(n["verified"])
        self.assertTrue(r["own"]["verified"])
        self.assertAlmostEqual(r["official_admit_rate"], 0.0876, places=3)
        self.assertEqual(r["needed"], 15)

    def test_status_not_enough_for_own_pool(self):
        r = cases.find_similar(STUDENT, self.col("Rutgers University-New Brunswick"))
        o = r["own"]
        self.assertEqual(o["status"], "not_enough")
        self.assertTrue(1 <= o["n"] < 15)

    def test_status_none_for_college_without_cases(self):
        r = cases.find_similar(STUDENT, self.col("Barnard College"))
        for pool in ("own", "national"):
            self.assertEqual(r[pool]["status"], "none")
            self.assertEqual(r[pool]["n"], 0)
            self.assertEqual(r[pool]["examples"], [])
        self.assertIsNone(r["overcount"])
        self.assertIsNone(r["pool_admit_share_all"])
        r2 = cases.find_similar(STUDENT, None)
        self.assertEqual(r2["national"]["status"], "none")
        self.assertIsNone(r2["official_admit_rate"])

    def test_relax_order_is_fixed(self):
        steps = cases._steps(True, True)
        self.assertEqual([(c["sat"], c["hook"], c["major"]) for c, _ in steps],
                         [(50, True, True), (50, False, True), (50, False, False), (100, False, False)])
        r = cases.find_similar(STUDENT, self.col("Rutgers University-New Brunswick"))
        n = r["national"]
        self.assertEqual(n["relaxed"], ["hook status"])
        self.assertIn("SAT within 50 points", n["matched_on"])
        self.assertIn("same major group", n["matched_on"])
        self.assertNotIn("same hook status", n["matched_on"])
        o = r["own"]  # too few cases: relaxes all the way, never past 100 points
        self.assertIn("SAT within 100 points", o["matched_on"])
        self.assertEqual(len(o["relaxed"]), 3)
        for ex in o["examples"]:
            sc = ex["sat"] if ex["sat"] else colleges.act_to_sat(ex["act"])
            self.assertLessEqual(abs(sc - 1450), 100)

    def test_no_score_student_matches_on_major_and_hooks_only(self):
        s = dict(STUDENT, sat=None)
        r = cases.find_similar(s, self.col("Purdue University-Main Campus"))
        n = r["national"]
        self.assertTrue(any("no test score" in m for m in n["matched_on"]))
        self.assertFalse(any(m.startswith("SAT within") for m in n["matched_on"]))
        self.assertIn("same major group", n["matched_on"])
        self.assertGreater(n["n"], 0)

    def test_act_is_converted(self):
        s = {"act": 33, "intended_major": "computer science", "hooks": []}
        r = cases.find_similar(s, self.col("Purdue University-Main Campus"))
        self.assertTrue(any("ACT converted" in m for m in r["national"]["matched_on"]))
        conv = colleges.act_to_sat(33)
        for ex in r["national"]["examples"]:
            c = ex["sat"] if ex["sat"] else colleges.act_to_sat(ex["act"])
            self.assertLessEqual(abs(c - conv), 100)

    def test_major_from_tags_when_student_gave_none(self):
        s = {"sat": 1450, "hooks": []}
        c = self.col("Purdue University-Main Campus")
        a = cases.find_similar(s, c)
        b = cases.find_similar(s, c, tags={"major_group": "CS"})
        self.assertFalse(any("same major group" in m for m in a["national"]["matched_on"]))
        self.assertIn("same major group", b["national"]["matched_on"])
        self.assertEqual(cases.major_group_for("Software Engineering"), "CS")
        self.assertEqual(cases.major_group_for("Mechanical engineering"), "ENG")
        self.assertEqual(cases.major_group_for("neuroscience"), "BIO")
        self.assertEqual(cases.major_group_for("pre-med"), "PREMED")
        self.assertIsNone(cases.major_group_for("Undecided"))

    def test_hidden_fields_never_appear(self):
        allowed = {"case_id", "sat", "act", "major", "hooks", "home_state", "activities_rating", "outcome",
                   "activities_note", "essay_theme", "shared"}
        for name in ("Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick"):
            r = cases.find_similar(STUDENT, self.col(name))
            text = json.dumps(r).lower()
            for bad in ("gender", "race", "income", "asian", "residence"):
                self.assertNotIn(bad, text)
            for pool in ("own", "national"):
                for ex in r[pool]["examples"]:
                    self.assertTrue(set(ex) <= allowed, set(ex) - allowed)
        n = cases.find_similar(STUDENT, self.col("Cornell University"))["national"]["examples"]
        self.assertTrue(all(e["case_id"].startswith("N-") for e in n))

    def test_deterministic(self):
        c = self.col("Cornell University")
        a = json.dumps(cases.find_similar(STUDENT, c), sort_keys=True)
        b = json.dumps(cases.find_similar(dict(STUDENT), c), sort_keys=True)
        self.assertEqual(a, b)

    def test_overcount_is_pool_share_over_official_rate(self):
        r = cases.find_similar(STUDENT, self.col("Cornell University"))
        self.assertEqual(r["overcount"], round(r["pool_admit_share_all"] / r["official_admit_rate"], 1))
        self.assertGreater(r["overcount"], 1)

    def test_examples_include_denial_and_admit(self):
        r = cases.find_similar(STUDENT, self.col("Purdue University-Main Campus"))
        ex = r["national"]["examples"]
        self.assertLessEqual(len(ex), 6)
        outs = {e["outcome"] for e in ex}
        self.assertIn("admitted", outs)
        self.assertIn("denied", outs)
        self.assertTrue(outs <= {"admitted", "denied", "waitlisted"})

    def test_no_forbidden_words_anywhere(self):
        for nm in ("Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick",
                   "Barnard College", "Princeton University"):
            for s in (STUDENT, {"label": "x"}, {"act": 30, "intended_major": "biology"}):
                r = cases.find_similar(s, colleges.find_college(nm), tags={"essay_themes": ["family"]})
                for text in strings(r):
                    low = text.lower()
                    for w in FORBIDDEN:
                        self.assertNotIn(w, low, text)

    def test_essay_theme_ordering_does_not_filter_or_change_n(self):
        p = Path(self.tmp.name) / "mine.csv"
        with open(p, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(caselog.STORE_COLUMNS)
        caselog.set_store_path(p)
        rows = [(1450, "curiosity", "Chess club"), (1440, "family", "Cares for siblings"),
                (1460, "leadership", "Summer research at a lab"), (1430, "persistence", "Debate team")]
        for i, (sat, theme, note) in enumerate(rows):
            res = caselog.add_case({"college": "Rutgers University-New Brunswick",
                                    "outcome": "admitted" if i % 2 else "denied",
                                    "sat": sat, "major_group": "CS", "hooks": "none", "home_state": "NJ",
                                    "essay_theme": theme, "activities_note": note})
            self.assertNotIn("error", res)
        c = self.col("Rutgers University-New Brunswick")
        plain = cases.find_similar(STUDENT, c)["own"]
        themed = cases.find_similar(STUDENT, c, tags={"essay_themes": ["family"], "activity_types": ["research"]})["own"]
        self.assertEqual(plain["n"], themed["n"])
        self.assertEqual(plain["shared_theme_n"], 0)
        self.assertEqual(themed["shared_theme_n"], 2)
        self.assertEqual(len(themed["examples"]), 4)
        first_two = themed["examples"][:2]
        self.assertTrue(all("shared" in e for e in first_two))
        self.assertTrue(all("shared" not in e for e in themed["examples"][2:]))
        flat = [s for e in first_two for s in e["shared"]]
        self.assertIn("essay theme: family", flat)
        self.assertIn("activity: research", flat)
        self.assertNotIn("shared_theme_n", cases.find_similar(STUDENT, c)["national"])

    def test_pool_summary(self):
        s = cases.pool_summary()
        self.assertEqual(s["own"]["cases"], 120)
        self.assertEqual(s["national"]["cases"], 2247)
        self.assertEqual(s["national"]["colleges"], 58)
        self.assertGreater(s["national"]["decisions"], 20000)


if __name__ == "__main__":
    unittest.main()
