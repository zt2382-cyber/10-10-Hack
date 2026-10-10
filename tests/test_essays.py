import json
import unittest

from admissions.core import connect, ingest
from admissions.essays import essay_search, index_essays
from tests.test_core import bundle


class FixtureEmbedder:
    """Known vectors test retrieval plumbing, not a substitute semantic model."""
    key = 'test@fixed:v1'

    def __init__(self):
        self.calls = 0

    def chunks(self, text):
        return [{'start_char': 0, 'end_char': len(text), 'text': text}]

    def encode(self, texts):
        self.calls += 1
        return [[1, 0] if t in ('I earned wages to help at home.', 'My job supported our household.') else [0, 1] for t in texts]


class EssayTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(':memory:')
        self.data = bundle()
        self.data['snapshots'][0]['profile']['essay_draft'] = 'My job supported our household.'
        ingest(self.db, self.data)
        self.embedder = FixtureEmbedder()
        self.query = dict(self.data['snapshots'][0]['profile'], essay_draft='I earned wages to help at home.')

    def tearDown(self):
        self.db.close()

    def find(self, **kwargs):
        return essay_search(self.db, self.query, self.embedder, 'demo', 2026, 'RD', 'engineering', 'domestic',
                            min_academic_coverage=.4, **kwargs)

    def test_passage_evidence_and_outcomes(self):
        index_essays(self.db, self.embedder, include_synthetic=True)
        result = self.find(include_synthetic=True)
        self.assertEqual(result['matches'][0]['essay_similarity'], 1)
        passage = result['matches'][0]['matching_passages']['historical']
        self.assertEqual(passage['text'], self.data['snapshots'][0]['profile']['essay_draft'][passage['start_char']:passage['end_char']])
        self.assertEqual(result['matches'][0]['outcome_events'], [])
        self.assertEqual(self.find()['matches'], [])

    def test_cache_reused_and_model_version_not_mixed(self):
        index_essays(self.db, self.embedder, True)
        result = index_essays(self.db, self.embedder, True)
        self.assertEqual(result['indexed'], 0)
        self.assertEqual(self.embedder.calls, 1)
        self.embedder.key = 'test@different:v1'
        self.assertEqual(self.find(include_synthetic=True)['unindexed_or_missing_essays'], 1)

    def test_stale_text_rejected(self):
        index_essays(self.db, self.embedder, True)
        profile = dict(self.query, essay_draft='Changed essay')
        self.db.execute('UPDATE snapshots SET profile_json=?', (json.dumps(profile),))
        self.db.commit()
        self.assertEqual(self.find(include_synthetic=True)['matches'], [])
        self.assertEqual(index_essays(self.db, self.embedder, True)['indexed'], 1)

    def test_academic_gate_and_self_exclusion(self):
        index_essays(self.db, self.embedder, True)
        self.assertEqual(self.find(include_synthetic=True, exclude_student_id='student')['matches'], [])
        self.query['gpa']['value'] = 2
        self.assertEqual(self.find(include_synthetic=True)['excluded_by_academic_thresholds'], 1)

    def test_empty_essay_and_bad_vectors(self):
        self.query['essay_draft'] = ' '
        with self.assertRaises(ValueError):
            self.find()
        self.embedder.encode = lambda texts: [[0, 0] for _ in texts]
        with self.assertRaises(ValueError):
            index_essays(self.db, self.embedder, True)
        self.assertEqual(self.db.execute('SELECT count(*) FROM essay_embeddings').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()

class PassageTests(unittest.TestCase):
    def test_token_windows_cover_entire_essay(self):
        from admissions.essays import LocalEmbedder
        class Tokenizer:
            def __call__(self, text, **kwargs):
                return {'offset_mapping': [(i, i+1) for i in range(len(text))]}
            def num_special_tokens_to_add(self, pair=False):
                return 2
        class Model:
            tokenizer = Tokenizer()
            max_seq_length = 10
        embedder = LocalEmbedder.__new__(LocalEmbedder)
        embedder.model = Model()
        text = 'abcdefghijklmnopqrstuvwxyz'
        chunks = embedder.chunks(text)
        covered = set()
        for chunk in chunks:
            self.assertLessEqual(len(chunk['text']), 8)
            self.assertEqual(chunk['text'], text[chunk['start_char']:chunk['end_char']])
            covered.update(range(chunk['start_char'], chunk['end_char']))
        self.assertEqual(covered, set(range(len(text))))

    def test_semantic_vector_ranking_includes_less_similar_candidate(self):
        db = connect(':memory:')
        try:
            data = bundle()
            data['snapshots'][0]['profile']['essay_draft'] = 'My job supported our household.'
            second = dict(data['snapshots'][0], id='snapshot-2', student_id='student-2',
                          profile=dict(data['snapshots'][0]['profile'], essay_draft='An unrelated astronomy essay.'))
            data['snapshots'].append(second)
            data['applications'].append(dict(data['applications'][0], id='application-2', snapshot_id='snapshot-2'))
            ingest(db, data)
            embedder = FixtureEmbedder()
            index_essays(db, embedder, True)
            query = dict(second['profile'], essay_draft='I earned wages to help at home.')
            result = essay_search(db, query, embedder, 'demo', 2026, 'RD', 'engineering', 'domestic', include_synthetic=True, min_academic_coverage=.4)
            self.assertEqual([m['essay_similarity'] for m in result['matches']], [1, 0])
            self.assertEqual(result['matches'][0]['student_id'], 'student')
        finally:
            db.close()
