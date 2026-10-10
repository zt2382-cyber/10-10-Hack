"""Run the synthetic document pilot: python3 -m scripts.validate_pilot."""
import json
import tempfile
from pathlib import Path

from admissions.core import connect, ingest, search
from admissions.intake import stage_document, review, publish

ROOT = Path(__file__).resolve().parents[1]


def validate():
    document = ROOT / 'examples/pilot/student_application.txt'
    expected = json.loads((ROOT / 'examples/pilot/expected.json').read_text())
    with tempfile.TemporaryDirectory() as directory:
        db = connect(str(Path(directory) / 'pilot.db'))
        try:
            staged = stage_document(db, document, 'freeform', 'pilot-001', True, 'synthetic')
            blocked = [c for c in staged['candidates'] if c['issue']]
            assert len(blocked) == expected['blocked_gpa_candidates']
            assert all(c['field'] == 'gpa' for c in blocked)
            content = db.execute('SELECT content FROM documents').fetchone()[0]
            for candidate in staged['candidates']:
                ev = candidate['evidence']
                for item in ev.get('items', [ev]):
                    assert content[item['start_char']:item['end_char']] == item['quoted_text']
                    assert item['page'] == 1
                review(db, candidate['id'], 'rejected' if candidate['issue'] else 'accepted', 'synthetic-pilot-review')
            profile = publish(db, staged['batch_id'], 'pilot-snapshot', '2024-11-01')['profile']
            for field in ('gpa', 'sat_submitted', 'interests', 'activities', 'courses'):
                assert profile[field] == expected[field], field
            actual_activities = [{k: a[k] for k in expected['activity_records'][0]} for a in profile['activity_records']]
            assert actual_activities == expected['activity_records']
            original = document.read_text()
            essay = original.split('Personal statement:\n', 1)[1].split('\nHonors:', 1)[0]
            assert profile['essay_draft'].strip() == essay.strip()
            assert 'School service recognition' not in profile['essay_draft']
            assert len(profile['activity_records']) == 3  # Essay captain anecdote is excluded.
            assert profile['sat_submitted'] != 1490  # Negated submission is excluded.
            assert db.execute('SELECT original_bytes FROM document_assets').fetchone()[0] == document.read_bytes()
            ingest(db, {'schema_version': 1,
                'sources': [{'id': 'pilot-decision-source', 'kind': 'synthetic_fixture', 'synthetic': True, 'consent': 'synthetic', 'reference': 'Fictional pilot outcome, not real admissions evidence'}],
                'applications': [{'id': 'pilot-app', 'snapshot_id': 'pilot-snapshot', 'college_id': 'fictional-pilot-university', 'program': 'engineering', 'cycle': 2025, 'round': 'RD', 'residency': 'domestic'}],
                'outcomes': [{'id': 'pilot-outcome', 'application_id': 'pilot-app', 'decision': 'waitlist', 'occurred_at': '2025-03-20', 'verified': False, 'source_id': 'pilot-decision-source'}]})
            args = (db, profile, 'fictional-pilot-university', 2026, 'RD', 'engineering', 'domestic')
            assert search(*args)['matches'] == []
            match = search(*args, include_synthetic=True)['matches'][0]
            assert match['score'] == 1 and match['coverage'] == .8
            assert match['outcome_events'][0]['decision'] == 'waitlist'
            return {'status': 'passed', 'synthetic': True, 'candidate_count': len(staged['candidates']),
                'accepted_candidates': len(staged['candidates'])-len(blocked), 'rejected_ambiguous_gpa': len(blocked),
                'activities_checked': len(actual_activities), 'courses_checked': len(profile['courses']),
                'essay_matches_original_section': True, 'evidence_offsets_checked': True,
                'original_bytes_preserved': True, 'negated_sat_excluded': True, 'essay_activity_excluded': True,
                'publication_and_outcome_retrieval': 'passed', 'academic_similarity': match['score'],
                'academic_coverage': match['coverage'], 'known_omissions': expected['known_omissions'],
                'unverified': ['PDF parsing', 'OCR', 'Real embedding model inference', 'Real applicant retrieval quality'],
                'profile': profile}
        finally:
            db.close()


if __name__ == '__main__':
    result = validate()
    output = ROOT / 'examples/pilot/validation_result.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'profile'}, indent=2))
