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


if __name__ == "__main__":
    unittest.main()
