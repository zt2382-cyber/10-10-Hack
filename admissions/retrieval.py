"""Unified, evidence-aware retrieval; heuristic similarity, not admission prediction."""
import json
import math
import re

from admissions.core import require, search, similarity, validate_profile
from admissions.essays import INDEX_SCHEMA, compare_passages, embed_text, essay_text, text_hash

WEIGHTS = {'gpa': .20, 'sat_submitted': .10, 'courses': .20, 'activities': .25, 'interests': .05, 'essay': .20}
VERSION = 'hybrid-v2'


def overlap(a, b):
    a = set(re.findall(r'\w+', a.casefold()))
    b = set(re.findall(r'\w+', b.casefold()))
    return len(a & b) / len(a | b) if a and b else 0


def grade_similarity(a, b):
    letters = ['F', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+']
    if a in letters and b in letters:
        return max(0, 1-abs(letters.index(a)-letters.index(b))/6)
    # Only compare numeric grades when their denominators are explicit and identical.
    pattern = r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)'
    aa, bb = re.fullmatch(pattern, a), re.fullmatch(pattern, b)
    if aa and bb and float(aa[2]) == float(bb[2]) and float(aa[2]) > 0:
        return max(0, 1-abs(float(aa[1])-float(bb[1]))/(float(aa[2])*.25))
    return None


def record_pair(a, b, kind):
    # Names provide a match anchor; details cannot match unrelated records by themselves.
    name = overlap(a['name'], b['name'])
    if name == 0:
        return None
    weights = {'name': .6, 'grade': .20, 'level': .15, 'credits': .05} if kind == 'courses' else {'name': .4, 'role': .15, 'hours': .15, 'duration': .15, 'achievements': .15}
    values = {'name': name}
    if kind == 'courses':
        grade = grade_similarity(a['grade'], b['grade'])
        if grade is not None:
            values['grade'] = grade
        if a.get('credits') is not None and b.get('credits') is not None:
            values['credits'] = max(0, 1-abs(a['credits']-b['credits'])/max(1, a['credits'], b['credits']))
        if a.get('level') and b.get('level'):
            values['level'] = float(a['level'].casefold() == b['level'].casefold())
    else:
        if a.get('role') and b.get('role'):
            values['role'] = overlap(a['role'], b['role'])
        if a.get('hours_per_week') is not None and b.get('hours_per_week') is not None:
            values['hours'] = max(0, 1-abs(a['hours_per_week']-b['hours_per_week'])/max(5, a['hours_per_week'], b['hours_per_week']))
        if a.get('duration') and b.get('duration'):
            months = lambda d: d['value']*(12 if d['unit'] == 'year' else 1)
            x, y = months(a['duration']), months(b['duration'])
            values['duration'] = max(0, 1-abs(x-y)/max(12, x, y))
        if a.get('achievements') and b.get('achievements'):
            values['achievements'] = overlap(' '.join(a['achievements']), ' '.join(b['achievements']))
    coverage = sum(weights[k] for k in values)
    score = sum(values[k]*weights[k] for k in values)/coverage
    return {'query_name': a['name'], 'historical_name': b['name'], 'similarity': score,
            'coverage': coverage, 'features': values}


def record_similarity(a, b, kind):
    if not a or not b:
        return None
    pairs = []
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            pair = record_pair(x, y, kind)
            if pair:
                pairs.append((pair['similarity']*pair['coverage'], i, j, pair))
    # Deterministic one-to-one alignment prevents reusing one activity/course repeatedly.
    pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
    used_a, used_b, selected = set(), set(), []
    for _, i, j, pair in pairs:
        if i not in used_a and j not in used_b:
            used_a.add(i); used_b.add(j); selected.append(pair)
    size = max(len(a), len(b))
    unmatched = size-len(selected)
    coverage = (sum(p['coverage'] for p in selected)+unmatched)/size
    numerator = sum(p['similarity']*p['coverage'] for p in selected)/size
    return {'similarity': numerator/coverage if coverage else 0, 'coverage': coverage,
            'matches': selected, 'unmatched_query': [x['name'] for i, x in enumerate(a) if i not in used_a],
            'unmatched_historical': [x['name'] for i, x in enumerate(b) if i not in used_b]}


