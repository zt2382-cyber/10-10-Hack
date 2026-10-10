import json
import unittest

from engine import colleges, similarity as S

STUDENT = {"label": "Student A (SYNTHETIC)", "sat": 1450, "home_state": "NJ", "intended_major": "Computer Science",
           "hooks": ["first_gen"], "gpa": 3.9, "gpa_scale": 4.0}
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


def col(name):
    c = colleges.find_college(name)
    assert c is not None, name
    return c


def case(**kw):
    """A national-style row with the given fields, as cases._national() would hand it over."""
    row = {"case_id": "N-1", "num": 1, "sat": None, "act": None, "score": None, "major": None, "group": None,
           "hooks_set": {"NONE"}, "hooks": "NONE", "home_state": None, "rating": None, "outcome": "admitted"}
    row.update(kw)
    return row


class DistanceTests(unittest.TestCase):
    def setUp(self):
        self.public = col("Purdue University-Main Campus")   # IN, public
        self.private = col("Cornell University")             # NY, private

    def test_identical_case_is_zero(self):
        sv = S._student_view(dict(STUDENT, activities_rating=6, home_state="IN"), self.public)
        cv = S._case_view(case(score=1450, group="CS", hooks_set={"FIRST-GEN"}, home_state="IN", rating=6))
        parts = S.part_distances(sv, cv, self.public)
        self.assertEqual(set(parts), {"score", "activities", "major", "hooks", "residency"})
        self.assertTrue(all(v == 0 for v in parts.values()), parts)
        self.assertEqual(S.total(parts), 0.0)

    def test_nearer_score_is_nearer(self):
        sv = S._student_view(dict(STUDENT, sat=1500), self.private)
        near = S._case_view(case(score=1480, group="CS", hooks_set={"FIRST-GEN"}))
        far = S._case_view(case(score=1200, group="CS", hooks_set={"FIRST-GEN"}))
        dn, df = S.total(S.part_distances(sv, near, self.private)), S.total(S.part_distances(sv, far, self.private))
        self.assertLess(dn, df)
        self.assertAlmostEqual(S.part_distances(sv, near, self.private)["score"], 20 / 400)
        self.assertEqual(S.part_distances(sv, far, self.private)["score"], 300 / 400)

    def test_score_distance_is_capped_at_one(self):
        sv = S._student_view(dict(STUDENT, sat=1600), self.private)
        cv = S._case_view(case(score=900))
        self.assertEqual(S.part_distances(sv, cv, self.private)["score"], 1.0)

    def test_missing_part_is_skipped_and_weights_renormalise(self):
        sv = S._student_view(dict(STUDENT, activities_rating=8), self.private)   # student has a rating
        cv = S._case_view(case(score=1410, group="CS", hooks_set={"FIRST-GEN"}))  # case has none
        parts = S.part_distances(sv, cv, self.private)
        self.assertNotIn("activities", parts)
        self.assertEqual(set(parts), {"score", "major", "hooks"})
        w = S.WEIGHTS
        expect = (w["score"] * (40 / 400) + w["major"] * 0 + w["hooks"] * 0) / (w["score"] + w["major"] + w["hooks"])
        self.assertAlmostEqual(S.total(parts), expect)

    def test_no_score_gives_no_distance(self):
        sv = S._student_view(dict(STUDENT, sat=None), self.private)
        cv = S._case_view(case(score=1450, group="CS"))
        parts = S.part_distances(sv, cv, self.private)
        self.assertNotIn("score", parts)
        self.assertIsNone(S.total(parts))
        self.assertIsNone(S.total({}))

    def test_act_is_converted_for_the_student(self):
        sv = S._student_view({"act": 33, "intended_major": "biology", "hooks": []}, self.private)
        self.assertEqual(sv["score"], colleges.act_to_sat(33))
        self.assertTrue(sv["converted"])

    def test_residency_only_at_public_colleges(self):
        in_state = dict(STUDENT, home_state="IN")
        sv_pub = S._student_view(in_state, self.public)
        sv_priv = S._student_view(in_state, self.private)
        same = S._case_view(case(score=1450, home_state="IN"))
        other = S._case_view(case(score=1450, home_state="CA"))
        self.assertEqual(S.part_distances(sv_pub, same, self.public)["residency"], 0.0)
        self.assertEqual(S.part_distances(sv_pub, other, self.public)["residency"], 1.0)
        self.assertNotIn("residency", S.part_distances(sv_priv, other, self.private))
        # two out-of-state people are "the same" for residency
        sv_ca = S._student_view(dict(STUDENT, home_state="CA"), self.public)
        tx = S._case_view(case(score=1450, home_state="TX"))
        self.assertEqual(S.part_distances(sv_ca, tx, self.public)["residency"], 0.0)
        # a case with no home state skips the part
        self.assertNotIn("residency", S.part_distances(sv_pub, S._case_view(case(score=1450)), self.public))

    def test_hooks_and_major_are_zero_or_one(self):
        sv = S._student_view(STUDENT, self.private)
        self.assertEqual(sv["major_group"], "CS")
        self.assertEqual(sv["hooks"], frozenset({"FIRST-GEN"}))
        a = S.part_distances(sv, S._case_view(case(score=1450, group="CS", hooks_set={"FIRST-GEN"})), self.private)
        b = S.part_distances(sv, S._case_view(case(score=1450, group="BIO", hooks_set={"NONE"})), self.private)
        self.assertEqual((a["major"], a["hooks"]), (0.0, 0.0))
        self.assertEqual((b["major"], b["hooks"]), (1.0, 1.0))
        # a case with no major leaves the part out
        self.assertNotIn("major", S.part_distances(sv, S._case_view(case(score=1450)), self.private))

    def test_major_from_reader_tag_only_when_student_gave_none_and_models_agreed(self):
        s = {"sat": 1450, "hooks": []}
        self.assertIsNone(S._student_view(s, self.private)["major_group"])
        self.assertEqual(S._student_view(s, self.private, {"major_group": "CS", "major_group_agreed": True})["major_group"], "CS")
        self.assertIsNone(S._student_view(s, self.private, {"major_group": "CS", "major_group_agreed": False})["major_group"])
        self.assertEqual(S._student_view(STUDENT, self.private, {"major_group": "BIO", "major_group_agreed": True})["major_group"], "CS")

    def test_gpa_part_only_when_both_sides_have_it(self):
        sv = S._student_view(STUDENT, self.private)
        self.assertAlmostEqual(sv["gpa"], 3.9)
        with_gpa = S._case_view(case(score=1450), gpa=3.4)
        without = S._case_view(case(score=1450))
        self.assertAlmostEqual(S.part_distances(sv, with_gpa, self.private)["gpa"], 0.5)
        self.assertNotIn("gpa", S.part_distances(sv, without, self.private))
        self.assertAlmostEqual(S._gpa(4.5, 5.0), 3.6)
        self.assertIsNone(S._gpa("x"))
        self.assertIsNone(S._gpa(4.5, 4.0))

    def test_major_interests_fall_back_to_intended_major(self):
        self.assertEqual(S._student_view(STUDENT, self.private)["major_interests"], ["CS"])
        sv = S._student_view(dict(STUDENT, major_interests=["Computer Science", "Mechanical Engineering", "software"]), self.private)
        self.assertEqual(sv["major_interests"], ["CS", "ENG"])

    def test_weights_cover_every_part_and_are_positive(self):
        self.assertEqual(set(S.WEIGHTS), {"score", "activities", "major", "hooks", "residency", "gpa"})
        self.assertTrue(all(w > 0 for w in S.WEIGHTS.values()))
        self.assertEqual(set(S.PART_WORD), set(S.WEIGHTS))


