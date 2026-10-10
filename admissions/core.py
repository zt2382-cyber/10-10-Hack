import json
import math
import sqlite3
from datetime import datetime

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, synthetic INTEGER NOT NULL,
 consent TEXT NOT NULL, reference TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_metadata (
 source_id TEXT PRIMARY KEY REFERENCES sources(id),
 evidence_pool TEXT NOT NULL, verification_level TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS snapshots (
 id TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES students(id),
 source_id TEXT NOT NULL REFERENCES sources(id), schema_version INTEGER NOT NULL,
 captured_at TEXT NOT NULL, profile_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS applications (
 id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 college_id TEXT NOT NULL, program TEXT NOT NULL, cycle INTEGER NOT NULL,
 round TEXT NOT NULL, residency TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS applications_cohort ON applications(college_id, cycle, round);
CREATE TABLE IF NOT EXISTS outcome_events (
 id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications(id),
 decision TEXT NOT NULL, occurred_at TEXT NOT NULL,
 verified INTEGER NOT NULL, source_id TEXT NOT NULL REFERENCES sources(id)
);
CREATE INDEX IF NOT EXISTS outcomes_application ON outcome_events(application_id, occurred_at);
"""


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_profile(profile):
    require(isinstance(profile, dict), 'profile must be an object')
    require(profile.get('essay_draft') is None or isinstance(profile['essay_draft'], str), 'essay_draft must be text or null')
    gpa = profile.get('gpa')
    if gpa is not None:
        require(isinstance(gpa, dict), 'gpa must include value, scale, and weighted')
        value, scale = gpa.get('value'), gpa.get('scale')
        require(type(value) in (int, float) and type(scale) in (int, float), 'GPA must be numeric')
        require(math.isfinite(value) and math.isfinite(scale) and 0 <= value <= scale and scale > 0, 'Invalid GPA range')
        require(type(gpa.get('weighted')) is bool, 'GPA weighting must be explicit')
    for field in ('rigor', 'activities', 'interests'):
        values = profile.get(field)
        require(values is None or isinstance(values, list) and all(isinstance(x, str) and x.strip() for x in values), f'{field} must be a list of nonempty strings or null')
    for field in ('activity_records', 'courses'):
        records = profile.get(field)
        require(records is None or isinstance(records, list), f'{field} must be a list or null')
        for record in records or []:
            require(isinstance(record, dict) and isinstance(record.get('name'), str) and bool(record['name'].strip()), f'{field} requires a name')
            if field == 'activity_records':
                hours = record.get('hours_per_week')
                require(hours is None or type(hours) in (int, float) and math.isfinite(hours) and 0 <= hours <= 168, 'Invalid weekly hours')
                role = record.get('role')
                require(role is None or isinstance(role, str), 'role must be text or null')
                achievements = record.get('achievements', [])
                require(isinstance(achievements, list) and all(isinstance(x, str) for x in achievements), 'achievements must be text entries')
                duration = record.get('duration')
                if duration is not None:
                    require(isinstance(duration, dict) and duration.get('unit') in ('year', 'month'), 'Invalid duration unit')
                    value = duration.get('value')
                    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, 'Invalid duration')
            else:
                require(isinstance(record.get('grade'), str) and bool(record['grade'].strip()), 'Course grade must preserve original text')
                credits = record.get('credits')
                require(credits is None or type(credits) in (int, float) and math.isfinite(credits) and credits >= 0, 'Invalid course credits')
                require(record.get('level') is None or isinstance(record['level'], str), 'level must be text or null')
                require(record.get('term') is None or isinstance(record['term'], str), 'term must be text or null')
    sat = profile.get('sat_submitted')
    require(sat is None or type(sat) is int and 400 <= sat <= 1600, 'sat_submitted must be 400–1600 or null')


def ingest(db, bundle):
    require(bundle.get('schema_version') == 1, 'Unsupported schema_version')
    # Validate before inserting; a failed import leaves no partial records.
    for snapshot in bundle.get('snapshots', []):
        validate_profile(snapshot['profile'])
        datetime.fromisoformat(snapshot['captured_at'])
    for source in bundle.get('sources', []):
        require(type(source['synthetic']) is bool, 'synthetic must be a boolean')
        require(source['consent'] in ('granted', 'synthetic'), 'Import requires granted consent or synthetic data')
        require(source['synthetic'] or source['consent'] == 'granted', 'Real data requires granted consent')
        require(source.get('evidence_pool', 'unclassified') in ('self_reported', 'counselor', 'other', 'unclassified'), 'Invalid evidence_pool')
        require(source.get('verification_level', 'unverified') in ('self_reported', 'document_supported', 'counselor_reviewed', 'unverified'), 'Invalid verification_level')
    for app in bundle.get('applications', []):
        require(app['round'] in ('ED', 'EA', 'RD', 'rolling'), 'Unsupported application round')
        require(type(app['cycle']) is int, 'cycle must be an integer')
    for event in bundle.get('outcomes', []):
        require(event['decision'] in ('admit', 'deny', 'defer', 'waitlist', 'withdraw'), 'Invalid decision')
        require(type(event['verified']) is bool, 'verified must be boolean')
        datetime.fromisoformat(event['occurred_at'])
    with db:
        for s in bundle.get('sources', []):
            db.execute('INSERT INTO sources VALUES (?, ?, ?, ?, ?)', (s['id'], s['kind'], s['synthetic'], s['consent'], s['reference']))
        for source in bundle.get('sources', []):
            db.execute('INSERT INTO source_metadata VALUES (?, ?, ?)',
                       (source['id'], source.get('evidence_pool', 'unclassified'), source.get('verification_level', 'unverified')))
        for s in bundle.get('snapshots', []):
            db.execute('INSERT OR IGNORE INTO students VALUES (?)', (s['student_id'],))
            db.execute('INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)', (s['id'], s['student_id'], s['source_id'], 1, s['captured_at'], json.dumps(s['profile'])))
        for a in bundle.get('applications', []):
            db.execute('INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?)', tuple(a[k] for k in ('id', 'snapshot_id', 'college_id', 'program', 'cycle', 'round', 'residency')))
        for e in bundle.get('outcomes', []):
            db.execute('INSERT INTO outcome_events VALUES (?, ?, ?, ?, ?, ?)', tuple(e[k] for k in ('id', 'application_id', 'decision', 'occurred_at', 'verified', 'source_id')))


WEIGHTS = {'gpa': 0.35, 'sat_submitted': 0.25, 'rigor': 0.20, 'activities': 0.15, 'interests': 0.05}


def similarity(query, candidate):
    validate_profile(query)
    components, missing = {}, []
    for field, weight in WEIGHTS.items():
        a, b = query.get(field), candidate.get(field)
        if a is None or b is None:
            missing.append(field)
            continue
        if field == 'gpa':
            # No conversion between unlike grading scales or weighting systems.
            if a['scale'] != b['scale'] or a['weighted'] != b['weighted']:
                missing.append('gpa: incompatible scales or weighting')
                continue
            value = max(0.0, 1 - abs(a['value'] - b['value']) / (a['scale'] * 0.25))
        elif field == 'sat_submitted':
            value = max(0.0, 1 - abs(a - b) / 400)
        else:
            aa, bb = {x.strip().casefold() for x in a}, {x.strip().casefold() for x in b}
            if not aa or not bb:
                missing.append(field)
                continue
            value = len(aa & bb) / len(aa | bb)
        components[field] = {'similarity': round(value, 4), 'weight': weight}
    coverage = sum(c['weight'] for c in components.values())
    score = sum(c['similarity'] * c['weight'] for c in components.values()) / coverage if coverage else 0
    return {'score': round(score, 4), 'coverage': round(coverage, 4), 'components': components, 'missing': missing}


def search(db, query, college_id, cycle, round_, program, residency, limit=10, include_synthetic=False, exclude_student_id=None, deduplicate=True, include_unscored=False):
    validate_profile(query)
    require(limit > 0, 'limit must be positive')
    rows = db.execute('''SELECT a.*, s.student_id, s.profile_json, src.synthetic, src.reference,
      src.id AS source_id, meta.evidence_pool, meta.verification_level
      FROM applications a JOIN snapshots s ON s.id = a.snapshot_id
      JOIN sources src ON src.id = s.source_id
      LEFT JOIN source_metadata meta ON meta.source_id=src.id
      WHERE a.college_id = ? AND a.cycle BETWEEN ? AND ?
      AND a.round = ? AND a.program = ? AND a.residency = ?''',
      (college_id, cycle - 3, cycle - 1, round_, program, residency)).fetchall()
    matches = []
    for row in rows:
        if row['synthetic'] and not include_synthetic or row['student_id'] == exclude_student_id:
            continue
        result = similarity(query, json.loads(row['profile_json']))
        # Coverage-adjusted ranking prevents sparse records from winning on one field.
        if result['coverage'] == 0 and not include_unscored:
            continue
        events = [dict(e) for e in db.execute('''SELECT e.id, e.decision, e.occurred_at, e.verified,
            src.id AS source_id, src.synthetic, src.reference, meta.evidence_pool, meta.verification_level FROM outcome_events e JOIN sources src ON src.id=e.source_id
            LEFT JOIN source_metadata meta ON meta.source_id=src.id
            WHERE e.application_id=? ORDER BY e.occurred_at, e.id''', (row['id'],))]
        if not include_synthetic:
            events = [e for e in events if not e['synthetic']]
        matches.append({'application_id': row['id'], 'student_id': row['student_id'], 'cycle': row['cycle'],
                        'synthetic': bool(row['synthetic']), 'source': row['reference'], 'source_id': row['source_id'],
                        'evidence_pool': 'synthetic' if row['synthetic'] else row['evidence_pool'] or 'unclassified',
                        'verification_level': 'synthetic' if row['synthetic'] else row['verification_level'] or 'unverified',
                        **result, 'rank_score': round(result['score'] * result['coverage'], 4),
                        'outcome_events': events})
    matches.sort(key=lambda m: (-m['rank_score'], -m['cycle'], m['application_id']))
    # One representative application per student in the returned evidence set.
    unique, seen = [], set()
    for match in matches:
        if not deduplicate or match['student_id'] not in seen:
            unique.append(match)
            seen.add(match['student_id'])
    return {'college_id': college_id, 'category': 'insufficient evidence',
            'reason': 'Prototype retrieval scores are not calibrated admission probabilities.',
            'synthetic_included': include_synthetic, 'eligible_students': len(unique), 'matches': unique[:limit]}
