import unittest
from admissions.core import connect, ingest, search, similarity


def bundle():
    return {'schema_version': 1,
        'sources': [{'id': 'source', 'kind': 'demo', 'synthetic': True, 'consent': 'synthetic', 'reference': 'Generated fixture'}],
        'snapshots': [{'id': 'snapshot', 'student_id': 'student', 'source_id': 'source', 'captured_at': '2024-10-01', 'profile': {'gpa': {'value': 3.8, 'scale': 4, 'weighted': False}, 'activities': ['robotics']}}],
        'applications': [{'id': 'application', 'snapshot_id': 'snapshot', 'college_id': 'demo', 'program': 'engineering', 'cycle': 2025, 'round': 'RD', 'residency': 'domestic'}],
        'outcomes': []}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(':memory:')
        self.data = bundle()
        self.query = self.data['snapshots'][0]['profile']

    def tearDown(self):
        self.db.close()

    def find(self, **kwargs):
        return search(self.db, self.query, 'demo', 2026, 'RD', 'engineering', 'domestic', **kwargs)

    def test_synthetic_is_opt_in_and_missing_outcome_is_unknown(self):
        ingest(self.db, self.data)
        self.assertEqual(self.find()['matches'], [])
        match = self.find(include_synthetic=True)['matches'][0]
        self.assertEqual(match['outcome_events'], [])
        self.assertEqual(self.find(include_synthetic=True)['category'], 'insufficient evidence')

    def test_foreign_key_failure_rolls_back_import(self):
        self.data['applications'][0]['snapshot_id'] = 'missing'
        with self.assertRaises(Exception):
            ingest(self.db, self.data)
        self.assertEqual(self.db.execute('SELECT count(*) FROM sources').fetchone()[0], 0)

    def test_incompatible_gpa_and_missing_fields_reduce_coverage(self):
        candidate = {'gpa': {'value': 4.5, 'scale': 5, 'weighted': True}, 'activities': ['robotics']}
        result = similarity(self.query, candidate)
        self.assertEqual(result['coverage'], .15)
        self.assertNotIn('gpa', result['components'])

    def test_current_cycle_and_self_excluded(self):
        ingest(self.db, self.data)
        self.assertEqual(self.find(include_synthetic=True, exclude_student_id='student')['matches'], [])
        self.assertEqual(search(self.db, self.query, 'demo', 2025, 'RD', 'engineering', 'domestic', include_synthetic=True)['matches'], [])

    def test_outcome_history_preserved(self):
        self.data['outcomes'] = [
            {'id': 'wait', 'application_id': 'application', 'decision': 'waitlist', 'occurred_at': '2025-03-01', 'verified': False, 'source_id': 'source'},
            {'id': 'admit', 'application_id': 'application', 'decision': 'admit', 'occurred_at': '2025-05-01', 'verified': True, 'source_id': 'source'}]
        ingest(self.db, self.data)
        events = self.find(include_synthetic=True)['matches'][0]['outcome_events']
        self.assertEqual([e['decision'] for e in events], ['waitlist', 'admit'])


if __name__ == '__main__':
    unittest.main()
