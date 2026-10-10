"""Tests for engine/colleges.py: loading, the old-file fallback, name resolution, net price fields, cost_sentence.
No network, no model."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from engine import colleges
from engine.colleges import INCOME_BANDS, cost_sentence, find_college, load_colleges

DATA = Path(__file__).resolve().parent.parent / "data" / "colleges"

# (what a person types, the Scorecard name it must resolve to)
WELL_KNOWN = [
    ("Cornell", "Cornell University"), ("Harvard", "Harvard University"), ("MIT", "Massachusetts Institute of Technology"),
    ("Stanford", "Stanford University"), ("Purdue", "Purdue University-Main Campus"),
    ("Rutgers", "Rutgers University-New Brunswick"), ("Penn State", "Pennsylvania State University-Main Campus"),
    ("UCLA", "University of California-Los Angeles"), ("Berkeley", "University of California-Berkeley"),
    ("Michigan", "University of Michigan-Ann Arbor"), ("Georgia Tech", "Georgia Institute of Technology-Main Campus"),
    ("Duke", "Duke University"), ("Yale", "Yale University"), ("Princeton", "Princeton University"),
    ("Brown", "Brown University"), ("Columbia", "Columbia University in the City of New York"),
    ("Northwestern", "Northwestern University"), ("Vanderbilt", "Vanderbilt University"), ("Rice", "Rice University"),
    ("NYU", "New York University"), ("Boston University", "Boston University"), ("UT Austin", "The University of Texas at Austin"),
    ("Ohio State", "Ohio State University-Main Campus"), ("WashU", "Washington University in St Louis"),
    ("Texas A&M", "Texas A&M University-College Station"), ("Hopkins", "Johns Hopkins University"),
    ("CMU", "Carnegie Mellon University"), ("Pitt", "University of Pittsburgh-Pittsburgh Campus"),
]
BANNED = re.compile(r"affordable|cheap|safe", re.I)
DISCLAIMER = "What your family would pay can differ; use the college's own net price calculator."


def col(**kw):
    base = {"name": "Test University", "state": "NJ", "control": "private", "cost_year": 60400, "tuition_in": 50000,
            "tuition_out": 50000, "net_price": 31600,
            "net_price_by_income": {"0-30k": 9400, "30-48k": 14400, "48-75k": 22600, "75-110k": 30100, "110k+": 47000}}
    base.update(kw)
    return base


class Loading(unittest.TestCase):
    def test_full_file_is_used_and_big(self):
        self.assertTrue((DATA / "scorecard_colleges.csv").exists())
        cs = load_colleges()
        self.assertGreater(len(cs), 1200)
        self.assertEqual(len({c["id"] for c in cs}), len(cs))

    def test_every_college_has_all_keys(self):
        keys = {"id", "name", "city", "state", "control", "admit_rate", "sat25", "sat75", "act25", "act75", "undergrads",
                "cost_year", "tuition_in", "tuition_out", "pell_share", "grad_rate", "net_price", "net_price_by_income",
                "median_debt", "loan_share", "url", "source"}
        for c in load_colleges():
            self.assertTrue(keys <= set(c), c["name"])
            self.assertEqual(tuple(c["net_price_by_income"]), INCOME_BANDS)
            self.assertIn(c["control"], ("public", "private"))
            self.assertIsNotNone(c["admit_rate"])

    def test_missing_markers_become_none(self):
        for c in load_colleges():
            for k in ("sat25", "net_price", "median_debt", "cost_year"):
                self.assertNotIsInstance(c[k], str)
        self.assertIsNone(colleges._num("PrivacySuppressed"))
        self.assertIsNone(colleges._num("NULL"))
        self.assertIsNone(colleges._num("NA"))
        self.assertIsNone(colleges._num(""))

    def test_net_price_present_for_most(self):
        cs = load_colleges()
        self.assertGreaterEqual(sum(1 for c in cs if c["net_price"] is not None), 800)
        self.assertGreaterEqual(sum(1 for c in cs if c["net_price_by_income"]["0-30k"] is not None), 800)
        self.assertGreaterEqual(sum(1 for c in cs if c["median_debt"] is not None), 800)
        self.assertGreaterEqual(sum(1 for c in cs if c["cost_year"] is not None), 800)

    def test_net_price_uses_the_right_sector(self):
        cornell = find_college("Cornell")
        self.assertEqual(cornell["control"], "private")
        self.assertGreater(cornell["net_price"], 10000)
        purdue = find_college("Purdue")
        self.assertEqual(purdue["control"], "public")
        self.assertLess(purdue["net_price"], purdue["cost_year"])

    def test_existing_values_keep_their_meaning(self):
        c = find_college("Cornell")
        self.assertEqual(c["state"], "NY")
        self.assertLess(c["admit_rate"], 0.15)
        self.assertGreater(c["sat75"], c["sat25"])


class Fallback(unittest.TestCase):
    """With scorecard_colleges.csv absent the two older files are read, and the old behaviour holds."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "colleges").mkdir()
        for f in colleges.OLD_FILES + ("sat_act_concordance.csv",):
            shutil.copy(DATA / f, self.tmp / "colleges" / f)
        self.real = colleges.DATA
        colleges.DATA = self.tmp
        self._clear()
        self.addCleanup(self.restore)

    def _clear(self):
        colleges.load_colleges.cache_clear()
        colleges._index.cache_clear()

    def restore(self):
        colleges.DATA = self.real
        self._clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_old_files_are_read(self):
        cs = load_colleges()
        self.assertEqual(len(cs), 1130)
        self.assertEqual(find_college("Cornell")["name"], "Cornell University")

    def test_new_fields_are_none_without_the_full_file(self):
        for c in load_colleges():
            self.assertIsNone(c["net_price"])
            self.assertIsNone(c["median_debt"])
            self.assertEqual(c["net_price_by_income"], {b: None for b in INCOME_BANDS})

    def test_cost_sentence_is_none_for_a_college_with_no_cost(self):
        more = [c for c in load_colleges() if c["cost_year"] is None and c["net_price"] is None]
        self.assertGreater(len(more), 100)
        self.assertIsNone(cost_sentence(more[0], "NJ", "30-48k"))

    def test_old_names_and_aliases_resolve(self):
        for short, full in WELL_KNOWN:
            self.assertIsNotNone(find_college(short), short)


