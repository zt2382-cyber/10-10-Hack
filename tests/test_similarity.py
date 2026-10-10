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
        self.assertEqual(set(S.WEIGHTS), {"score", "activities", "major", "hooks", "residency", "gpa", "essay", "activity_text"})
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
        self.assertEqual(r["student"], {"score": 1450, "converted": False, "activities": None})

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
        self.assertEqual(n["n_admitted"] + n["n_denied"], 0)
        self.assertNotIn("lean", n)
        self.assertNotIn("steady", n)

    def test_own_status_is_not_enough_for_the_synthetic_store(self):
        # The invented school history is deeper now, so look for any college where it is still thin.
        from engine import colleges as _C
        thin = None
        for c in _C.load_colleges():
            o = S.closeness(STUDENT, c)["own"]
            if o["status"] == "not_enough":
                thin = o
                break
        self.assertIsNotNone(thin, "expected at least one college with too few of the school's own cases")
        self.assertTrue(thin["n_admitted"] + thin["n_denied"] > 0)

    def test_pools_are_never_merged(self):
        r = S.closeness(STUDENT, col("Rutgers University-New Brunswick"))
        for ex in r["national"].get("nearest_admitted", []) + r["national"].get("nearest_denied", []):
            self.assertTrue(ex["case_id"].startswith("N-"))
        for ex in r["own"].get("nearest_admitted", []) + r["own"].get("nearest_denied", []):
            self.assertTrue(ex["case_id"].startswith("S-"))
        for p in r["national"].get("points", []):
            self.assertTrue(p["case_id"].startswith("N-"))
        from engine import caselog as _caselog
        self.assertLessEqual(r["own"]["n_admitted"] + r["own"]["n_denied"] + r["own"]["n_waitlisted"], len(_caselog.load_cases()))

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


class ChangesTests(unittest.TestCase):
    NEVER = ("hook", "legacy", "first-gen", "first_gen", "athlete", "urm", "state", "gpa", "grade", "income", "race",
             "gender", "invent", "inflat", "exaggerat") + FORBIDDEN

    def ok_pools(self):
        for nm, s in (("Cornell University", STUDENT), ("Purdue University-Main Campus", dict(STUDENT, activities_rating=5)),
                      ("New York University", dict(STUDENT, sat=1350, intended_major="Psychology", home_state="NY")),
                      ("Tufts University", dict(STUDENT, sat=1350, major_interests=["Psychology", "Biology"]))):
            n = S.closeness(s, col(nm))["national"]
            if n["status"] == "ok":
                yield nm, s, n

    def test_shape_order_and_gain(self):
        seen_any = False
        for nm, s, n in self.ok_pools():
            ch = n["changes"]
            self.assertLessEqual(len(ch), 3)
            self.assertEqual([c["gap_after"] for c in ch], sorted((c["gap_after"] for c in ch), reverse=True))
            for c in ch:
                seen_any = True
                self.assertEqual(set(c), {"change", "gap_before", "gap_after", "lean_after", "because"})
                self.assertAlmostEqual(c["gap_before"], n["gap"], places=3)
                self.assertGreaterEqual(c["gap_after"] - c["gap_before"], S.CHANGE_GAIN - 1e-6)
                self.assertIn(c["lean_after"], ("closer_to_admitted", "closer_to_denied", "in_between"))
                self.assertTrue(1 <= len(c["because"]) <= 3)
                self.assertTrue(all(i.startswith("N-") for i in c["because"]))
            self.assertEqual(n["changes_note"], "" if ch else S.NOTHING_HELPS)
        self.assertTrue(seen_any, "expected at least one college with a change that helps")

    def test_never_touches_who_the_student_is(self):
        for nm, s, n in self.ok_pools():
            for c in n["changes"]:
                low = c["change"].lower()
                for bad in self.NEVER:
                    self.assertNotIn(bad, low, c["change"])
        for bad in self.NEVER:
            self.assertNotIn(bad, S.NOTHING_HELPS.lower())

    def test_tries_cover_only_score_activities_and_named_majors(self):
        c = col("Cornell University")
        sv = S._student_view(STUDENT, c)
        kinds = [t[0].split()[0] for t in S._tries(sv)]
        self.assertEqual(kinds, ["Score", "Score", "Score"])   # no rating, one major: score only
        sv = S._student_view(dict(STUDENT, activities_rating=9.5), c)
        names = [t[0] for t in S._tries(sv)]
        self.assertEqual(sum(1 for n in names if n.startswith("Activities")), 1)   # 9.5 -> 10 once, not twice
        self.assertIn("deeper involvement in the activities already listed", names[-1])
        sv = S._student_view(dict(STUDENT, sat=1600), c)
        self.assertFalse(any(n.startswith("Score") for n, _ in S._tries(sv)))
        sv = S._student_view(dict(STUDENT, sat=1580), c)
        scores = [v["score"] for n, v in S._tries(sv) if n.startswith("Score")]
        self.assertEqual(scores, [1600])   # 30, 60 and 100 all cap at 1600: tried once
        sv = S._student_view(dict(STUDENT, major_interests=["Computer Science", "Biology"]), c)
        majors = [(n, v) for n, v in S._tries(sv) if n.startswith("Intended major")]
        self.assertEqual(len(majors), 1)
        self.assertEqual(majors[0][1]["major_group"], "BIO")
        self.assertIn("BIO", majors[0][0])
        for _, v in S._tries(sv):   # nothing about who the student is ever moves
            self.assertEqual(v["hooks"], sv["hooks"])
            self.assertEqual(v["home_state"], sv["home_state"])
            self.assertEqual(v["gpa"], sv["gpa"])

    def test_no_changes_when_status_is_not_ok(self):
        n = S.closeness(STUDENT, college_by_case_name("CLAREMONT MCKENNA"))["national"]
        self.assertEqual(n["changes"], [])
        self.assertEqual(n["changes_note"], "")


