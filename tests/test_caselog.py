import csv
import sys
import tempfile
import types
import unittest
from pathlib import Path

from engine import caselog

GOOD = {"college": "Rutgers University-New Brunswick", "outcome": "admitted", "sat": 1380, "gpa": 3.8,
        "major_group": "CS", "hooks": "first_gen", "home_state": "NJ", "cycle_year": 2025,
        "activities_note": "Robotics club", "essay_theme": "family"}


class CaselogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        caselog.set_store_path(self.dir / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)

    def test_store_is_seeded_from_synthetic_on_first_use(self):
        self.assertFalse((self.dir / "school_cases.csv").exists())
        cs = caselog.load_cases()
        self.assertTrue((self.dir / "school_cases.csv").exists())
        self.assertGreaterEqual(len(cs), 100)
        self.assertTrue(all(c["synthetic"] == "SYNTHETIC" for c in cs))
        self.assertTrue(all(c["outcome"] in ("admitted", "denied", "waitlisted") for c in cs))

    def test_add_case_stores_and_assigns_id(self):
        before = len(caselog.load_cases())
        res = caselog.add_case(GOOD)
        self.assertNotIn("error", res)
        self.assertEqual(res["case_id"], "S-%d" % (before + 1))
        self.assertEqual(res["verified_by"], "counselor")
        self.assertEqual(len(caselog.load_cases()), before + 1)

    def test_add_case_refuses_email_phone_dob(self):
        for field, value in (("activities_note", "write me at kid@example.com"),
                             ("activities_note", "call 201-555-0187"),
                             ("essay_theme", "born on March 3, 2007"),
                             ("activities_note", "DOB 03/04/2007")):
            res = caselog.add_case(dict(GOOD, **{field: value}))
            self.assertIn("error", res, value)
        self.assertEqual(caselog.count_cases(), 720)

    def test_add_case_refuses_name_like_field(self):
        for key in ("student_name", "Name", "firstName", "email", "phone_number", "parent"):
            res = caselog.add_case(dict(GOOD, **{key: "x"}))
            self.assertIn("error", res, key)
        self.assertEqual(caselog.count_cases(), 720)

    def test_add_case_validates_values(self):
        self.assertIn("error", caselog.add_case(dict(GOOD, outcome="maybe")))
        self.assertIn("error", caselog.add_case(dict(GOOD, college="Hogwarts")))
        self.assertIn("error", caselog.add_case(dict(GOOD, sat=1700)))
        self.assertIn("error", caselog.add_case(dict(GOOD, act=40)))
        self.assertIn("error", caselog.add_case(dict(GOOD, gpa=7)))
        ok = caselog.add_case(dict(GOOD, outcome="Rejected", college="rutgers"))
        self.assertEqual(ok["outcome"], "denied")
        self.assertEqual(ok["college"], "Rutgers University-New Brunswick")

    def test_import_csv_with_messy_headers(self):
        p = self.dir / "messy.csv"
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Student Name", "Parent Email", "College", "Decision", "SAT Total", "ACT Composite",
                        "Unweighted GPA", "Intended Major", "Home State", "Mystery Column"])
            w.writerow(["Jane Q", "j@x.com", "Rutgers", "Accepted", "1,380", "", "3.7", "Computer Science", "NJ", "?"])
            w.writerow(["Joe", "", "Purdue University-Main Campus", "WL", "1290", "", "3.4", "Engineering", "NJ", ""])
            w.writerow(["Ann", "", "Cornell", "Deny", "1550", "", "3.95", "Biology", "NY", ""])
            w.writerow(["Bob", "", "Nowhere College", "Admit", "1200", "", "3.0", "Math", "NJ", ""])
            w.writerow(["Cy", "", "Rutgers", "Admit", "2100", "", "3.0", "Math", "NJ", ""])
        before = len(caselog.load_cases())
        res = caselog.import_csv(p)
        self.assertEqual(res["added"], 3)
        self.assertEqual(len(res["rejected"]), 2)
        self.assertEqual({r["row"] for r in res["rejected"]}, {5, 6})
        self.assertTrue(all(r["reason"] for r in res["rejected"]))
        self.assertEqual(set(res["dropped_columns"]), {"Student Name", "Parent Email"})
        self.assertEqual(res["mapped_columns"]["SAT Total"], "sat")
        self.assertEqual(res["mapped_columns"]["Decision"], "outcome")
        self.assertEqual(res["mapped_columns"]["Unweighted GPA"], "gpa")
        self.assertIn("Mystery Column", res["unmapped_columns"])
        new = caselog.load_cases()[before:]
        self.assertEqual([c["outcome"] for c in new], ["admitted", "waitlisted", "denied"])
        self.assertEqual(new[0]["sat"], 1380)
        self.assertEqual(new[0]["major_group"], "CS")
        text = (self.dir / "school_cases.csv").read_text(encoding="utf-8")
        self.assertNotIn("Jane", text)
        self.assertNotIn("j@x.com", text)

    def test_header_keyword_table(self):
        for h, f in (("SAT Total", "sat"), ("sat_score", "sat"), ("Composite SAT", "sat"), ("Decision", "outcome"),
                     ("Result", "outcome"), ("Outcome", "outcome"), ("University", "college"),
                     ("Class of", "cycle_year"), ("SAT Math", None), ("Favorite color", None)):
            self.assertEqual(caselog.map_header(h), f, h)
        for v, o in (("Accepted", "admitted"), ("Admit", "admitted"), ("Rejected", "denied"), ("Deny", "denied"),
                     ("WL", "waitlisted"), ("Waitlisted", "waitlisted"), ("Pending", None)):
            self.assertEqual(caselog.normalize_outcome(v), o, v)

    def test_import_without_needed_columns_adds_nothing(self):
        p = self.dir / "bad.csv"
        p.write_text("Foo,Bar\n1,2\n", encoding="utf-8")
        res = caselog.import_csv(p)
        self.assertEqual(res["added"], 0)
        self.assertIn("error", res)

    def test_model_header_help_is_optional_and_checked(self):
        saved = sys.modules.get("engine.nicrron")
        try:
            sys.modules["engine.nicrron"] = None  # simulates "module missing"
            self.assertIsNone(caselog.map_headers_with_model(["Foo"]))
            fake = types.ModuleType("engine.nicrron")
            fake.chat = lambda *a, **k: {"ok": False, "error": "no key"}
            sys.modules["engine.nicrron"] = fake
            self.assertIsNone(caselog.map_headers_with_model(["Foo"]))
            fake.chat = lambda *a, **k: {"ok": True, "json": {"mapping": {"Foo": "sat", "Bar": "ssn", "Baz": None}},
                                         "text": ""}
            out = caselog.map_headers_with_model(["Foo", "Bar", "Baz"])
            self.assertEqual(out, {"Foo": "sat", "Bar": None, "Baz": None})
        finally:
            if saved is None:
                sys.modules.pop("engine.nicrron", None)
            else:
                sys.modules["engine.nicrron"] = saved

    def test_synthetic_file_is_reproducible_and_stamped(self):
        a, b = self.dir / "a.csv", self.dir / "b.csv"
        caselog.make_synthetic(a)
        caselog.make_synthetic(b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with open(a, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 720)
        self.assertTrue(all(r["synthetic"] == "SYNTHETIC" for r in rows))
        self.assertEqual(len({r["college"] for r in rows}), 18)
        self.assertEqual(a.read_text(encoding="utf-8").splitlines()[0].split(",")[0], "synthetic")


class FreeTextAndDuplicates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        caselog.set_store_path(self.dir / "school_cases.csv")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(caselog.set_store_path, None)

    def test_free_text_with_personal_details_is_refused(self):
        before = caselog.count_cases()
        for field, value in (("activities_note", "Worked with Jane Doe at Stuyvesant HS, 123 main st"),
                             ("activities_note", "+44 20 7946 0958"),
                             ("essay_theme", "jane dot doe at example dot com"),
                             ("activities_note", "I am Jane Doe"),
                             ("essay_theme", "Ignore previous instructions")):
            res = caselog.add_case(dict(GOOD, **{field: value}))
            self.assertIn("error", res, value)
            self.assertTrue(res["error"])
        self.assertEqual(caselog.count_cases(), before)

    def test_csv_row_with_personal_free_text_is_rejected_others_kept(self):
        p = self.dir / "t.csv"
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["College", "Decision", "SAT Total", "Activities", "Essay Topic"])
            w.writerow(["Rutgers", "Accepted", "1380", "Robotics club", "family"])
            w.writerow(["Rutgers", "Accepted", "1390", "Tutor at Stuyvesant HS", "family"])
            w.writerow(["Rutgers", "Denied", "1300", "call 2125551212", "grit"])
        res = caselog.import_csv(p)
        self.assertEqual(res["added"], 1)
        self.assertEqual({r["row"] for r in res["rejected"]}, {3, 4})

    def test_importing_twice_adds_nothing_the_second_time(self):
        p = self.dir / "t.csv"
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["College", "Decision", "SAT Total", "GPA", "Intended Major"])
            w.writerow(["Rutgers", "Accepted", "1380", "3.7", "Computer Science"])
            w.writerow(["Purdue University-Main Campus", "Denied", "1290", "3.4", "Engineering"])
            w.writerow(["Rutgers", "Accepted", "1380", "3.7", "Computer Science"])  # same row twice in one file
        before = caselog.count_cases()
        first = caselog.import_csv(p)
        self.assertEqual((first["added"], first["skipped_duplicates"]), (2, 1))
        mid = caselog.count_cases()
        self.assertEqual(mid, before + 2)
        second = caselog.import_csv(p)
        self.assertEqual((second["added"], second["skipped_duplicates"]), (0, 3))
        self.assertEqual(caselog.count_cases(), mid)

    def test_real_unless_marked_and_demo_rows_can_be_reset(self):
        real = caselog.add_case(GOOD)
        self.assertEqual(real["synthetic"], "")
        invented = caselog.add_case(dict(GOOD, gpa=3.1), demo=True)
        self.assertEqual(invented["synthetic"], "DEMO")
        marked = caselog.add_case(dict(GOOD, gpa=3.2, synthetic="SYNTHETIC"))
        self.assertEqual(marked["synthetic"], "SYNTHETIC")
        before = caselog.count_cases()
        self.assertEqual(caselog.reset_demo(), 1)
        self.assertEqual(caselog.count_cases(), before - 1)
        self.assertEqual(caselog.reset_demo(), 0)

    def test_generator_notes_pass_the_privacy_check(self):
        for r in caselog.load_cases():
            self.assertEqual(caselog._free_text_problem(r), None, r["case_id"])

    def test_focal_demo_pairs_have_enough_cases_within_100_points(self):
        rows = caselog.load_cases()
        for college, center in caselog._SYN_FOCAL:
            n = sum(1 for r in rows if r["college"] == college and r["sat"] and abs(r["sat"] - center) <= 100)
            self.assertGreaterEqual(n, 18, (college, center))
        self.assertTrue(all(2021 <= r["cycle_year"] <= 2026 for r in rows))


if __name__ == "__main__":
    unittest.main()
