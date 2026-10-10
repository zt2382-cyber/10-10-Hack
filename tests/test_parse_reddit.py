"""Tests for tools/parse_reddit_posts.py and engine/cases_parsed.py. Small hand-made posts; no network, no model."""
import csv
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import parse_reddit_posts as P  # noqa: E402
from engine import cases, cases_parsed  # noqa: E402

TS = "1648862612"  # March 2022


def post(body, title="t"):
    return P.parse_post(title, body, TS, Counter())


def parsed(body):
    rec, dec = post(body)
    assert rec is not None, dec
    return rec, dec


FILLER = "\nExtracurriculars: Robotics team captain, volunteer tutor\nAwards: school award\n"

BASIC = """Demographics
Gender: Female
Race/Ethnicity: Asian
Residence: Ohio
Type of School: Public magnet
Hooks: first-gen, legacy at Cornell
Intended Major(s): Computer Science
Academics
GPA (UW/W): 3.92 UW / 4.35 W
Rank: 8/65
# of Honors/AP/IB/Dual Enrollment/etc.: 11 APs
Standardized Testing
SAT: 1500+ superscore (780 EBRW 750 M)
Extracurriculars/Activities
1. Robotics team captain, state finalist
2. Volunteer tutor at the local library
Awards/Honors
1. School science award
Essays
Common App was about caring for my grandmother and moving to the US. 8/10
Decisions
Acceptances: Cornell (ED), UMich, Penn State
Waitlists: Duke
Rejections: Harvard, MIT
Additional Information
Thanks for reading, ask me anything.
"""


class Fields(unittest.TestCase):
    def test_sat_superscore_plus_and_components_in_parentheses(self):
        rec, _ = parsed(BASIC)
        self.assertEqual(rec["sat_total"], 1500)
        self.assertEqual(rec["sat_superscore"], "Y")

    def test_act_with_section_scores(self):
        body = BASIC.replace("SAT: 1500+ superscore (780 EBRW 750 M)", "SAT/ACT: 35 ACT (36E 35M 34R 36S)")
        rec, _ = parsed(body)
        self.assertEqual(rec["act_composite"], 35)
        self.assertEqual(rec["sat_total"], "")

    def test_sat_range_is_midpoint_and_wide_range_is_empty(self):
        rec, _ = parsed(BASIC.replace("1500+ superscore (780 EBRW 750 M)", "1480-1520"))
        self.assertEqual(rec["sat_total"], 1500)
        rec, _ = parsed(BASIC.replace("1500+ superscore (780 EBRW 750 M)", "1300-1500"))
        self.assertEqual(rec["sat_total"], "")

    def test_gpa_labels_rank_and_ap_count(self):
        rec, _ = parsed(BASIC)
        self.assertEqual((rec["gpa_unweighted"], rec["gpa_weighted"]), (3.92, 4.35))
        self.assertEqual(rec["class_rank_raw"], "8/65")
        self.assertAlmostEqual(rec["class_rank_top_pct"], 12.3)
        self.assertEqual(rec["ap_ib_count"], 11)

    def test_gpa_label_first_style_and_scale(self):
        rec, _ = parsed(BASIC.replace("GPA (UW/W): 3.92 UW / 4.35 W", "GPA: UW- 3.7 W- 4.2 (out of 5.0)"))
        self.assertEqual((rec["gpa_unweighted"], rec["gpa_weighted"]), (3.7, 4.2))
        rec, _ = parsed(BASIC.replace("GPA (UW/W): 3.92 UW / 4.35 W", "GPA: 3.9/4.0"))
        self.assertEqual((rec["gpa_unlabeled"], rec["gpa_scale"]), (3.9, "4.0"))

    def test_top_percent_rank(self):
        rec, _ = parsed(BASIC.replace("Rank: 8/65", "Rank: top 5%"))
        self.assertEqual(rec["class_rank_top_pct"], 5.0)

    def test_major_state_school_type_hooks(self):
        rec, _ = parsed(BASIC)
        self.assertEqual((rec["major_text"], rec["major_group"]), ("Computer Science", "CS"))
        self.assertEqual((rec["home_state"], rec["school_type"]), ("OH", "public"))
        self.assertEqual(rec["hooks"], "FIRST-GEN;LEGACY")

    def test_no_hook_when_negated(self):
        rec, _ = parsed(BASIC.replace("Hooks: first-gen, legacy at Cornell", "Hooks: no legacy, not first-gen"))
        self.assertEqual(rec["hooks"], "")

    def test_activity_and_essay_tags_and_rating(self):
        rec, _ = parsed(BASIC)
        self.assertIn("robotics", rec["activities_tags"])
        self.assertIn("volunteering", rec["activities_tags"])
        self.assertIn("family", rec["essay_themes"])
        self.assertIn("immigration", rec["essay_themes"])
        self.assertEqual(rec["essay_self_rating"], "8")
        self.assertTrue(rec["essay_topic"].startswith("Common App was about caring"))