def structured_components(query, candidate):
    legacy = similarity(query, candidate)['components']
    components = {}
    for field in ('gpa', 'sat_submitted', 'interests'):
        if field in legacy:
            components[field] = {'similarity': legacy[field]['similarity'], 'coverage': 1, 'method': 'structured'}
    for field, rich, fallback, fallback_coverage in [('courses', 'courses', 'rigor', .3), ('activities', 'activity_records', 'activities', .4)]:
        result = record_similarity(query.get(rich), candidate.get(rich), rich)
        if result is not None:
            components[field] = {**result, 'method': 'record alignment'}
        elif fallback in legacy:
            components[field] = {'similarity': legacy[fallback]['similarity'], 'coverage': fallback_coverage, 'method': 'tag fallback'}
    return components


def summarize(components, weights):
    coverage = sum(weights[k]*v['coverage'] for k, v in components.items())
    rank = sum(weights[k]*v['coverage']*v['similarity'] for k, v in components.items())
    return rank/coverage if coverage else 0, coverage, rank


def retrieve(db, query, college_id, cycle, round_, program, residency, embedder=None,
             limit=10, include_synthetic=False, exclude_student_id=None,
             without_essays=False, min_academic_coverage=.25, min_academic_similarity=.4,
             weights=None, diagnostics=True, neighbours=7, needed=15):
    validate_profile(query)
    require(type(neighbours) is int and neighbours > 0, 'neighbours must be positive')
    require(type(needed) is int and needed > 0, 'needed must be positive')
    if diagnostics and embedder is not None:
        embedder = CachedEmbedder(embedder)
    require(type(limit) is int and limit > 0, 'limit must be positive')
    require(0 <= min_academic_coverage <= 1 and 0 <= min_academic_similarity <= 1, 'Thresholds must be between 0 and 1')
    weights = dict(WEIGHTS if weights is None else weights)
    require(set(weights) == set(WEIGHTS) and all(type(v) in (int,float) and math.isfinite(v) and v > 0 for v in weights.values()), 'Weights must contain all components with positive finite values')
    total = sum(weights.values()); weights = {k:v/total for k,v in weights.items()}
    query_text = essay_text(query)
    if query_text and not without_essays:
        require(embedder is not None, 'Essay retrieval requires an embedding model; use explicit without_essays mode to disable it')
        db.executescript(INDEX_SCHEMA)
        query_chunks, query_vectors = embed_text(embedder, query_text)
    else:
        query_chunks = query_vectors = None
    pool = search(db, query, college_id, cycle, round_, program, residency, limit=2147483647,
                  include_synthetic=include_synthetic, exclude_student_id=exclude_student_id,
                  deduplicate=False, include_unscored=True)
    matches, excluded, warnings = [], 0, []
    has_field_evidence = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='profile_evidence'").fetchone() is not None
    if without_essays:
        warnings.append('Essay scoring explicitly disabled')
    elif not query_text:
        warnings.append('Query has no essay; essay evidence unavailable')
    academic_weights = {k: weights[k] for k in ('gpa','sat_submitted','courses')}
    academic_total = sum(academic_weights.values())
    for match in pool['matches']:
        row = db.execute('''SELECT s.id, s.profile_json FROM applications a JOIN snapshots s ON s.id=a.snapshot_id WHERE a.id=?''', (match['application_id'],)).fetchone()
        candidate = json.loads(row['profile_json'])
        validate_profile(candidate)
        components = structured_components(query, candidate)
        academic = {k:v for k,v in components.items() if k in academic_weights}
        academic_score, academic_cov, _ = summarize(academic, academic_weights)
        academic_cov /= academic_total
        if academic_cov < min_academic_coverage or academic_score < min_academic_similarity:
            excluded += 1
            continue
        comparison = None
        essay_status = 'disabled' if without_essays else 'query_missing'
        if query_vectors is not None:
            candidate_text = essay_text(candidate)
            essay_status = 'historical_missing'
            if candidate_text:
                cached = db.execute('SELECT * FROM essay_embeddings WHERE snapshot_id=? AND model_key=?', (row['id'],embedder.key)).fetchone()
                require(cached is not None and cached['text_hash'] == text_hash(candidate_text),
                        f"Essay index missing or stale for snapshot {row['id']}; run index-essays with the same model/revision")
                comparison = compare_passages(query_chunks, query_vectors, json.loads(cached['chunks_json']), json.loads(cached['vectors_json']))
                components['essay'] = {'similarity': max(0, comparison['essay_similarity']), 'coverage': 1, 'method': 'passage embeddings'}
                essay_status = 'scored'
        score, coverage, rank = summarize(components, weights)
        for key, component in components.items():
            component['weight'] = weights[key]
            component['contribution'] = round(weights[key]*component['coverage']*component['similarity'],6)
        provenance = []
        if has_field_evidence:
            provenance = [dict(e) for e in db.execute('''SELECT p.field, c.document_id, d.filename, c.reviewer, c.evidence_json
                FROM profile_evidence p JOIN field_candidates c ON c.id=p.candidate_id
                JOIN documents d ON d.id=c.document_id WHERE p.snapshot_id=?''', (row['id'],))]
            for item in provenance:
                item['evidence'] = json.loads(item.pop('evidence_json'))
        matches.append({'application_id': match['application_id'], 'student_id': match['student_id'],
            'cycle': match['cycle'], 'synthetic': match['synthetic'], 'source': match['source'],
            'source_id':match['source_id'], 'evidence_pool':match['evidence_pool'], 'verification_level':match['verification_level'],
            'similarity': round(score,4), 'coverage': round(coverage,4), 'rank_score': round(rank,4),
            'academic_similarity': round(academic_score,4), 'academic_coverage': round(academic_cov,4),
            'components': components, 'missing_components': sorted(set(weights)-set(components)),
            'essay_status': essay_status, 'matching_passages': comparison['matching_passages'] if comparison else None,
            'profile_evidence': provenance, 'outcome_events': match['outcome_events']})
    matches.sort(key=lambda m:(-m['rank_score'],-m['coverage'],-m['cycle'],m['application_id']))
    unique, seen = [], set()
    for match in matches:
        if match['student_id'] not in seen:
            unique.append(match); seen.add(match['student_id'])
    result = {'retrieval_version': VERSION, 'model': embedder.key if query_vectors is not None else None,
            'college_id':college_id,'weights':weights,'warnings':warnings,
            'eligible_students': len({m['student_id'] for m in pool['matches']}),
            'excluded_applications_by_academic_gate':excluded, 'matched_students':len(unique),
            'synthetic_included':include_synthetic, 'category':'insufficient evidence',
            'reason':'Combined similarity is a retrieval heuristic, not an admission probability.',
            'matches':unique[:limit]}

    from admissions.evidence import outcome_comparisons, stability
    result['outcome_comparison'] = outcome_comparisons(matches, neighbours, needed)
    result['stability'] = None
    if diagnostics:
        variants = []
        # Neighbour-size tests reuse the ranked evidence and require no model call.
        for k in (5, 10):
            if k != neighbours:
                variants.append((f'{k} neighbours', unique, outcome_comparisons(matches, k, needed)))
        options = []
        if query.get('sat_submitted') is not None:
            for delta in (-30, 30):
                changed = dict(query, sat_submitted=max(400,min(1600,query['sat_submitted']+delta)))
                if changed['sat_submitted'] != query['sat_submitted']:
                    options.append((f'SAT {delta:+d}', changed, weights, without_essays))
        if query_vectors is not None:
            for factor in (.8, 1.2):
                changed_weights = dict(weights, essay=weights['essay']*factor)
                options.append((f'essay weight x{factor}',query,changed_weights,False))
            options.append(('essay excluded',query,weights,True))
        for name, changed_query, changed_weights, disable_essays in options:
            changed = retrieve(db, changed_query, college_id, cycle, round_, program, residency,
                embedder=embedder,limit=max(limit,len(matches),1),include_synthetic=include_synthetic,
                exclude_student_id=exclude_student_id,without_essays=disable_essays,
                min_academic_coverage=min_academic_coverage,min_academic_similarity=min_academic_similarity,
                weights=changed_weights,diagnostics=False,neighbours=neighbours,needed=needed)
            variants.append((name,changed['matches'],changed['outcome_comparison']))
        result['stability'] = stability(unique,result['outcome_comparison'],variants,top_k=limit)
    return result


class CachedEmbedder:
    """Per-request memoization avoids repeated inference in sensitivity checks."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.key = delegate.key
        self.cache = {}
    def chunks(self, text):
        return self.delegate.chunks(text)
    def encode(self, texts):
        key = tuple(texts)
        if key not in self.cache:
            self.cache[key] = self.delegate.encode(texts)
        return self.cache[key]
