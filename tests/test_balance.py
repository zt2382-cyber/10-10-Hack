"""Tests for engine.balance. Label dicts are built by hand; nothing here depends on engine.labels."""
import unittest

from engine import balance
from engine.colleges import find_college, load_colleges

NO_PAY = "What this family would actually pay is not known here."


def col(name="Test U", rate=0.5, control="private", state="PA", cid=None, **kw):
    d = {"id": cid or name, "name": name, "city": "X", "state": state, "control": control, "admit_rate": rate,
         "sat25": 1200, "sat75": 1400, "act25": None, "act75": None, "undergrads": 5000, "cost_year": 50000,
         "tuition_in": 40000, "tuition_out": 40000, "pell_share": 0.2, "grad_rate": 0.8}
    d.update(kw)
    return d


def entry(state, name=None, college="auto", rate=0.5):
    name = name or "College {}".format(state)
    if college == "auto":
        college = None if state == "outside_data" else col(name, rate=rate)
    return {"college": college, "name": name, "label": {"state": state}}


def ids(out):
    return [w["id"] for w in out["warnings"]]


STUDENT = {"sat": 1450, "home_state": "NJ"}


class TestWarnings(unittest.TestCase):
    def mixed(self):
        return [entry("reach"), entry("target"), entry("target"), entry("likely"), entry("likely")]

    def test_balanced_list_has_no_warnings(self):
        self.assertEqual(balance.assess(self.mixed(), STUDENT)["warnings"], [])

    def test_reach_heavy_fires_with_real_numbers(self):
        lst = [entry("reach")] * 5 + [entry("target"), entry("likely")] + [entry("cant_say")]
        out = balance.assess(lst, STUDENT)
        self.assertIn("reach_heavy", ids(out))
        text = [w for w in out["warnings"] if w["id"] == "reach_heavy"][0]["text"]
        self.assertEqual(text, "5 of the 7 labelled colleges are reaches.")

    def test_reach_heavy_needs_more_than_half(self):
        lst = [entry("reach")] * 2 + [entry("target")] * 2 + [entry("likely")]
        self.assertNotIn("reach_heavy", ids(balance.assess(lst, STUDENT)))
        lst = [entry("reach")] * 2 + [entry("target"), entry("likely")]
        self.assertNotIn("reach_heavy", ids(balance.assess(lst, STUDENT)))  # exactly half

    def test_reach_for_everyone_counts_as_reach(self):
        lst = [entry("reach_for_everyone", rate=0.05)] * 3 + [entry("target"), entry("likely")]
        out = balance.assess(lst, STUDENT)
        self.assertEqual(out["counts"]["reach"], 3)
        self.assertIn("reach_heavy", ids(out))

    def test_no_likely_fires_and_not(self):
        lst = [entry("reach"), entry("target")] * 3
        self.assertIn("no_likely", ids(balance.assess(lst, STUDENT)))
        self.assertNotIn("no_likely", ids(balance.assess(self.mixed(), STUDENT)))

    def test_no_target_fires_and_not(self):
        lst = [entry("reach"), entry("likely")] * 3
        self.assertIn("no_target", ids(balance.assess(lst, STUDENT)))
        self.assertNotIn("no_target", ids(balance.assess(self.mixed(), STUDENT)))

    def test_prestige_pile_fires_at_four_and_not_at_three(self):
        four = [entry("reach_for_everyone", name="Elite {}".format(i), rate=0.06) for i in range(4)]
        three = four[:3]
        self.assertIn("prestige_pile", ids(balance.assess(four + [entry("likely")], STUDENT)))
        self.assertNotIn("prestige_pile", ids(balance.assess(three + [entry("likely"), entry("target")], STUDENT)))

    def test_short_list_fires_and_not(self):
        out = balance.assess(self.mixed()[:4], STUDENT)
        self.assertIn("short_list", ids(out))
        self.assertEqual([w for w in out["warnings"] if w["id"] == "short_list"][0]["text"],
                         "Only 4 colleges on this list could be labelled.")
        self.assertNotIn("short_list", ids(balance.assess(self.mixed(), STUDENT)))

    def test_all_cant_say_fires_and_not(self):
        out = balance.assess([entry("cant_say"), entry("cant_say")], {})
        self.assertIn("all_cant_say", ids(out))
        self.assertNotIn("all_cant_say", ids(balance.assess(self.mixed(), STUDENT)))


