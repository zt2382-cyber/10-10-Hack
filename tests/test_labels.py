"""Tests for engine.labels. Real colleges come from find_college; boundary cases copy a real college and change one field."""
import json
import unittest

from engine.colleges import act_to_sat, find_college
from engine.labels import RULES_TEXT, label_college

PURDUE = find_college("Purdue University-Main Campus")      # admit 0.4987, SAT 1200-1480, ACT 27-34
CORNELL = find_college("Cornell University")                # admit 0.0876, SAT 1500-1570
MICHIGAN = find_college("University of Michigan-Ann Arbor")  # admit 0.1564, SAT 1360-1530
LYNCHBURG = find_college("University of Lynchburg")         # admit 0.4301, SAT 980-1230, no ACT range
MISSISSIPPI = find_college("Mississippi Christian University")  # admit 0.2911, ACT 19-25, no SAT range
PITZER = find_college("Pitzer College")                     # admit 0.2516, no SAT or ACT range


def sat(n):
    return {"sat": n, "act": None}


def act(n):
    return {"sat": None, "act": n}


class TestLabels(unittest.TestCase):
    def test_00_real_colleges_loaded(self):
        for c in (PURDUE, CORNELL, MICHIGAN, LYNCHBURG, MISSISSIPPI, PITZER):
            self.assertIsNotNone(c)

    def test_r0_outside_data(self):
        r = label_college(sat(1450), None)
        self.assertEqual((r["state"], r["text"], r["rule_id"]), ("outside_data", "Outside our data", "R0"))
        self.assertTrue(r["steady"])
        self.assertEqual(r["flips"], [])
        self.assertIsNone(find_college("Hogwarts School"))  # a name that is not in our college file
        self.assertEqual(label_college(sat(1450), find_college("Hogwarts School"))["state"], "outside_data")

    def test_r1_reach_for_everyone(self):
        r = label_college(sat(1600), CORNELL)
        self.assertEqual((r["state"], r["text"], r["rule_id"]), ("reach_for_everyone", "Reach for everyone", "R1"))
        self.assertIn("8.8%", r["rule_text"])
        self.assertTrue(r["steady"] and r["flips"] == [])
        # no score at all still gives R1: it comes before the score checks
        self.assertEqual(label_college({}, CORNELL)["state"], "reach_for_everyone")

    def test_r2_cant_say_missing_admit_rate(self):
        r = label_college(sat(1300), dict(PURDUE, admit_rate=None))
        self.assertEqual((r["state"], r["text"], r["rule_id"]), ("cant_say", "Can't say", "R2"))
        self.assertIn("admit rate is missing", r["rule_text"])
        self.assertTrue(r["steady"] and r["flips"] == [])

    def test_r2_cant_say_student_has_no_score(self):
        for s in ({}, {"sat": None, "act": None}, None, {"sat": "n/a"}):
            r = label_college(s, PURDUE)
            self.assertEqual(r["state"], "cant_say", s)
            self.assertIn("score", r["rule_text"])

    def test_r2_cant_say_college_has_no_range(self):
        r = label_college(sat(1300), PITZER)
        self.assertEqual(r["state"], "cant_say")
        self.assertIn("no usable SAT or ACT range", r["rule_text"])
        self.assertEqual(r["publishers"], [])  # nobody can label without a range at this admit rate

    def test_r2_sat_only_student_act_only_college(self):
        r = label_college(sat(1100), MISSISSIPPI)
        self.assertEqual(r["state"], "cant_say")
        self.assertIn("only an SAT score", r["rule_text"])
        self.assertIn("only an ACT range", r["rule_text"])

    def test_r3_reach(self):
        r = label_college(sat(1150), PURDUE)
        self.assertEqual((r["state"], r["rule_id"], r["score_kind"], r["score_used"]), ("reach", "R3", "SAT", 1150))
        self.assertEqual(r["inputs"], {"sat25": 1200, "sat75": 1480, "admit_rate": PURDUE["admit_rate"]})
        self.assertIn("1150", r["rule_text"])
        self.assertIn("1200 to 1480", r["rule_text"])

    def test_r4_target_text_has_real_numbers(self):
        r = label_college(sat(1300), PURDUE)
        self.assertEqual((r["state"], r["rule_id"]), ("target", "R4"))
        self.assertEqual(r["rule_text"], "The score of 1300 is inside the college's middle range, 1200 to 1480.")
        self.assertEqual(r["not_used"], ["GPA", "activities", "essay"])
        self.assertIn("The score range covers only students who sent scores.", r["caveats"])
        self.assertTrue(r["steady"])

    def test_r5_likely(self):
        r = label_college(sat(1500), PURDUE)
        self.assertEqual((r["state"], r["text"], r["rule_id"]), ("likely", "Likely", "R5"))
        self.assertIn("1500", r["rule_text"])

    def test_above_range_but_selective_is_target(self):
        r = label_college(sat(1600), MICHIGAN)  # admit 15.6%, top of range 1530
        self.assertEqual((r["state"], r["rule_id"]), ("target", "R4"))
        self.assertIn("not marked likely", r["rule_text"])

    def test_boundary_15_percent_exactly(self):
        self.assertEqual(label_college(sat(1300), dict(PURDUE, admit_rate=0.15))["rule_id"], "R4")  # 15% is not under 15%
        self.assertEqual(label_college(sat(1300), dict(PURDUE, admit_rate=0.1499))["rule_id"], "R1")

    def test_boundary_40_percent_exactly(self):
        self.assertEqual(label_college(sat(1480), dict(PURDUE, admit_rate=0.40))["state"], "likely")   # 40% counts
        self.assertEqual(label_college(sat(1480), dict(PURDUE, admit_rate=0.3999))["state"], "target")
        self.assertEqual(label_college(sat(1479), dict(PURDUE, admit_rate=0.40))["state"], "target")   # 75th pct exactly counts
        self.assertEqual(label_college(sat(1200), PURDUE)["state"], "target")                          # 25th pct exactly is not reach
        self.assertEqual(label_college(sat(1199), PURDUE)["state"], "reach")

    def test_act_only_student_uses_act_range(self):
        r = label_college(act(30), PURDUE)
        self.assertEqual((r["state"], r["score_kind"], r["score_used"]), ("target", "ACT", 30))
        self.assertEqual(r["inputs"], {"act25": 27, "act75": 34, "admit_rate": PURDUE["admit_rate"]})
        self.assertIn("ACT score of 30", r["rule_text"])
        self.assertIn("27 to 34", r["rule_text"])

    def test_act_converted_to_sat(self):
        r = label_college(act(30), LYNCHBURG)  # college has an SAT range only
        self.assertEqual(r["score_kind"], "ACT converted to SAT")
        self.assertEqual(r["score_used"], act_to_sat(30))
        self.assertEqual(r["state"], "likely")  # converted score is above 1230 and admit rate is 43%
        self.assertIn("980 to 1230", r["rule_text"])
        self.assertTrue(any("converted" in c for c in r["caveats"]))
        self.assertIn("The score range covers only students who sent scores.", r["caveats"])

    def test_sat_wins_when_student_has_both(self):
        r = label_college({"sat": 1300, "act": 20}, PURDUE)
        self.assertEqual((r["score_kind"], r["score_used"]), ("SAT", 1300))

    def test_edge_flip_down(self):
        r = label_college(sat(1210), PURDUE)  # 1180 would be reach
        self.assertEqual(r["state"], "target")
        self.assertFalse(r["steady"])
        self.assertIn({"cause": "score 30 points lower", "to": "reach"}, r["flips"])
        self.assertNotIn("score 30 points higher", [f["cause"] for f in r["flips"]])

    def test_edge_flip_up(self):
        r = label_college(sat(1460), PURDUE)  # 1490 would be likely
        self.assertFalse(r["steady"])
        self.assertEqual(r["flips"], [{"cause": "score 30 points higher", "to": "likely"}])

    def test_edge_flip_admit_rate(self):
        r = label_college(sat(1500), dict(PURDUE, admit_rate=0.44))  # 39% would not be likely
        self.assertEqual(r["state"], "likely")
        self.assertIn({"cause": "admit rate 5 points lower", "to": "target"}, r["flips"])
        r2 = label_college(sat(1300), dict(PURDUE, admit_rate=0.18))  # 13% would be reach for everyone
        self.assertIn({"cause": "admit rate 5 points lower", "to": "reach_for_everyone"}, r2["flips"])

    def test_edge_flip_uses_one_act_point(self):
        r = label_college(act(27), PURDUE)  # ACT 26 would be reach
        self.assertEqual(r["state"], "target")
        self.assertIn({"cause": "score 1 point lower", "to": "reach"}, r["flips"])

    def test_steady_when_nothing_changes(self):
        r = label_college(sat(1330), PURDUE)
        self.assertTrue(r["steady"])
        self.assertEqual(r["flips"], [])

    def test_publishers_disagree(self):
        r = label_college(sat(1450), PURDUE)  # ours: target. Scoir calls anything above the midpoint 1340 likely.
        self.assertEqual(r["state"], "target")
        got = {p["name"]: p["label"] for p in r["publishers"]}
        self.assertEqual(got["BigFuture"], "target")
        self.assertEqual(got["Scoir"], "likely")
        self.assertTrue(r["publishers_disagree"])

    def test_publishers_agree(self):
        r = label_college(sat(1300), PURDUE)
        self.assertEqual({p["label"] for p in r["publishers"]}, {"target"})
        self.assertEqual({p["name"] for p in r["publishers"]},
                         {"BigFuture", "Princeton Review", "Scoir", "Appily", "CollegeVine"})
        self.assertFalse(r["publishers_disagree"])

    def test_reach_for_everyone_counts_as_reach_for_publishers(self):
        r = label_college(sat(1600), CORNELL)  # Appily and CollegeVine say reach; score-only books say target or likely
        self.assertEqual(r["state"], "reach_for_everyone")
        self.assertTrue(r["publishers_disagree"])
        lab = {p["name"]: p["label"] for p in r["publishers"]}
        self.assertEqual(lab["Appily"], "reach")
        self.assertEqual(lab["CollegeVine"], "reach")

    def test_odd_input_never_raises(self):
        for s in (None, "text", 5, [], {"sat": "abc"}, {"sat": 99999}, {"act": 99}, {"sat": float("nan")}, {"sat": True}):
            for c in (None, {}, {"admit_rate": "x"}, {"admit_rate": 0.5, "sat25": "a"}, PURDUE, "Purdue"):
                r = label_college(s, c)
                self.assertIn(r["state"], {"outside_data", "reach_for_everyone", "cant_say", "reach", "target", "likely"})
                self.assertTrue(r["rule_text"])
        r = label_college({"sat": 99999, "act": 30}, PURDUE)  # a bad SAT is ignored, the ACT is used
        self.assertEqual(r["score_kind"], "ACT")
        self.assertTrue(any("400 to 1600" in c for c in r["caveats"]))

    def test_output_is_json_and_has_contract_keys(self):
        keys = {"state", "text", "rule_id", "rule_text", "score_used", "score_kind", "inputs", "not_used", "caveats",
                "steady", "flips", "publishers", "publishers_disagree"}
        for c in (None, CORNELL, PURDUE, PITZER, MISSISSIPPI):
            r = label_college(sat(1400), c)
            self.assertEqual(set(r), keys)
            json.dumps(r)

    def test_no_probability_language(self):
        outs = [label_college(s, c) for s in (sat(1100), sat(1450), act(30)) for c in (None, CORNELL, PURDUE, MICHIGAN, PITZER)]
        blob = (json.dumps(outs) + " ".join(RULES_TEXT)).lower()
        for bad in ("chance", "probab", "likelihood of admission"):
            self.assertNotIn(bad, blob)

    def test_rules_text_exported(self):
        self.assertIsInstance(RULES_TEXT, list)
        self.assertTrue(all(isinstance(x, str) and x for x in RULES_TEXT))
        self.assertGreaterEqual(len(RULES_TEXT), 5)


if __name__ == "__main__":
    unittest.main()
