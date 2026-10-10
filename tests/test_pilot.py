import unittest
from scripts.validate_pilot import validate
from admissions.documents import extract_freeform


class PilotTests(unittest.TestCase):
    def test_document_against_authored_expected_values(self):
        result = validate()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['activities_checked'], 3)
        self.assertEqual(result['courses_checked'], 4)

    def test_negated_score_and_essay_assertions_do_not_update_profile(self):
        records = extract_freeform('I have not submitted SAT: 1500\nPersonal statement:\nI was captain of the rowing team.\nSubmitted SAT: 1550\nHonors:\nService award\n')
        self.assertEqual([r[0] for r in records], ['essay_draft'])
        self.assertNotIn('Service award', records[0][1])