class TestEdges(unittest.TestCase):
    def test_empty_list(self):
        out = balance.assess([], STUDENT)
        self.assertEqual(out["counts"], {"reach": 0, "target": 0, "likely": 0, "cant_say": 0, "outside_data": 0})
        self.assertEqual(out["cost_notes"], [])
        self.assertNotIn("all_cant_say", ids(out))
        self.assertIn("short_list", ids(out))

    def test_odd_input_never_raises(self):
        for bad in (None, "x", 5, [None, 3, {}, {"label": None}, {"label": {"state": "weird"}, "college": "no"}]):
            for stu in (None, {}, "x", {"sat": "abc"}):
                out = balance.assess(bad, stu)
                self.assertIn("counts", out)
                self.assertIn("suggestions", out)

    def test_no_score_student_gets_no_suggestions_and_a_note(self):
        out = balance.assess([entry("cant_say")], {"home_state": "NJ"})
        self.assertEqual(out["suggestions"], [])
        self.assertEqual(out["suggestions_note"], "No suggestions without a test score: there is nothing to compare.")

    def test_student_with_score_has_no_note(self):
        self.assertNotIn("suggestions_note", balance.assess([], STUDENT))

    def test_determinism(self):
        lst = [entry("reach_for_everyone", rate=0.05), entry("target")]
        a, b = balance.assess(lst, STUDENT), balance.assess(lst, STUDENT)
        self.assertEqual(a, b)


class TestSuggestions(unittest.TestCase):
    def test_caps_and_buckets(self):
        out = balance.assess([], STUDENT)
        likely = [s for s in out["suggestions"] if s["would_be"] == "likely"]
        target = [s for s in out["suggestions"] if s["would_be"] == "target"]
        self.assertTrue(1 <= len(likely) <= 3)
        self.assertTrue(1 <= len(target) <= 3)
        self.assertEqual(len(likely) + len(target), len(out["suggestions"]))
        for s in out["suggestions"]:
            self.assertGreaterEqual(s["admit_rate"], 0.15)
            self.assertIsNotNone(s["sat25"])

    def test_no_duplicates_of_listed_colleges(self):
        base = balance.assess([], STUDENT)["suggestions"]
        names = [s["name"] for s in base]
        listed = [{"college": find_college(n), "name": n, "label": {"state": "target"}} for n in names]
        again = balance.assess(listed, STUDENT)["suggestions"]
        self.assertTrue(again)
        self.assertFalse({s["id"] for s in again} & {s["id"] for s in base})
        # a listed college known only by name (no college dict) is also excluded
        by_name = [{"college": None, "name": n, "label": {"state": "target"}} for n in names]
        again2 = balance.assess(by_name, STUDENT)["suggestions"]
        self.assertFalse({s["name"] for s in again2} & set(names))

    def test_home_state_preferred(self):
        out = balance.assess([], STUDENT)
        by = {}
        for s in out["suggestions"]:
            by.setdefault(s["would_be"], []).append(find_college(s["id"]))
        for would_be, cs in by.items():
            states = [c["state"] == "NJ" for c in cs]
            # in-state colleges never come after an out-of-state one
            self.assertEqual(states, sorted(states, reverse=True), would_be)
        # home-state effect is real: another home state changes who comes first
        tx = balance.assess([], {"sat": 1450, "home_state": "TX"})["suggestions"]
        self.assertNotEqual([s["id"] for s in tx], [s["id"] for s in out["suggestions"]])
        first_tx = find_college(tx[0]["id"])
        self.assertEqual(first_tx["state"], "TX")

    def test_tuition_note_wording(self):
        out = balance.assess([], STUDENT)
        for s in out["suggestions"]:
            c = find_college(s["id"])
            if c["control"] == "public" and c["state"] == "NJ":
                self.assertEqual(s["tuition_note"], "In-state tuition applies")
            elif c["control"] == "public":
                self.assertEqual(s["tuition_note"], "Out-of-state tuition applies")
            else:
                self.assertEqual(s["tuition_note"], "Private: one tuition for all")

    def test_suggestion_text_is_plain_and_has_numbers(self):
        for s in balance.assess([], STUDENT)["suggestions"]:
            self.assertIn("{}%".format(int(round(s["admit_rate"] * 100))), s["why"])
            low = s["why"].lower()
            for banned in ("chance", "probab", "affordable", "cheap", "major"):
                self.assertNotIn(banned, low)

    def test_act_only_student_gets_suggestions(self):
        out = balance.assess([], {"act": 30, "home_state": "OH"})
        self.assertTrue(out["suggestions"])