class NameResolution(unittest.TestCase):
    def test_well_known_short_and_full_names(self):
        for short, full in WELL_KNOWN:
            c = find_college(short)
            self.assertIsNotNone(c, short)
            self.assertEqual(c["name"], full, short)
            self.assertIs(find_college(full), c)
            self.assertIs(find_college(full.upper()), c)
            self.assertIs(find_college(c["id"]), c)

    def test_every_case_file_name_resolves(self):
        self.assertEqual([s for s in colleges.CASE_NAME_TO_SCORECARD if find_college(s) is None], [])

    def test_every_alias_resolves_to_its_full_name(self):
        for alias, full in colleges.EXTRA_ALIASES.items():
            c = find_college(alias)
            self.assertIsNotNone(c, alias)
            self.assertEqual(c["name"], full, alias)

    def test_old_names_still_found_by_id_or_rename(self):
        # a college renamed in the newer federal file is still found by its old name
        old = {r["UNITID"]: r["INSTNM"] for r in colleges._read_rows(colleges.OLD_FILES)}
        ids = {c["id"] for c in load_colleges()}
        for uid, name in old.items():
            if uid in ids:
                self.assertEqual(find_college(name)["id"], uid, name)
        self.assertEqual(find_college("Edgewood College")["id"], find_college("Edgewood University")["id"])

    def test_four_case_file_colleges_now_found(self):
        for s in ("CALTECH", "FORDHAM", "HARVEY MUDD", "UCM"):
            self.assertIsNotNone(find_college(s), s)

    def test_unknown_name_is_none(self):
        self.assertIsNone(find_college("Hogwarts School"))
        self.assertIsNone(find_college(""))
        self.assertIsNone(find_college(None))


class CostSentence(unittest.TestCase):
    def test_income_band_case(self):
        s = cost_sentence(col(cost_year=36400), None, "30-48k")
        self.assertEqual(s, "Sticker cost is about $36,000 a year. Families like yours paid about $14,000 on average after "
                            "grants (federal data, families earning $30,000 to $48,000). " + DISCLAIMER)

    def test_public_in_state_sticker(self):
        s = cost_sentence(col(control="public", cost_year=36400, net_price=18200), "NJ", "30-48k")
        self.assertTrue(s.startswith("Sticker cost is about $36,000 a year in-state. Families like yours paid about $14,000"))

    def test_overall_case(self):
        s = cost_sentence(col(cost_year=None, net_price=18400, net_price_by_income={b: None for b in INCOME_BANDS}),
                          None, "30-48k")
        self.assertEqual(s, "The average family paid about $18,000 after grants. " + DISCLAIMER)

    def test_overall_when_no_band_given(self):
        s = cost_sentence(col(cost_year=None, net_price=17600))
        self.assertIn("The average family paid about $18,000 after grants.", s)
        self.assertNotIn("Families like yours", s)

    def test_sticker_only_case(self):
        s = cost_sentence(col(net_price=None, net_price_by_income={b: None for b in INCOME_BANDS}))
        self.assertEqual(s, "Sticker cost is about $60,000 a year. " + DISCLAIMER)

    def test_nothing_known_is_none(self):
        self.assertIsNone(cost_sentence(col(cost_year=None, net_price=None, net_price_by_income={})))
        self.assertIsNone(cost_sentence(None))

    def test_out_of_state_public(self):
        c = col(control="public", state="NJ", cost_year=30000, tuition_in=12000, tuition_out=30000, net_price=15000)
        s = cost_sentence(c, "CA", "30-48k")
        self.assertIn("about $48,000 a year for students from out of state", s)
        self.assertNotIn("after grants", s)
        self.assertTrue(s.endswith(DISCLAIMER))

    def test_rounds_to_nearest_thousand(self):
        self.assertIn("$14,000", cost_sentence(col(), None, "30-48k"))  # 14,400
        self.assertIn("$23,000", cost_sentence(col(), None, "48-75k"))  # 22,600
        self.assertEqual(colleges._dollars(13500), "$14,000")
        self.assertEqual(colleges._dollars(13499), "$13,000")

    def test_every_band_has_wording(self):
        for band in INCOME_BANDS:
            self.assertIn("Families like yours paid", cost_sentence(col(), None, band))

    def test_banned_words_never_appear_on_real_colleges(self):
        for c in load_colleges():
            for band in (None,) + INCOME_BANDS:
                for home in (None, c["state"], "ZZ"):
                    s = cost_sentence(c, home, band)
                    if s is not None:
                        self.assertIsNone(BANNED.search(s), s)
                        self.assertTrue(s.endswith(DISCLAIMER))
                        self.assertNotRegex(s, r"\$\d+,(?!000)\d{3}")  # every dollar figure is a whole thousand

    def test_real_college_sentence(self):
        s = cost_sentence(find_college("Cornell"), "NJ", "0-30k")
        self.assertIn("Sticker cost is about", s)
        self.assertIn("families earning up to $30,000", s)


if __name__ == "__main__":
    unittest.main()
