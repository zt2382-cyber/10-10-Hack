import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        self.assertEqual(r["own"]["status"], "ok")
        self.assertFalse(r["own"]["verified"])  # invented demo history
        self.assertTrue(r["own"]["invented"])
        self.assertAlmostEqual(r["official_admit_rate"], 0.0876, places=3)
        self.assertEqual(r["needed"], 15)

    def test_status_not_enough_for_own_pool(self):
        r = cases.find_similar(STUDENT, self.col("Carnegie Mellon University"))
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
        self.assertFalse(any("hook" in m for m in n["matched_on"]))
        o = cases.find_similar(STUDENT, self.col("Carnegie Mellon University"))["own"]  # too few: relaxes all the way, never past 100 points
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
                   "activities_note", "essay_theme", "shared", "invented", "why_similar"}
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
        self.assertEqual(s["own"]["cases"], 720)
        self.assertEqual(s["own"]["invented_cases"], 720)
        self.assertEqual(s["national"]["cases"], 2247)
        self.assertEqual(s["national"]["colleges"], 58)
        self.assertGreater(s["national"]["decisions"], 20000)


class Provenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        caselog.set_store_path(Path(self.tmp.name) / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)

    def col(self, name):
        return colleges.find_college(name)

    def test_demo_history_is_labelled_invented_everywhere(self):
        o = cases.find_similar(STUDENT, self.col("Cornell University"))["own"]
        self.assertEqual(o["source"], "Invented demo school history (not real students)")
        self.assertTrue(o["invented"])
        self.assertFalse(o["verified"])
        self.assertEqual((o["n_invented"], o["n_real"]), (o["n"], 0))
        self.assertTrue(all(e["invented"] is True for e in o["examples"]))

    def test_real_cases_are_counted_alone_and_demo_ones_left_out_with_a_note(self):
        for i in range(3):
            self.assertNotIn("error", caselog.add_case({
                "college": "Cornell University", "outcome": "denied", "sat": 1450 + i, "major_group": "CS",
                "hooks": "none", "home_state": "NJ", "cycle_year": 2026}))
        o = cases.find_similar(STUDENT, self.col("Cornell University"))["own"]
        self.assertEqual(o["source"], "Your school's finished cases")
        self.assertTrue(o["verified"])
        self.assertFalse(o["invented"])
        self.assertEqual((o["n"], o["n_real"], o["n_invented"]), (3, 3, 0))
        self.assertIn("invented demo case", o["note"])
        self.assertIn("left out", o["note"])
        self.assertTrue(all(e["invented"] is False for e in o["examples"]))

    def test_demo_added_case_counts_as_invented(self):
        caselog.set_store_path(Path(self.tmp.name) / "other.csv")
        with open(caselog.store_path(), "w", encoding="utf-8", newline="") as fh:
            csv.DictWriter(fh, fieldnames=caselog.STORE_COLUMNS).writeheader()
        caselog.add_case({"college": "Cornell University", "outcome": "denied", "sat": 1450}, demo=True)
        o = cases.find_similar(STUDENT, self.col("Cornell University"))["own"]
        self.assertTrue(o["invented"])
        self.assertEqual(o["n_invented"], 1)

    def test_demo_students_reach_15_where_the_review_wanted(self):
        cs = dict(STUDENT, sat=1450, intended_major="Computer Science")
        bio = dict(STUDENT, sat=1250, intended_major="Biology")
        for stu, names in ((cs, ("Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick")),
                           (bio, ("Rutgers University-New Brunswick", "Pennsylvania State University-Main Campus",
                                  "Boston University"))):
            for name in names:
                o = cases.find_similar(stu, self.col(name))["own"]
                self.assertEqual(o["status"], "ok", (name, stu["sat"]))
                self.assertGreaterEqual(o["n"], 15)
        self.assertIn(cases.find_similar(cs, self.col("University of Michigan-Ann Arbor"))["own"]["status"],
                      ("not_enough", "none"))


class Unavailable(unittest.TestCase):
    def test_unreadable_store_is_unavailable_never_none(self):
        with mock.patch.object(caselog, "load_cases", side_effect=OSError("disk gone")):
            r = cases.find_similar(STUDENT, colleges.find_college("Cornell University"))
            self.assertEqual(r["own"]["status"], "unavailable")
            self.assertIn("could not be read", r["own"]["note"])
            self.assertNotEqual(r["national"]["status"], "unavailable")
            s = cases.pool_summary()
            self.assertEqual(s["own"]["status"], "unavailable")
            self.assertIn("could not be read", s["own"]["note"])
            self.assertIsNone(s["own"]["cases"])


class NationalLabel(unittest.TestCase):
    def test_source_and_fixed_sentence(self):
        for name in ("Cornell University", "Carnegie Mellon University", "Barnard College"):
            n = cases.find_similar(STUDENT, colleges.find_college(name))["national"]
            self.assertEqual(n["source"], "Public posts on Reddit (r/collegeresults), self-reported")
            self.assertIn("People who post skew high-scoring, computer-science-heavy and toward selective colleges. "
                          "This is not a national sample of applicants.", n["note"])