class Decisions(unittest.TestCase):
    def outcomes(self, body):
        _, dec = parsed(body)
        return {(d["college_as_written"], d["outcome"], d["round"]) for d in dec}

    def test_lists_inline_commas_and_rounds(self):
        o = self.outcomes(BASIC)
        self.assertIn(("Cornell", "admitted", "ED"), o)
        self.assertIn(("UMich", "admitted", ""), o)
        self.assertIn(("Duke", "waitlisted", ""), o)
        self.assertIn(("MIT", "denied", ""), o)

    def test_bullets_and_one_line_per_school(self):
        body = BASIC.split("Decisions")[0] + """Decisions
Acceptances:
* Boston University (RD)
* UC Davis
Waitlists:
- Northwestern (RD)
Rejections:
1. Stanford (REA)
2. Yale
Additional Information
none
"""
        o = self.outcomes(body)
        self.assertIn(("Boston University", "admitted", "RD"), o)
        self.assertIn(("UC Davis", "admitted", ""), o)
        self.assertIn(("Stanford", "denied", "EA"), o)
        self.assertIn(("Yale", "denied", ""), o)

    def test_waitlist_arrow_accepted_and_deferred_to_rejected(self):
        body = BASIC.split("Decisions")[0] + """Decisions
Waitlists: UMich (WL -> accepted), Duke WL -> rejected
Rejections: Harvard REA: Deferred --> rejected
Additional Information
none
"""
        o = self.outcomes(body)
        self.assertIn(("UMich", "admitted", ""), o)
        self.assertIn(("Duke", "denied", ""), o)
        self.assertIn(("Harvard", "denied", "EA"), o)

    def test_emoji_outcomes(self):
        body = BASIC.split("Decisions")[0] + """Decisions
✅ Georgia Tech
❌ Stanford
⏳ Rice
Additional Information
none
"""
        o = self.outcomes(body)
        self.assertEqual({x[:2] for x in o}, {("Georgia Tech", "admitted"), ("Stanford", "denied"), ("Rice", "waitlisted")})

    def test_one_line_per_school_with_dash_outcome(self):
        body = BASIC.split("Decisions")[0] + """Decisions
Harvard (RD) - Rejected
UIUC - Accepted
Rice - Waitlisted
Additional Information
none
"""
        o = self.outcomes(body)
        self.assertEqual({x[:2] for x in o}, {("Harvard", "denied"), ("UIUC", "admitted"), ("Rice", "waitlisted")})

    def test_waiting_list_is_not_an_outcome(self):
        body = BASIC.split("Decisions")[0] + """Decisions
Acceptances: UMich
Waiting on: Princeton, Harvard
Additional Information
none
"""
        o = self.outcomes(body)
        self.assertEqual({x[:2] for x in o}, {("UMich", "admitted")})

    def test_college_mapping_uses_alias_table_and_keeps_unknown(self):
        _, dec = parsed(BASIC.replace("Penn State", "Penn State, Zzyzx Tech"))
        by = {d["college_as_written"]: d for d in dec}
        self.assertEqual(by["UMich"]["college_name"], "University of Michigan-Ann Arbor")
        self.assertEqual(by["Penn State"]["college_id"] != "", True)
        self.assertEqual(by["Zzyzx Tech"]["college_id"], "")


