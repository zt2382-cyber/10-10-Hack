import unittest

from engine import claims
from engine.colleges import find_college


def by_id(cl, cid):
    return next((c for c in cl if c["claim_id"] == cid), None)


class TestCollegeSays(unittest.TestCase):
    def test_known_college_c7_claim(self):
        cl = claims.college_says(find_college("Georgia Tech"))
        c = by_id(cl, "c7_essay")
        self.assertIsNotNone(c)
        self.assertIn("Georgia Tech rates the application essay as Important", c["text"])
        self.assertEqual(c["field"], "CDS C7")
        self.assertEqual(c["year"], "2025-26")
        self.assertTrue(c["source_url"].startswith("https://irp.gatech.edu"))
        self.assertIsNone(c["kb"])
        self.assertTrue(c["checked"])

    def test_claim_shape(self):
        for c in claims.college_says(find_college("Georgia Tech")):
            for k in ("claim_id", "text", "field", "year", "source_url", "numbers", "kb", "checked"):
                self.assertIn(k, c)
            self.assertTrue(c["checked"])

    def test_admit_total_numbers(self):
        c = by_id(claims.college_says(find_college("Georgia Tech")), "admit_total")
        self.assertIn("8,921 of 66,881", c["text"])
        self.assertIn("13.3%", c["text"])
        self.assertIn(8921, c["numbers"])

    def test_mit_counts_skipped(self):
        cl = claims.college_says(find_college("MIT"))
        self.assertIsNone(by_id(cl, "admit_total"))
        self.assertIsNone(by_id(cl, "admit_residency"))
        self.assertIsNotNone(by_id(cl, "waitlist"))  # other fields of that row still pass

    def test_michigan_c7_skipped(self):
        cl = claims.college_says(find_college("UMICH"))
        self.assertFalse([c for c in cl if c["field"] == "CDS C7"])
        self.assertIsNotNone(by_id(cl, "admit_total"))

    def test_college_with_no_row(self):
        rice = find_college("Rice University")
        self.assertIsNotNone(rice)
        self.assertEqual(claims.college_says(rice), [])
        self.assertEqual(claims.college_says(None), [])

    def test_residency_split_numbers(self):
        c = by_id(claims.college_says(find_college("Georgia Tech")), "admit_residency")
        for n in (3691, 12527, 4513, 44596, 716, 9758):
            self.assertIn(n, c["numbers"])
        self.assertIn("3,691 of 12,527 in-state", c["text"])
        self.assertIn("716 of 9,758 international", c["text"])

    def test_test_range_says_submitted(self):
        c = by_id(claims.college_says(find_college("Georgia Tech")), "test_range")
        self.assertIn("submitted", c["text"])
        self.assertIn("78%", c["text"])
        self.assertIn("1370-1530", c["text"])

    def test_suspect_waitlist_count_skipped(self):
        # UIUC and Berkeley show "1" admitted from a wait list of thousands: treated as a yes/no mark, not shown
        self.assertIsNone(by_id(claims.college_says(find_college("UIUC")), "waitlist"))

    def test_uva_year_corrected_by_flag(self):
        c = by_id(claims.college_says(find_college("UVA")), "admit_total")
        self.assertEqual(c["year"], "2024-25")

    def test_every_returned_claim_passes_recheck(self):
        for col in claims.load_colleges():
            for c in claims.college_says(col):
                row = claims.row_for(col)
                self.assertTrue(c["checked"])
                nums = c["numbers"]
                res = claims.check_sentence(c["text"], nums, {col["name"], claims._display(row)})
                self.assertTrue(res["ok"], (col["name"], c["text"], res["reason"]))