class KindsTests(unittest.TestCase):
    def test_three_kinds_described_from_counts(self):
        kinds, kind_of = S._kinds("CORNELL")
        self.assertEqual([k["kind_id"] for k in kinds], ["K1", "K2", "K3"])
        n_adm = [v for v in S._national_groups("CORNELL")[0] if v["score"] is not None]
        self.assertEqual(sum(k["size"] for k in kinds), min(len(n_adm), S.KINDS_CAP))
        self.assertEqual(len(kind_of), min(len(n_adm), S.KINDS_CAP))
        ids = {v["case_id"] for v in n_adm}
        for k in kinds:
            self.assertIn(k["medoid_case_id"], ids)                    # a medoid is a real case
            self.assertEqual(kind_of[k["medoid_case_id"]], k["kind_id"])
            self.assertTrue(k["name"].split(" score")[0] in ("High", "Mid", "Lower"), k["name"])
            self.assertIsInstance(k["median_sat"], int)
            self.assertTrue(k["size"] >= 1)
        sats = [k["median_sat"] for k in kinds]
        self.assertEqual(sats, sorted(sats, reverse=True))              # K1 is the highest-scoring kind

    def test_fewer_than_30_admitted_gives_no_kinds(self):
        self.assertEqual(S._kinds("CLAREMONT MCKENNA"), ([], {}))
        n = S.closeness(STUDENT, college_by_case_name("CLAREMONT MCKENNA"))["national"]
        self.assertEqual(n["kinds"], [])
        self.assertTrue(all(p["kind_id"] is None for p in n["points"]))

    def test_same_input_gives_the_same_kinds(self):
        a = json.dumps(S._kinds("UPENN"), sort_keys=True, default=str)
        S._kinds.cache_clear()
        b = json.dumps(S._kinds("UPENN"), sort_keys=True, default=str)
        self.assertEqual(a, b)

    def test_kinds_in_the_block_mark_one_nearest_and_tag_points(self):
        n = S.closeness(STUDENT, col("Cornell University"))["national"]
        self.assertEqual(len(n["kinds"]), 3)
        self.assertEqual(sum(1 for k in n["kinds"] if k["nearest"]), 1)
        near = next(k for k in n["kinds"] if k["nearest"])
        self.assertEqual(near["distance"], min(k["distance"] for k in n["kinds"]))
        for k in n["kinds"]:
            self.assertEqual(set(k), {"kind_id", "name", "size", "median_sat", "median_activities", "top_major",
                                      "medoid_case_id", "distance", "nearest"})
        tagged = [p for p in n["points"] if p["kind_id"]]
        self.assertTrue(tagged)
        self.assertTrue(all(p["outcome"] == "admitted" for p in tagged))
        self.assertTrue(all(p["kind_id"] is None for p in n["points"] if p["outcome"] != "admitted"))

    def test_ten_cold_colleges_under_a_second(self):
        import time
        names = ["CORNELL", "MIT", "STANFORD", "CMU", "PRINCETON", "GEORGIA TECH", "PURDUE", "UPENN", "UMICH", "NYU"]
        names = [n for n in names if n in S._cases._national()[0]][:10]
        self.assertGreaterEqual(len(names), 8)
        for n in names:
            S._kinds.cache_clear()
        t = time.perf_counter()
        for n in names:
            S._kinds(n)
        self.assertLess(time.perf_counter() - t, 1.0)