class PrivacyAndId(unittest.TestCase):
    def test_race_gender_not_stored_and_scrubbed_from_text(self):
        body = BASIC.replace("1. Robotics team captain, state finalist",
                             "1. Robotics team captain, one of two female members and the only Asian captain")
        rec, _ = parsed(body)
        blob = " ".join(str(v) for v in rec.values()).lower()
        for w in ("female", "asian", "gender", "race"):
            self.assertNotIn(w, blob)

    def test_username_link_and_name_never_kept(self):
        body = BASIC.replace("2. Volunteer tutor at the local library",
                             "2. Volunteer tutor, see u/some_user_1 at https://example.com/x or mail me@example.com")
        rec, _ = parsed(body)
        blob = " ".join(str(v) for v in rec.values())
        for bad in ("some_user_1", "example.com", "http"):
            self.assertNotIn(bad, blob)

    def test_personal_activity_field_dropped_whole(self):
        body = BASIC.replace("1. Robotics team captain, state finalist",
                             "1. Captain at Lincoln Park High School robotics, call me at 212-555-0147")
        rec, _ = parsed(body)
        self.assertEqual(rec["activities_summary"], "")
        self.assertEqual(rec["activities_tags"], "")
        self.assertNotIn("Lincoln", " ".join(str(v) for v in rec.values()))

    def test_id_is_hash_of_text_and_source_note(self):
        a, _ = parsed(BASIC)
        b, _ = parsed(BASIC)
        c, _ = parsed(BASIC + " extra")
        self.assertEqual(a["record_id"], b["record_id"])
        self.assertNotEqual(a["record_id"], c["record_id"])
        self.assertRegex(a["record_id"], r"^R-[0-9a-f]{12}$")
        self.assertEqual(a["source_note"], "self-described in a public Reddit post; not verified")

    def test_short_or_untemplated_posts_are_dropped(self):
        rec, why = post("What are my chances at Harvard? I have a 1500 and a 3.9 and I play violin. Thanks all." * 3)
        self.assertIsNone(rec)
        self.assertEqual(why, "not_template_post")
        rec, why = post("tiny")
        self.assertEqual(why, "too_short")


class AdapterShape(unittest.TestCase):
    def test_rows_match_national_shape_plus_two_fields(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            raw = tmp / "raw.csv"
            with open(raw, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["Upvotes", "Date", "Title", "Body Text", "Link"])
                w.writerow(["1", TS, "t", BASIC, "https://x/comments/abc123/x/"])
                w.writerow(["1", TS, "t2", BASIC.replace("Computer Science", "Biology") + " more", "https://x/comments/def456/x/"])
            out = tmp / "parsed"
            P.run(raw, out)
            self.assertIn("not verified", (out / "applicants.csv").read_text(encoding="utf-8").splitlines()[0])
            applicants, decisions = cases_parsed.load(out)
            self.assertEqual(len(applicants), 2)
            self.assertTrue(all(d["source_note"] == P.SOURCE_NOTE for d in decisions))
            rows = cases_parsed.as_national_rows(out)
            self.assertIn("MIT", rows)  # keyed by the case-file short name when there is one
            ref = next(iter(cases._national()[0].values()))[0]
            row = rows["MIT"][0]
            self.assertEqual({r["group"] for r in rows["MIT"]}, {"CS", "BIO"})
            self.assertEqual(set(row) - {"activities_tags", "essay_themes"}, set(ref))
            self.assertIsInstance(row["hooks_set"], set)
            self.assertIn(row["outcome"], ("admitted", "denied", "waitlisted"))
            self.assertIsInstance(row["activities_tags"], list)
            self.assertEqual(row["sat"], 1500)
            self.assertTrue(row["case_id"].startswith("P-"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