class TestCheckSentence(unittest.TestCase):
    ALLOWED = [8921, 66881, 13.3, 2025, 2026]
    NAMES = {"Georgia Tech"}
    GOOD = "In 2025-26, Georgia Tech admitted 8,921 of 66,881 first-year applicants (13.3%)."

    def test_true_sentence_passes(self):
        r = claims.check_sentence(self.GOOD, self.ALLOWED, self.NAMES)
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["reason"])

    def test_wrong_number_fails(self):
        r = claims.check_sentence(self.GOOD.replace("8,921", "8,912"), self.ALLOWED, self.NAMES)
        self.assertFalse(r["ok"])
        self.assertIn("8,912", r["reason"])

    def test_unknown_college_name_fails(self):
        r = claims.check_sentence(self.GOOD.replace("Georgia Tech", "Cornell"), self.ALLOWED, self.NAMES)
        self.assertFalse(r["ok"])
        self.assertIn("college", r["reason"])

    def test_name_variants_are_the_same_college(self):
        r = claims.check_sentence(self.GOOD.replace("Georgia Tech", "Georgia Institute of Technology"),
                                  self.ALLOWED, self.NAMES)
        self.assertTrue(r["ok"], r)

    def test_forbidden_phrase_fails(self):
        r = claims.check_sentence("Georgia Tech says your essay will help (13.3%).", self.ALLOWED, self.NAMES)
        self.assertFalse(r["ok"])
        self.assertIn("do not allow", r["reason"])

    def test_missing_caveat_fails(self):
        bad = "Among Georgia Tech enrolled first-year students the middle 50% scored 1370-1530."
        r = claims.check_sentence(bad, [50, 1370, 1530], self.NAMES)
        self.assertFalse(r["ok"])
        self.assertIn("submitted", r["reason"])
        ok = "Among Georgia Tech enrolled first-year students who submitted SAT scores the middle 50% scored 1370-1530."
        self.assertTrue(claims.check_sentence(ok, [50, 1370, 1530], self.NAMES)["ok"])

    def test_percent_matches_fraction(self):
        self.assertTrue(claims.check_sentence("Georgia Tech admitted 13.3% of applicants.", [0.133], self.NAMES)["ok"])
        self.assertTrue(claims.check_sentence("Georgia Tech admitted 13.3% of applicants.", [13.3], self.NAMES)["ok"])
        self.assertFalse(claims.check_sentence("Georgia Tech admitted 14.3% of applicants.", [0.133], self.NAMES)["ok"])

    def test_commas_ranges_dollars(self):
        t = "Georgia Tech lists $88,000 and a range of 1,370 to 1370-1530."
        self.assertTrue(claims.check_sentence(t, [88000, 1370, 1530], self.NAMES)["ok"] is False)  # 'submitted' missing
        t2 = "Georgia Tech lists $88,000 for students who submitted scores in the 1,370-1,530 range."
        self.assertTrue(claims.check_sentence(t2, [88000, 1370, 1530], self.NAMES)["ok"])
        self.assertFalse(claims.check_sentence(t2, [88000, 1370], self.NAMES)["ok"])

    def test_quote_must_be_listed(self):
        t = 'Georgia Tech says "very important".'
        self.assertFalse(claims.check_sentence(t, [], self.NAMES)["ok"])
        self.assertTrue(claims.check_sentence(t, [], self.NAMES, quotes=["Very Important"])["ok"])

    def test_c7_tag_is_not_a_number(self):
        t = "Georgia Tech rates class rank as Not Considered in section C7."
        self.assertTrue(claims.check_sentence(t, [], self.NAMES)["ok"])


class TestMythChecks(unittest.TestCase):
    def test_wording_for_known_college(self):
        ms = claims.myth_checks(find_college("Georgia Tech"))
        self.assertEqual(len(ms), 5)
        for m in ms:
            self.assertEqual(set(m) >= {"belief", "college_says", "source_url", "year"}, True)
        interest = next(m for m in ms if "interest" in m["belief"])
        self.assertIn("demonstrated interest", interest["college_says"])
        self.assertIn("Not Considered", interest["college_says"])
        self.assertEqual(interest["year"], "2025-26")
        self.assertTrue(interest["source_url"])

    def test_never_judges_the_belief(self):
        for col in ("Georgia Tech", "Stanford", "UCLA"):
            for m in claims.myth_checks(find_college(col)):
                low = m["college_says"].lower()
                for w in ("myth", "false", "true", "wrong", "correct"):
                    self.assertNotIn(w, low)
                res = claims.check_sentence(m["college_says"], [], {find_college(col)["name"], col})
                self.assertTrue(res["ok"], (col, m["college_says"], res["reason"]))

    def test_no_row_says_form_does_not_say(self):
        for m in claims.myth_checks(find_college("Rice University")):
            self.assertEqual(m["college_says"], "This college's form does not say.")
            self.assertIsNone(m["source_url"])

    def test_unreadable_row_is_not_reported_as_silence(self):
        for m in claims.myth_checks(find_college("UMICH")):
            self.assertNotEqual(m["college_says"], "This college's form does not say.")


class TestHelpers(unittest.TestCase):
    def test_kb_query_and_caveats(self):
        cl = claims.college_says(find_college("Georgia Tech"))
        for c in cl:
            q = claims.kb_query_for(c)
            self.assertTrue(q and len(q) < 160)
            self.assertNotIn("Georgia", q)
        self.assertGreaterEqual(len(claims.REQUIRED_CAVEATS), 3)
        self.assertTrue(all(isinstance(s, str) for s in claims.REQUIRED_CAVEATS))

    def test_all_24_rows_match_a_scorecard_college(self):
        self.assertEqual(claims.unmatched_rows(), [])


if __name__ == "__main__":
    unittest.main()
