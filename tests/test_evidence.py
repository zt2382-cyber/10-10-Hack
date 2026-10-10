import copy
import unittest

from admissions.core import connect, ingest
from admissions.evidence import outcome_comparisons, outcome_view, stability
from admissions.retrieval import retrieve


def match(student, score, decision, pool='self_reported', synthetic=False, verified=False):
    level = 'document_supported' if verified else 'self_reported'
    return {'application_id':student,'student_id':student,'cycle':2025,'rank_score':score,
        'coverage':.8,'components':{'gpa':{'similarity':score,'coverage':1}},
        'source':'Fictional test fixture','evidence_pool':pool,'verification_level':level,'synthetic':synthetic,
        'matching_passages':None,'outcome_events':[] if decision=='unknown' else [
            {'id':student,'decision':decision,'occurred_at':'2025-03-01','synthetic':synthetic,
             'verified':verified,'verification_level':level,'evidence_pool':pool,'reference':'Fictional decision'}]}


class OutcomeEvidenceTests(unittest.TestCase):
    def test_group_summary_and_parts(self):
        rows=[match('a1',.9,'admit'),match('a2',.8,'admit'),match('d1',.5,'deny'),match('d2',.4,'deny')]
        pool=outcome_comparisons(rows,neighbours=2,needed=2)['pools'][0]
        self.assertEqual(pool['status'],'ok')
        self.assertAlmostEqual(pool['gap'],.4)
        self.assertEqual(pool['lean'],'closer_to_admitted')
        self.assertEqual(pool['parts'][0]['admitted']['n'],2)
        self.assertEqual(pool['nearest_denied'][0]['student_id'],'d1')

    def test_small_and_missing_groups_abstain(self):
        rows=[match('a',.9,'admit'),match('d',.5,'deny')]
        pool=outcome_comparisons(rows)['pools'][0]
        self.assertEqual(pool['status'],'not_enough');self.assertIsNone(pool['lean'])
        pool=outcome_comparisons(rows[:1])['pools'][0]
        self.assertEqual(pool['status'],'none');self.assertIsNone(pool['gap'])

    def test_pools_and_verification_never_merge(self):
        rows=[match('a',.9,'admit'),match('d',.5,'deny',pool='counselor',verified=True),
              match('synthetic',.8,'admit',pool='counselor',synthetic=True,verified=True)]
        pools=outcome_comparisons(rows,needed=1)['pools']
        self.assertEqual(len(pools),3)
        self.assertTrue(all(p['status']=='none' for p in pools))
        synthetic=next(p for p in pools if p['synthetic'])
        self.assertFalse(synthetic['verified']);self.assertEqual(synthetic['evidence_pool'],'synthetic')

    def test_final_decision_uses_dates_not_admit_precedence(self):
        row=match('a',.9,'waitlist')
        later=dict(row['outcome_events'][0],id='later',decision='deny',occurred_at='2025-05-01')
        row['outcome_events'].insert(0,later)
        self.assertEqual(outcome_view(row)['decision'],'deny')
        row['outcome_events'].append(dict(later,id='contradiction',decision='admit'))
        self.assertEqual(outcome_view(row)['decision'],'conflicting')

    def test_waitlists_unknown_and_conflicts_not_in_admit_deny_groups(self):
        rows=[match('a',.9,'admit'),match('d',.5,'deny'),match('w',.8,'waitlist'),match('u',.7,'unknown')]
        pools=outcome_comparisons(rows,needed=1)['pools']
        pool=next(p for p in pools if p['counts']['admit'])
        self.assertEqual(sum(p['counts']['waitlist'] for p in pools),1)
        self.assertEqual(sum(p['counts']['unknown'] for p in pools),1)
        self.assertEqual(len(pool['nearest_admitted']),1)

    def test_mixed_profile_outcome_provenance_explicit(self):
        row=match('a',.9,'admit')
        row['outcome_events'][0]['evidence_pool']='counselor'
        self.assertEqual(outcome_view(row)['pool'],'self_reported -> counselor')
        row['outcome_events'][0]['synthetic']=True
        self.assertTrue(outcome_view(row)['synthetic'])

    def test_timezone_equivalent_events_are_conflicting(self):
        row=match('a',.9,'admit')
        row['outcome_events'][0]['occurred_at']='2025-03-01T12:00:00+00:00'
        row['outcome_events'].append(dict(row['outcome_events'][0],decision='deny',occurred_at='2025-03-01T07:00:00-05:00'))
        self.assertEqual(outcome_view(row)['decision'],'conflicting')

    def test_deduplication_and_diagnostics(self):
        rows=[match('a',.9,'admit'),match('d',.5,'deny')]
        duplicate=dict(rows[0],application_id='duplicate',rank_score=.8)
        self.assertEqual(outcome_comparisons(rows+[duplicate],needed=1)['pools'][0]['n_students'],2)
        changed=[dict(rows[1],rank_score=.95),dict(rows[0],rank_score=.4)]
        result=stability(rows,outcome_comparisons(rows,needed=1),[('changed',changed,outcome_comparisons(changed,needed=1))],top_k=1)
        self.assertFalse(result['ranking_steady']);self.assertFalse(result['outcome_direction_steady'])
        self.assertEqual(result['scenarios'][0]['top_k_jaccard'],0)