class TestCostNotes(unittest.TestCase):
    def test_one_note_per_listed_college_with_cost(self):
        lst = [entry("target", name="A"), entry("outside_data"), entry("likely", name="B")]
        out = balance.assess(lst, STUDENT)
        self.assertEqual([n["name"] for n in out["cost_notes"]], ["A", "B"])
        for n in out["cost_notes"]:
            self.assertTrue(n["text"].endswith(NO_PAY))
            self.assertIn("$50,000", n["text"])

    def test_in_state_and_out_of_state_rates(self):
        nj = col("NJ Pub", control="public", state="NJ", tuition_in=15000, tuition_out=33000)
        oh = col("OH Pub", control="public", state="OH", tuition_in=12000, tuition_out=31000, cid="oh")
        lst = [{"college": nj, "name": "NJ Pub", "label": {"state": "target"}},
               {"college": oh, "name": "OH Pub", "label": {"state": "target"}}]
        notes = {n["name"]: n["text"] for n in balance.assess(lst, STUDENT)["cost_notes"]}
        self.assertIn("$15,000", notes["NJ Pub"])
        self.assertIn("in-state", notes["NJ Pub"])
        self.assertIn("$31,000", notes["OH Pub"])
        self.assertNotIn("$12,000", notes["OH Pub"])

    def test_no_cost_no_note_and_banned_words(self):
        bare = col("Bare", cost_year=None, tuition_in=None, tuition_out=None)
        lst = [{"college": bare, "name": "Bare", "label": {"state": "target"}}]
        self.assertEqual(balance.assess(lst, STUDENT)["cost_notes"], [])
        for c in load_colleges()[:40]:
            out = balance.assess([{"college": c, "name": c["name"], "label": {"state": "target"}}], STUDENT)
            for n in out["cost_notes"]:
                low = n["text"].lower()
                for banned in ("affordable", "cheap", "safe financially"):
                    self.assertNotIn(banned, low)
                self.assertTrue(n["text"].endswith(NO_PAY))


class TestInlineLabels(unittest.TestCase):
    def test_inline_rules_match_contract(self):
        stu = {"sat": 1300}
        f = balance._inline_label
        self.assertEqual(f(stu, col(rate=0.1))["state"], "reach_for_everyone")
        self.assertEqual(f(stu, col(rate=None))["state"], "cant_say")
        self.assertEqual(f({}, col())["state"], "cant_say")
        self.assertEqual(f({"sat": 1100}, col(rate=0.5))["state"], "reach")
        self.assertEqual(f({"sat": 1300}, col(rate=0.5))["state"], "target")
        self.assertEqual(f({"sat": 1400}, col(rate=0.5))["state"], "likely")
        self.assertEqual(f({"sat": 1400}, col(rate=0.3))["state"], "target")  # >=75th but admit rate under 40%
        self.assertEqual(f({"sat": 1300}, col(sat25=None, sat75=None, act25=25, act75=30))["state"], "cant_say")


if __name__ == "__main__":
    unittest.main()