def admitted_views(spec):
    """Synthetic admitted case views: (score, activities, major group, how many) per blob."""
    out, i = [], 0
    for score, act, major, k in spec:
        for j in range(k):
            i += 1
            out.append({"case_id": f"N-{i}", "num": i, "score": score + (j % 5) * 4, "activities": act + (j % 3) * 0.2,
                        "major_group": major, "hooks": frozenset({"NONE"}), "home_state": None, "gpa": None,
                        "outcome": "admitted", "row": {"hooks": "NONE"}})
    return out


class GroupsTests(unittest.TestCase):
    def setUp(self):
        self.cornell = col("Cornell University")
        self.sv = S._student_view(dict(STUDENT, activities_rating=6), self.cornell)
        self.groups = S._national_groups("CORNELL")

    def test_bands_follow_the_written_rule(self):
        self.assertEqual(S._score_band(1500, 1500, 1570), "inside")     # at the 25th: inside
        self.assertEqual(S._score_band(1570, 1500, 1570), "inside")     # at the 75th: inside
        self.assertEqual(S._score_band(1499, 1500, 1570), "below")
        self.assertEqual(S._score_band(1571, 1500, 1570), "above")
        self.assertEqual(S._act_band(5.9), "low")
        self.assertEqual(S._act_band(6), "mid")
        self.assertEqual(S._act_band(7.9), "mid")
        self.assertEqual(S._act_band(8), "high")

    def test_nine_cells_in_fixed_order_and_counts_add_up(self):
        g = S._groups_grid(self.sv, self.groups, self.cornell, own=False)
        self.assertEqual(g["status"], "ok")
        self.assertEqual((g["sat25"], g["sat75"]), (1500, 1570))
        self.assertEqual((g["act_mid"], g["act_high"], g["min_n"], g["few_n"]), (6, 8, 5, 15))
        self.assertEqual([(c["activities_band"], c["score_band"]) for c in g["cells"]],
                         [(a, s) for a in ("high", "mid", "low") for s in ("below", "inside", "above")])
        total = sum(len(group) for group in self.groups)
        self.assertEqual(sum(c["n"] for c in g["cells"]) + g["left_out"], total)
        self.assertFalse(g["capped"])
        for c in g["cells"]:
            self.assertEqual(c["n"], c["admitted"] + c["waitlisted"] + c["denied"])
            self.assertEqual(c["n"], len(c["cases"]))
            self.assertEqual(c["state"], "not_enough" if c["n"] < 5 else ("few" if c["n"] < 15 else "ok"))
            for case in c["cases"]:
                self.assertEqual(len(case), 6)
                self.assertIn(case[3], ("a", "w", "d"))
                self.assertEqual(S._score_band(case[1], 1500, 1570), c["score_band"])
                self.assertEqual(S._act_band(case[2]), c["activities_band"])
            gaps = [abs(case[1] - 1450) for case in c["cases"]]
            self.assertEqual(gaps, sorted(gaps))                        # closest score to the student first
        self.assertIn("rosier", g["caveat"])

    def test_student_cell_is_marked_once_and_notes_say_what_is_missing(self):
        g = S._groups_grid(self.sv, self.groups, self.cornell, own=False)
        mine = [c for c in g["cells"] if c["is_student"]]
        self.assertEqual(len(mine), 1)
        self.assertEqual((mine[0]["score_band"], mine[0]["activities_band"]), ("below", "mid"))
        self.assertEqual(g["student_note"], "")
        no_rating = S._groups_grid(S._student_view(STUDENT, self.cornell), self.groups, self.cornell, own=False)
        self.assertFalse(any(c["is_student"] for c in no_rating["cells"]))
        self.assertIn("activities rating", no_rating["student_note"])
        no_score = S._groups_grid(S._student_view(dict(STUDENT, sat=None), self.cornell), self.groups, self.cornell, own=False)
        self.assertEqual(len(no_score["cells"]), 9)                     # the grid still draws
        self.assertFalse(any(c["is_student"] for c in no_score["cells"]))
        self.assertIn("score", no_score["student_note"])

    def test_not_enough_few_and_cant_say(self):
        few = S._groups_grid(self.sv, (admitted_views([(1520, 7, "CS", 4)]), [], []), self.cornell, own=False)
        cell = [c for c in few["cells"] if c["n"]][0]
        self.assertEqual((cell["n"], cell["state"]), (4, "not_enough"))
        some = S._groups_grid(self.sv, (admitted_views([(1520, 7, "CS", 9)]), [], []), self.cornell, own=False)
        self.assertEqual([c["state"] for c in some["cells"] if c["n"]], ["few"])
        ucla = col("University of California-Los Angeles")
        g = S._groups_grid(self.sv, S._national_groups("UCLA"), ucla, own=False)
        self.assertEqual(g["status"], "cant_say")
        self.assertIn("no middle score range", g["reason"])
        self.assertEqual(g["cells"], [])
        own = S._groups_grid(self.sv, self.groups, self.cornell, own=True)
        self.assertEqual(own["status"], "cant_say")
        self.assertIn("activities rating", own["reason"])
        empty = S._groups_grid(self.sv, ([], [], []), self.cornell, own=False)
        self.assertEqual(empty["status"], "cant_say")

    def test_cap_spreads_the_list_and_says_so(self):
        many = admitted_views([(1520, 7, "CS", 1000)])
        g = S._groups_grid(self.sv, (many, [], []), self.cornell, own=False)
        self.assertTrue(g["capped"])
        self.assertEqual(sum(c["n"] for c in g["cells"]), S.GROUPS_CAP)

    def test_groups_ride_inside_the_closeness_block(self):
        r = S.closeness(dict(STUDENT, activities_rating=6), self.cornell)
        self.assertEqual(r["national"]["groups"]["status"], "ok")
        self.assertEqual(r["own"]["groups"]["status"], "cant_say")
        self.assertIsNone(r["own"]["kinds_check"])
        self.assertEqual(r["national"]["kinds_check"]["verdict"], S._kinds_check("CORNELL")["verdict"])
        no_score = S.closeness(dict(STUDENT, sat=None), self.cornell)["national"]
        self.assertEqual(no_score["status"], "cant_say")
        self.assertEqual(len(no_score["groups"]["cells"]), 9)           # a cant_say pool still carries the grid
        for text in strings(r):
            for w in FORBIDDEN:
                self.assertNotIn(w, text.lower())