class ScoreRule(unittest.TestCase):
    def test_out_of_range_or_fractional_scores_are_no_score(self):
        from engine import labels
        for sat, act in ((2000, None), (300, None), (None, 29.5), (None, 40), ("abc", None)):
            stu = {"sat": sat, "act": act}
            self.assertEqual(labels._clean_student_scores(stu)[:2], (None, None))
            self.assertIsNone(cases._valid_sat(sat))
            self.assertIsNone(cases._valid_act(act))
        self.assertEqual(cases._valid_sat("1450"), 1450)
        self.assertEqual(cases._valid_act(29), 29)
        r = cases.find_similar({"sat": 2000, "act": 29.5, "intended_major": "Computer Science"},
                               colleges.find_college("Purdue University-Main Campus"))
        self.assertTrue(any("no test score" in m for m in r["own"]["matched_on"]))


class HookText(unittest.TestCase):
    def test_shared_hook_is_named(self):
        stu = dict(STUDENT, hooks=["first_gen", "legacy"])
        o = cases.find_similar(stu, colleges.find_college("Rutgers University-New Brunswick"))["own"]
        if any("hook" in m for m in o["matched_on"]):
            line = next(m for m in o["matched_on"] if "hook" in m)
            self.assertTrue(line.startswith("shares a hook with the student ("), line)
            self.assertNotIn("same hook status", line)


class SimilarityPlugin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        caselog.set_store_path(Path(self.tmp.name) / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)
        self.col = colleges.find_college("Purdue University-Main Campus")

    def run_with(self, env):
        with mock.patch.dict(os.environ, env, clear=False):
            for k in ("SIMILARITY_URL",):
                os.environ.pop(k, None)
            return cases.find_similar(STUDENT, self.col)

    def test_nothing_changes_without_a_plugin(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in ("SIMILARITY_PLUGIN", "SIMILARITY_URL", "SIMILARITY_MODE"):
                os.environ.pop(k, None)
            r = cases.find_similar(STUDENT, self.col)
        self.assertFalse(r["own"]["similarity_tool"]["used"])
        self.assertFalse(any("why_similar" in e for e in r["own"]["examples"]))

    def test_rank_mode_reorders_and_keeps_counts(self):
        base = self.run_with({"SIMILARITY_PLUGIN": "engine.nonexistent:none"})
        r = self.run_with({"SIMILARITY_PLUGIN": "engine.similarity_plugin:example_plugin", "SIMILARITY_MODE": "rank"})
        for pool in ("own", "national"):
            self.assertTrue(r[pool]["similarity_tool"]["used"], pool)
            self.assertEqual(r[pool]["similarity_tool"]["mode"], "rank")
            for k in ("n", "admitted", "denied", "waitlisted", "status"):
                self.assertEqual(r[pool][k], base[pool][k], (pool, k))
            self.assertEqual({e["case_id"] for e in r[pool]["examples"]}, {e["case_id"] for e in base[pool]["examples"]})
            self.assertTrue(all(e.get("why_similar") for e in r[pool]["examples"]))
            gaps = [abs((e["sat"] or 1450) - 1450) for e in r[pool]["examples"]]
            self.assertEqual(gaps, sorted(gaps))

    def test_filter_mode_recomputes_counts_and_rule(self):
        base = self.run_with({"SIMILARITY_PLUGIN": "engine.nonexistent:none"})
        r = self.run_with({"SIMILARITY_PLUGIN": "engine.similarity_plugin:example_plugin", "SIMILARITY_MODE": "filter"})
        o = r["own"]
        self.assertTrue(o["similarity_tool"]["used"])
        self.assertEqual(o["similarity_tool"]["mode"], "filter")
        self.assertEqual(o["matched_on"], ["closest test score first; same major group noted"])
        self.assertEqual(o["n"], o["admitted"] + o["denied"] + o["waitlisted"])
        self.assertLessEqual(o["n"], base["own"]["n"])
        self.assertEqual(o["status"], "ok" if o["n"] >= 15 else ("not_enough" if o["n"] else "none"))
        for e in o["examples"]:
            self.assertLessEqual(abs((e["sat"] or 1450) - 1450), 100)

    def test_broken_plugin_falls_back_cleanly(self):
        base = self.run_with({"SIMILARITY_PLUGIN": ""})
        r = self.run_with({"SIMILARITY_PLUGIN": "no.such.module:nothing", "SIMILARITY_MODE": "filter"})
        t = r["own"]["similarity_tool"]
        self.assertFalse(t["used"])
        self.assertTrue(t["why"])
        for k in ("n", "admitted", "denied", "waitlisted", "status", "matched_on"):
            self.assertEqual(r["own"][k], base["own"][k], k)


if __name__ == "__main__":
    unittest.main()
