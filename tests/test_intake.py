import json
import unittest
from admissions.core import connect, ingest, search
from admissions.intake import stage, review, publish, inspect_batch


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(':memory:')

    def tearDown(self):
        self.db.close()

    def stage(self, text='gpa: 3.8 / 4.0 unweighted\nactivities: Robotics; Tutoring\nsat_submitted: 1420\n', **kwargs):
        return stage(self.db, text, 'fixture.txt', kwargs.pop('kind', 'intake-text'),
                     kwargs.pop('student_id', 'student'), True, 'synthetic', **kwargs)

    def accept(self, report):
        for candidate in report['candidates']:
            review(self.db, candidate['id'], 'accepted', 'test-reviewer')

    def test_review_publish_provenance_and_search(self):
        report = self.stage()
        with self.assertRaises(ValueError):
            publish(self.db, report['batch_id'], 'snapshot', '2024-11-01')
        self.accept(report)
        result = publish(self.db, report['batch_id'], 'snapshot', '2024-11-01')
        self.assertEqual(result['profile']['activities'], ['robotics', 'tutoring'])
        evidence = self.db.execute('SELECT count(*) FROM profile_evidence').fetchone()[0]
        self.assertEqual(evidence, 3)
        document = self.db.execute('SELECT content FROM documents').fetchone()[0]
        for c in report['candidates']:
            e = c['evidence']
            self.assertEqual(document[e['start_char']:e['end_char']], e['quoted_text'])
        ingest(self.db, {'schema_version': 1, 'applications': [{'id': 'app', 'snapshot_id': 'snapshot', 'college_id': 'demo', 'program': 'engineering', 'cycle': 2025, 'round': 'RD', 'residency': 'domestic'}]})
        matches = search(self.db, result['profile'], 'demo', 2026, 'RD', 'engineering', 'domestic', include_synthetic=True)['matches']
        self.assertEqual(len(matches), 1)
        with self.assertRaises(ValueError):
            review(self.db, report['candidates'][0]['id'], 'rejected', 'reviewer')
        with self.assertRaises(ValueError):
            self.stage(batch_id=report['batch_id'])

    def test_conflicting_sources_require_explicit_resolution(self):
        first = self.stage('gpa: 3.8 / 4.0 unweighted\n')
        second = self.stage('gpa: 3.9 / 4.0 unweighted\n', batch_id=first['batch_id'])
        self.assertEqual(second['conflicts'], ['gpa'])
        self.accept(second)
        with self.assertRaises(ValueError):
            publish(self.db, first['batch_id'], 'snapshot', '2024-11-01')
        review(self.db, first['candidates'][0]['id'], 'rejected', 'reviewer')
        result = publish(self.db, first['batch_id'], 'snapshot', '2024-11-01')
        self.assertEqual(result['profile']['gpa']['value'], 3.9)
        self.assertEqual(self.db.execute('SELECT count(*) FROM review_events').fetchone()[0], 3)

    def test_bad_value_and_ambiguous_gpa_not_guessed(self):
        report = self.stage('gpa: 3.8\nsat_submitted: 2000\n')
        self.assertTrue(all(c['issue'] for c in report['candidates']))
        with self.assertRaises(ValueError):
            review(self.db, report['candidates'][0]['id'], 'accepted', 'reviewer')

    def test_csv_quoted_values_and_single_student_constraint(self):
        report = self.stage('gpa,activities\n3.8 / 4.0 unweighted,"robotics; tutoring"\n', kind='intake-csv')
        self.assertEqual(len(report['candidates']), 2)
        self.assertEqual(report['candidates'][0]['evidence']['row'], 2)
        with self.assertRaises(ValueError):
            self.stage('activities\nrobotics\ntutoring\n', kind='intake-csv')

    def test_essay_exact_text_and_student_isolation(self):
        text = 'I helped my family.\nThen I built a robot.\n'
        report = self.stage(text, kind='essay')
        self.assertEqual(report['candidates'][0]['value'], text)
        with self.assertRaises(ValueError):
            self.stage(student_id='another', batch_id=report['batch_id'])

    def test_publish_failure_rolls_back_and_can_retry(self):
        report = self.stage()
        self.accept(report)
        self.db.execute('INSERT INTO sources VALUES (?, ?, ?, ?, ?)', ('intake:' + report['batch_id'], 'demo', 1, 'synthetic', 'fixture'))
        self.db.commit()
        with self.assertRaises(Exception):
            publish(self.db, report['batch_id'], 'snapshot', '2024-11-01')
        self.assertIsNone(inspect_batch(self.db, report['batch_id'])['published_snapshot_id'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM snapshots').fetchone()[0], 0)

    def test_real_input_requires_consent(self):
        with self.assertRaises(ValueError):
            stage(self.db, 'activities: robotics', 'file', 'intake-text', 's', False, 'synthetic')