class KindsCheckTests(unittest.TestCase):
    def setUp(self):
        self.orig = S._national_groups
        blobs = admitted_views([(1200, 3, "BIO", 40), (1420, 6, "CS", 40), (1590, 9, "ENG", 40)])
        import random
        rng = random.Random(1)
        flat = admitted_views([(rng.randrange(1000, 1600, 10), rng.randrange(0, 11), rng.choice(["CS", "BIO", "ENG", "BUSINESS"]), 1)
                               for _ in range(120)])
        fake = {"BLOBS3": (blobs, [], []), "UNIFORM": (flat, [], [])}
        S._national_groups = lambda name: fake.get(name) or self.orig(name)
        S._kinds_check.cache_clear()
        S._kinds.cache_clear()
        self.addCleanup(setattr, S, "_national_groups", self.orig)
        self.addCleanup(S._kinds_check.cache_clear)
        self.addCleanup(S._kinds.cache_clear)

    def test_three_separated_blobs_are_clear(self):
        c = S._kinds_check("BLOBS3")
        self.assertEqual(c["verdict"], "clear")
        self.assertGreaterEqual(c["separation"], 0.9)
        self.assertGreaterEqual(c["separation"] - c["shuffled"], 0.05)
        self.assertGreaterEqual(c["stability"], 0.75)
        self.assertEqual(c["text"], S.KINDS_VERDICT_TEXT["clear"])
        self.assertEqual(c["needs"]["separation"], S.KINDS_SEPARATION)

    def test_one_uniform_blob_has_no_clear_kinds(self):
        c = S._kinds_check("UNIFORM")
        self.assertEqual(c["verdict"], "none")
        self.assertLess(c["separation"], S.KINDS_SEPARATION)

    def test_same_input_gives_the_same_numbers_and_no_kinds_gives_none(self):
        a = S._kinds_check("CORNELL")
        S._kinds_check.cache_clear()
        self.assertEqual(a, S._kinds_check("CORNELL"))
        self.assertEqual(set(a), {"separation", "shuffled", "stability", "verdict", "text", "needs"})
        self.assertIn(a["verdict"], ("clear", "loose", "none"))
        self.assertIsNone(S._kinds_check("CLAREMONT MCKENNA"))

    def test_silhouette_and_jaccard(self):
        D = [[0, 1, 9, 9], [1, 0, 9, 9], [9, 9, 0, 1], [9, 9, 1, 0]]
        self.assertAlmostEqual(S._silhouette(D, [0, 0, 2, 2]), 8 / 9)
        self.assertEqual(S._silhouette(D, [0, 0, 0, 0]), 0.0)
        self.assertEqual(S._jaccard({1, 2}, {2, 3}), 1 / 3)
        self.assertEqual(S._jaccard(set(), set()), 0.0)

    def test_a_large_college_checks_in_under_two_seconds(self):
        import time
        t = time.perf_counter()
        S._kinds_check("CORNELL")
        self.assertLess(time.perf_counter() - t, 2.0)


