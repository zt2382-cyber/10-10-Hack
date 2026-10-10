import copy
import json
import unittest

from admissions.core import connect, ingest
from admissions.essays import index_essays
from admissions.retrieval import retrieve, record_similarity, WEIGHTS


class SemanticFixture:
    key = 'fixture@v1'
    def chunks(self, text): return [{'text': text, 'start_char': 0, 'end_char': len(text)}]
    def encode(self, texts):
        # Authored topic vectors isolate ranking behavior; no model-quality claim.
        return [[1, 0] if t.startswith('engineering') else [0, 1] for t in texts]


def profile(essay='engineering teamwork'):
    return {'gpa': {'value':3.8,'scale':4.0,'weighted':False}, 'sat_submitted':1420,
            'interests':['engineering'], 'activities':['robotics'],
            'activity_records':[{'name':'Robotics Club','role':'Captain','hours_per_week':8,
                                 'duration':{'value':3,'unit':'year'},'achievements':['Regional award']}],
            'courses':[{'name':'AP Physics','grade':'A','level':'AP','term':'2024','credits':1}],
            'essay_draft':essay}


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:'); self.embedder=SemanticFixture(); self.query=profile()
        profiles={'strong':profile(), 'other_essay':profile('music performance'), 'weak':profile()}
        profiles['weak']['gpa']['value']=2.0
        profiles['weak']['sat_submitted']=800
        profiles['weak']['courses'][0]['grade']='F'
        bundle={'schema_version':1,'sources':[{'id':'source','kind':'fixture','synthetic':True,'consent':'synthetic','reference':'Fictional retrieval examples'}], 'snapshots':[], 'applications':[], 'outcomes':[]}
        for student,p in profiles.items():
            bundle['snapshots'].append({'id':student,'student_id':student,'source_id':'source','captured_at':'2024-11-01','profile':p})
            bundle['applications'].append({'id':student,'snapshot_id':student,'college_id':'demo','program':'engineering','cycle':2025,'round':'RD','residency':'domestic'})
        ingest(self.db,bundle)
        index_essays(self.db,self.embedder,True)

    def tearDown(self): self.db.close()
    def find(self, **kwargs):
        return retrieve(self.db,self.query,'demo',2026,'RD','engineering','domestic',embedder=self.embedder,include_synthetic=True,**kwargs)

    def test_essay_changes_order_without_overriding_academic_gate(self):
        matches=self.find()['matches']
        self.assertEqual([m['student_id'] for m in matches],['strong','other_essay'])
        self.assertEqual(self.find()['excluded_applications_by_academic_gate'],1)
        self.assertGreater(matches[0]['rank_score'],matches[1]['rank_score'])
        self.query['essay_draft']='music performance'
        self.assertEqual(self.find()['matches'][0]['student_id'],'other_essay')

    def test_missing_essay_explicit_and_fixed_weight_coverage(self):
        del self.query['essay_draft']
        result=self.find()
        self.assertTrue(result['warnings'])
        self.assertEqual(result['matches'][0]['coverage'],.8)
        self.assertEqual(result['matches'][0]['essay_status'],'query_missing')
        for m in result['matches']:
            self.assertAlmostEqual(sum(c['contribution'] for c in m['components'].values()),m['rank_score'],places=4)

    def test_stale_and_wrong_model_fail_instead_of_silent_degradation(self):
        self.db.execute("UPDATE essay_embeddings SET text_hash='stale' WHERE snapshot_id='strong'")
        self.db.commit()
        with self.assertRaisesRegex(ValueError,'index missing or stale'): self.find()
        self.assertTrue(self.find(without_essays=True)['warnings'])

    def test_rich_courses_without_legacy_fields_are_retrieved(self):
        self.query={'courses':self.query['courses']}
        result=self.find()
        self.assertEqual(len(result['matches']),3)
        self.assertIn('courses',result['matches'][0]['components'])

    def test_sparse_tags_not_equal_to_rich_activity_evidence(self):
        matches=self.find(without_essays=True)['matches']
        rich=matches[0]['rank_score']
        del self.query['activity_records']
        self.assertLess(self.find(without_essays=True)['matches'][0]['rank_score'],rich)

    def test_outcome_does_not_change_ranking(self):
        before=[(m['application_id'],m['rank_score']) for m in self.find()['matches']]
        self.db.execute("INSERT INTO outcome_events VALUES ('decision','other_essay','admit','2025-03-01',1,'source')")
        self.db.commit()
        after=[(m['application_id'],m['rank_score']) for m in self.find()['matches']]
        self.assertEqual(before,after)

    def test_duplicates_deduplicated_after_combined_ranking(self):
        p=profile('music performance')
        ingest(self.db,{'schema_version':1,'snapshots':[{'id':'duplicate','student_id':'strong','source_id':'source','captured_at':'2024-11-01','profile':p}], 'applications':[{'id':'duplicate','snapshot_id':'duplicate','college_id':'demo','program':'engineering','cycle':2025,'round':'RD','residency':'domestic'}]})
        index_essays(self.db,self.embedder,True)
        self.query['essay_draft']='music performance'
        matches=self.find()['matches']
        self.assertEqual(len([m for m in matches if m['student_id']=='strong']),1)
        self.assertEqual(next(m for m in matches if m['student_id']=='strong')['application_id'],'duplicate')

    def test_filters_and_self_exclusion(self):
        self.assertNotIn('strong',[m['student_id'] for m in self.find(exclude_student_id='strong')['matches']])
        self.assertEqual(retrieve(self.db,self.query,'demo',2026,'RD','engineering','domestic',embedder=self.embedder)['matches'],[])
        self.assertEqual(retrieve(self.db,self.query,'demo',2025,'RD','engineering','domestic',embedder=self.embedder,include_synthetic=True)['matches'],[])

    def test_record_alignment_does_not_reuse_candidate(self):
        a=profile()['activity_records'][0]
        result=record_similarity([a,copy.deepcopy(a)],[a],'activity_records')
        self.assertEqual(len(result['matches']),1)
        self.assertLess(result['similarity'],1)

    def test_weights_and_provider_validation(self):
        with self.assertRaises(ValueError): self.find(weights={'essay':1})
        with self.assertRaises(ValueError):
            retrieve(self.db,self.query,'demo',2026,'RD','engineering','domestic',include_synthetic=True)
        result=self.find(weights={k:v*2 for k,v in WEIGHTS.items()})
        self.assertAlmostEqual(sum(result['weights'].values()),1)

    def test_historical_missing_essay_reduces_coverage(self):
        p=profile(); del p['essay_draft']
        self.db.execute('UPDATE snapshots SET profile_json=? WHERE id=?',(json.dumps(p),'strong'))
        self.db.commit()
        match=next(m for m in self.find()['matches'] if m['student_id']=='strong')
        self.assertEqual(match['essay_status'],'historical_missing')
        self.assertEqual(match['coverage'],.8)

    def test_wrong_model_cache_is_rejected(self):
        self.embedder.key='fixture@v2'
        with self.assertRaisesRegex(ValueError,'index missing or stale'): self.find()

    def test_incompatible_numeric_grades_reduce_course_evidence(self):
        from admissions.retrieval import grade_similarity
        self.assertIsNone(grade_similarity('92/100','4/5'))
        self.assertIsNone(grade_similarity('92','93'))
        self.assertEqual(grade_similarity('92/100','92/100'),1)