def college_by_case_name(short):
    return next(c for c in colleges.load_colleges() if colleges.case_name_for(c) == short)


class ClosenessTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from engine import caselog
        self.tmp = tempfile.TemporaryDirectory()
        caselog.set_store_path(Path(self.tmp.name) / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)

    def test_ok_block_has_the_contract_shape(self):
        r = S.closeness(STUDENT, col("Cornell University"))
        self.assertEqual(r["needed"], 15)
        self.assertEqual(r["neighbours"], 7)
        n = r["national"]
        self.assertEqual(n["status"], "ok")
        self.assertFalse(n["verified"])
        self.assertGreaterEqual(n["n_admitted"], 15)
        self.assertGreaterEqual(n["n_denied"], 15)
        for k in ("d_admitted", "d_denied", "gap", "lean", "text", "steady", "flips", "parts", "not_used",
                  "nearest_admitted", "nearest_denied", "kinds", "changes", "points"):
            self.assertIn(k, n, k)
        self.assertAlmostEqual(n["gap"], round(n["d_denied"] - n["d_admitted"], 3), places=3)
        self.assertIn(n["lean"], ("closer_to_admitted", "closer_to_denied", "in_between"))
        self.assertEqual(n["text"], S.LEAN_TEXT[n["lean"]])
        self.assertEqual(n["steady"], n["flips"] == [])
        for f in n["flips"]:
            self.assertIn("cause", f)
            self.assertIn("to", f)
        self.assertTrue(r["own"]["verified"])
        self.assertIn("not a forecast", r["caveat"])

    def test_lean_follows_gap_and_threshold(self):
        self.assertEqual(S._lean(S.LEAN_GAP), "closer_to_admitted")
        self.assertEqual(S._lean(-S.LEAN_GAP), "closer_to_denied")
        self.assertEqual(S._lean(S.LEAN_GAP / 2), "in_between")
        self.assertEqual(S._lean(-S.LEAN_GAP / 2), "in_between")
        self.assertIsNone(S._lean(None))

    def test_not_enough_when_a_group_is_small(self):
        n = S.closeness(STUDENT, college_by_case_name("CLAREMONT MCKENNA"))["national"]
        self.assertEqual(n["status"], "not_enough")
        self.assertTrue(1 <= n["n_admitted"] < 15)
        self.assertIsNone(n["lean"])
        self.assertIsNone(n["steady"])
        self.assertEqual(n["flips"], [])
        self.assertIn("d_admitted", n)   # the rings still place a hollow dot
        n2 = S.closeness(STUDENT, college_by_case_name("RUTGERS"))["national"]
        self.assertEqual(n2["status"], "not_enough")
        self.assertTrue(1 <= n2["n_denied"] < 15)

    def test_none_when_no_cases(self):
        r = S.closeness(STUDENT, col("Barnard College"))
        for pool in ("own", "national"):
            self.assertEqual(r[pool]["status"], "none")
            self.assertEqual((r[pool]["n_admitted"], r[pool]["n_denied"]), (0, 0))
            self.assertNotIn("lean", r[pool])
        r2 = S.closeness(STUDENT, None)
        self.assertEqual(r2["national"]["status"], "none")
        self.assertEqual(r2["own"]["status"], "none")

    def test_cant_say_without_a_score_still_shows_counts(self):
        n = S.closeness(dict(STUDENT, sat=None), col("Cornell University"))["national"]
        self.assertEqual(n["status"], "cant_say")
        self.assertGreater(n["n_admitted"] + n["n_denied"], 0)
        self.assertNotIn("lean", n)
        self.assertNotIn("steady", n)

    def test_own_status_is_not_enough_for_the_synthetic_store(self):
        o = S.closeness(STUDENT, col("Rutgers University-New Brunswick"))["own"]
        self.assertEqual(o["status"], "not_enough")
        self.assertTrue(o["n_admitted"] + o["n_denied"] > 0)

    def test_pools_are_never_merged(self):
        r = S.closeness(STUDENT, col("Rutgers University-New Brunswick"))
        for ex in r["national"].get("nearest_admitted", []) + r["national"].get("nearest_denied", []):
            self.assertTrue(ex["case_id"].startswith("N-"))
        for ex in r["own"].get("nearest_admitted", []) + r["own"].get("nearest_denied", []):
            self.assertTrue(ex["case_id"].startswith("S-"))
        for p in r["national"].get("points", []):
            self.assertTrue(p["case_id"].startswith("N-"))
        self.assertLessEqual(r["own"]["n_admitted"] + r["own"]["n_denied"] + r["own"]["n_waitlisted"], 120)

    def test_nearest_examples_are_near_and_typed(self):
        n = S.closeness(STUDENT, col("Purdue University-Main Campus"))["national"]
        self.assertTrue(1 <= len(n["nearest_admitted"]) <= 3)
        self.assertTrue(1 <= len(n["nearest_denied"]) <= 3)
        for ex in n["nearest_admitted"]:
            self.assertEqual(ex["outcome"], "admitted")
        for ex in n["nearest_denied"]:
            self.assertEqual(ex["outcome"], "denied")
        for ex in n["nearest_admitted"] + n["nearest_denied"]:
            self.assertIn("distance", ex)
            self.assertIn("score", ex["parts"])
            self.assertTrue(set(ex["parts"]) <= set(S.WEIGHTS))
            for bad in ("gender", "race", "income"):
                self.assertNotIn(bad, json.dumps(ex).lower())
        ds = [ex["distance"] for ex in n["nearest_admitted"]]
        self.assertEqual(ds, sorted(ds))
        self.assertLessEqual(ds[-1], n["d_admitted"] + 1e-9)   # the 3 shown are the nearest of the 7

    def test_parts_and_not_used(self):
        n = S.closeness(STUDENT, col("Cornell University"))["national"]
        names = [p["part"] for p in n["parts"]]
        self.assertIn("score", names)
        self.assertNotIn("activities", names)   # the student gave no rating
        for p in n["parts"]:
            self.assertIn(p["text"], ("close", "some way off", "far"))
            self.assertTrue(0 <= p["distance"] <= 1)
        self.assertIn("GPA", n["not_used"])
        self.assertIn("activities rating", n["not_used"])
        self.assertIn("residency (private college)", n["not_used"])
        self.assertIn("essay", n["not_used"])
        self.assertIn("activity descriptions", n["not_used"])
        pub = S.closeness(dict(STUDENT, activities_rating=7), col("Purdue University-Main Campus"))["national"]
        self.assertNotIn("residency (private college)", pub["not_used"])
        self.assertNotIn("activities rating", pub["not_used"])
        self.assertIn("activities", [p["part"] for p in pub["parts"]])

    def test_points_are_capped_and_typed(self):
        n = S.closeness(STUDENT, college_by_case_name("UPENN"))["national"]
        self.assertEqual(len(n["points"]), 300)
        self.assertGreater(n["n_admitted"] + n["n_denied"] + n["n_waitlisted"], 300)
        for p in n["points"]:
            self.assertEqual(set(p), {"case_id", "sat", "activities", "outcome", "kind_id"})
            self.assertIn(p["outcome"], ("admitted", "denied", "waitlisted"))
            self.assertIsNotNone(p["sat"])

    def test_high_score_student_is_nearer_admitted_than_a_low_score_student(self):
        c = col("Purdue University-Main Campus")
        high = S.closeness(dict(STUDENT, sat=1580), c)["national"]
        low = S.closeness(dict(STUDENT, sat=1100), c)["national"]
        self.assertGreater(high["gap"], low["gap"])
        self.assertEqual(high["lean"], "closer_to_admitted")

    def test_deterministic(self):
        c = col("Cornell University")
        a = json.dumps(S.closeness(STUDENT, c), sort_keys=True)
        b = json.dumps(S.closeness(dict(STUDENT), c), sort_keys=True)
        self.assertEqual(a, b)

    def test_no_forbidden_words_anywhere(self):
        for nm in ("Cornell University", "Purdue University-Main Campus", "Rutgers University-New Brunswick",
                   "Barnard College", "Princeton University"):
            for s in (STUDENT, {"label": "x"}, {"act": 30, "intended_major": "biology"}, dict(STUDENT, sat=1580)):
                r = S.closeness(s, colleges.find_college(nm), tags={"essay_themes": ["family"]})
                for text in strings(r):
                    low = text.lower()
                    for w in FORBIDDEN:
                        self.assertNotIn(w, low, text)
        for text in list(S.LEAN_TEXT.values()) + list(S.STATUS_TEXT.values()) + [S.CAVEAT]:
            for w in FORBIDDEN:
                self.assertNotIn(w, text.lower())


if __name__ == "__main__":
    unittest.main()