class MethodTests(unittest.TestCase):
    def test_method_reads_from_the_same_constants(self):
        m = S.method()
        self.assertEqual(m["groups"], {"act_mid": S.ACT_MID, "act_high": S.ACT_HIGH, "min_n": S.GROUP_MIN, "few_n": S.GROUP_FEW, "cap": S.GROUPS_CAP})
        self.assertEqual(m["kinds_check"]["separation"], S.KINDS_SEPARATION)
        self.assertEqual(m["kinds_check"]["stability"], S.KINDS_STABILITY)
        self.assertEqual({p["part"]: p["weight"] for p in m["parts"]}, S.WEIGHTS)
        self.assertEqual(m["neighbours"], S.NEIGHBOURS)
        self.assertEqual(m["lean_gap"], S.LEAN_GAP)
        self.assertEqual(m["kinds"]["seed"], S.KINDS_SEED)
        self.assertNotIn("essay text", m["never_used"])
        self.assertNotIn("activity descriptions", m["never_used"])
        self.assertTrue(all(not p["required"] for p in m["parts"]))
        self.assertIn("numpy", m["libraries"]["not_used"])
        for text in strings(m):
            for w in FORBIDDEN:
                self.assertNotIn(w, text.lower())
        json.dumps(m)   # plain data only


class CheckTests(unittest.TestCase):
    def test_small_check_is_deterministic_national_only_and_adds_up(self):
        a = S.check(n=60, seed=7)
        b = S.check(n=60, seed=7)
        for k in ("rows", "used", "sampled", "skipped_small_groups"):
            self.assertEqual(a[k], b[k])
        self.assertEqual(a["sampled"], 60)
        self.assertEqual(a["used"] + a["skipped_small_groups"], 60)
        self.assertEqual([r["lean"] for r in a["rows"]], ["closer_to_admitted", "in_between", "closer_to_denied"])
        for r in a["rows"]:
            self.assertEqual(r["n"], r["admitted"] + r["denied"])
        self.assertNotIn("synthetic", json.dumps(a).lower())
        for text in strings(a):
            for w in FORBIDDEN:
                self.assertNotIn(w, text.lower())
        self.assertNotEqual(json.dumps(S.check(n=60, seed=8)["rows"]), json.dumps(a["rows"]))


if __name__ == "__main__":
    unittest.main()