class IntegratedEvidenceTests(unittest.TestCase):
    def test_full_cohort_summary_not_truncated_by_display_limit(self):
        db=connect(':memory:')
        try:
            # Fictional in-memory rows exercise the non-synthetic provenance paths.
            bundle={'schema_version':1,'sources':[{'id':'source','kind':'test_fixture','synthetic':False,'consent':'granted',
                'reference':'Fictional fixture for provenance logic','evidence_pool':'self_reported','verification_level':'self_reported'}],
                'snapshots':[],'applications':[],'outcomes':[]}
            for i in range(32):
                key=str(i);admitted=i<16
                profile={'gpa':{'value':3.8 if admitted else 3.4,'scale':4,'weighted':False},'sat_submitted':1440 if admitted else 1280}
                bundle['snapshots'].append({'id':key,'student_id':key,'source_id':'source','captured_at':'2024-11-01','profile':profile})
                bundle['applications'].append({'id':key,'snapshot_id':key,'college_id':'demo','program':'engineering','cycle':2025,'round':'RD','residency':'domestic'})
                bundle['outcomes'].append({'id':key,'application_id':key,'decision':'admit' if admitted else 'deny','occurred_at':'2025-03-01','verified':False,'source_id':'source'})
            ingest(db,bundle)
            result=retrieve(db,{'gpa':{'value':3.8,'scale':4,'weighted':False},'sat_submitted':1440},'demo',2026,'RD','engineering','domestic',limit=1)
            self.assertEqual(len(result['matches']),1)
            pool=result['outcome_comparison']['pools'][0]
            self.assertEqual(pool['counts']['admit'],16);self.assertEqual(pool['counts']['deny'],16)
            self.assertEqual(pool['status'],'ok')
            self.assertEqual(pool['lean'],'closer_to_admitted')
            self.assertEqual(len(result['stability']['scenarios']),4)
            self.assertEqual(result['matches'][0]['evidence_pool'],'self_reported')
        finally:db.close()

    def test_old_database_migrates_without_inventing_provenance(self):
        import sqlite3
        from admissions.core import SCHEMA
        db=connect(':memory:')
        try:
            db.execute('DROP TABLE source_metadata');db.executescript(SCHEMA)
            self.assertEqual(db.execute('SELECT count(*) FROM source_metadata').fetchone()[0],0)
        finally:db.close()


    def test_essay_ablation_exposes_rank_change_with_one_query_inference(self):
        from tests.test_retrieval import profile, SemanticFixture
        from admissions.essays import index_essays
        class CountingEmbedder(SemanticFixture):
            calls=0
            def encode(self,texts):
                self.calls+=1
                return super().encode(texts)
        db=connect(':memory:')
        try:
            embedder=CountingEmbedder()
            profiles={'a':profile('music performance'),'b':profile('engineering teamwork')}
            profiles['b']['gpa']['value']=3.7
            bundle={'schema_version':1,'sources':[{'id':'s','kind':'fixture','synthetic':True,'consent':'synthetic','reference':'Synthetic diagnostic fixture'}],
                'snapshots':[],'applications':[],'outcomes':[]}
            for key,p in profiles.items():
                bundle['snapshots'].append({'id':key,'student_id':key,'source_id':'s','captured_at':'2024-11-01','profile':p})
                bundle['applications'].append({'id':key,'snapshot_id':key,'college_id':'demo','program':'engineering','cycle':2025,'round':'RD','residency':'domestic'})
                bundle['outcomes'].append({'id':key,'application_id':key,'decision':'admit' if key=='b' else 'deny','occurred_at':'2025-03-01','verified':False,'source_id':'s'})
            ingest(db,bundle);index_essays(db,embedder,True);embedder.calls=0
            result=retrieve(db,profile(),'demo',2026,'RD','engineering','domestic',embedder=embedder,include_synthetic=True,limit=1,needed=1)
            self.assertEqual(embedder.calls,1)
            self.assertEqual(result['matches'][0]['application_id'],'b')
            ablation=next(s for s in result['stability']['scenarios'] if s['scenario']=='essay excluded')
            self.assertEqual(ablation['top_ids'],['a'])
            self.assertFalse(result['stability']['ranking_steady'])
            self.assertFalse(result['stability']['outcome_direction_steady'])
            self.assertTrue(all(not p['verified'] for p in result['outcome_comparison']['pools']))
        finally:db.close()
