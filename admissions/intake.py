"""Evidence-backed staging for explicit intake fields and essay text."""
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from admissions.core import require, validate_profile

SCHEMA = '''
CREATE TABLE IF NOT EXISTS intake_batches (
 id TEXT PRIMARY KEY, published_snapshot_id TEXT REFERENCES snapshots(id)
);
CREATE TABLE IF NOT EXISTS documents (
 id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES intake_batches(id),
 student_id TEXT NOT NULL, kind TEXT NOT NULL, filename TEXT NOT NULL,
 content TEXT NOT NULL, sha256 TEXT NOT NULL, synthetic INTEGER NOT NULL,
 consent TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_assets (
 document_id TEXT PRIMARY KEY REFERENCES documents(id),
 original_bytes BLOB NOT NULL, pages_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS field_candidates (
 id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
 field TEXT NOT NULL, value_json TEXT, evidence_json TEXT NOT NULL,
 extractor_version TEXT NOT NULL, issue TEXT,
 status TEXT NOT NULL DEFAULT 'pending', reviewer TEXT, reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS review_events (
 id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL REFERENCES field_candidates(id),
 status TEXT NOT NULL, reviewer TEXT NOT NULL, reviewed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profile_evidence (
 snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 field TEXT NOT NULL, candidate_id TEXT NOT NULL REFERENCES field_candidates(id),
 PRIMARY KEY(snapshot_id, field)
);
'''
FIELDS = {'gpa', 'sat_submitted', 'rigor', 'activities', 'interests', 'essay_draft', 'activity_records', 'courses'}


def now():
    return datetime.now(timezone.utc).isoformat()


def setup(db):
    db.executescript(SCHEMA)


def parse_value(field, raw):
    if field in ('activity_records', 'courses'):
        value = json.loads(raw)
    elif field == 'gpa':
        match = re.fullmatch(r'\s*([\d.]+)\s*/\s*([\d.]+)\s+(unweighted|weighted)\s*', raw, re.I)
        require(match is not None, 'Expected GPA like: 3.8 / 4.0 unweighted')
        value = {'value': float(match[1]), 'scale': float(match[2]), 'weighted': match[3].lower() == 'weighted'}
    elif field == 'sat_submitted':
        value = int(raw.strip())
    elif field in ('rigor', 'activities', 'interests'):
        value = list(dict.fromkeys(x.strip().casefold() for x in raw.split(';') if x.strip()))
        require(bool(value), 'No tags found')
    else:
        value = raw
    validate_profile({field: value})
    return value


def extract(content, kind):
    if kind == 'essay':
        require(bool(content.strip()), 'Essay is empty')
        return [('essay_draft', content, {'start_char': 0, 'end_char': len(content), 'quoted_text': content})]
    records = []
    if kind == 'intake-text':
        offset = 0
        for line in content.splitlines(keepends=True):
            match = re.match(r'^\s*([a-z_]+)\s*:\s*(.*?)\s*$', line)
            if match and match[1] in FIELDS:
                a, b = match.span(2)
                records.append((match[1], match[2], {'start_char': offset+a, 'end_char': offset+b, 'quoted_text': content[offset+a:offset+b]}))
            offset += len(line)
    elif kind == 'intake-csv':
        reader = csv.DictReader(io.StringIO(content))
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames)), 'CSV needs unique headers')
        rows = list(reader)
        require(len(rows) == 1, 'CSV must contain exactly one student row per document')
        require(None not in rows[0], 'CSV has extra cells')
        for field, raw in rows[0].items():
            if field in FIELDS and raw and raw.strip():
                records.append((field, raw, {'row': 2, 'column': field, 'quoted_text': raw}))
    else:
        raise ValueError('Supported kinds: intake-text, intake-csv, essay')
    require(bool(records), 'No recognized fields found; use explicit intake field names')
    return records


def stage(db, content, filename, kind, student_id, synthetic, consent, batch_id=None, extracted_records=None, original_bytes=None, pages=None):
    setup(db)
    require(bool(student_id.strip()), 'student_id is required')
    require(type(synthetic) is bool and consent in ('granted', 'synthetic'), 'Consent assertion is required')
    require(synthetic or consent == 'granted', 'Real documents require granted consent')
    require(synthetic or consent != 'synthetic', 'Synthetic consent is only for synthetic documents')
    records = extracted_records if extracted_records is not None else extract(content, kind)
    batch_id = batch_id or str(uuid4())
    existing = db.execute('SELECT * FROM intake_batches WHERE id=?', (batch_id,)).fetchone()
    if existing:
        require(existing['published_snapshot_id'] is None, 'Published batch is immutable')
        owners = db.execute('SELECT DISTINCT student_id, synthetic FROM documents WHERE batch_id=?', (batch_id,)).fetchall()
        require(all(r['student_id'] == student_id and bool(r['synthetic']) == synthetic for r in owners), 'Batch cannot mix students or real/synthetic documents')
    document_id = str(uuid4())
    with db:
        db.execute('INSERT OR IGNORE INTO intake_batches(id) VALUES (?)', (batch_id,))
        db.execute('INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (document_id, batch_id, student_id, kind, filename, content, hashlib.sha256(original_bytes if original_bytes is not None else content.encode()).hexdigest(), synthetic, consent, now()))
        if original_bytes is not None:
            db.execute('INSERT INTO document_assets VALUES (?, ?, ?)', (document_id, original_bytes, json.dumps(pages or [])))
        for record in records:
            field, raw, evidence = record[:3]
            require(field in FIELDS, 'Unknown extracted field')
            issue = record[3] if len(record) == 4 else None
            try:
                value = raw if extracted_records is not None else parse_value(field, raw)
                if not issue:
                    validate_profile({field: value})
            except (ValueError, TypeError) as exc:
                value, issue = None, str(exc)
            db.execute('INSERT INTO field_candidates(id, document_id, field, value_json, evidence_json, extractor_version, issue) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (str(uuid4()), document_id, field, json.dumps(value), json.dumps(evidence), 'document-rules-v2' if extracted_records is not None else 'explicit-fields-v1', issue))
    return inspect_batch(db, batch_id)


def inspect_batch(db, batch_id):
    setup(db)
    batch = db.execute('SELECT * FROM intake_batches WHERE id=?', (batch_id,)).fetchone()
    require(batch is not None, 'Unknown batch')
    rows = db.execute('''SELECT c.*, d.filename FROM field_candidates c JOIN documents d ON d.id=c.document_id
        WHERE d.batch_id=? ORDER BY c.field, c.id''', (batch_id,)).fetchall()
    candidates, values = [], {}
    for row in rows:
        item = dict(row)
        item['value'] = json.loads(item.pop('value_json'))
        item['evidence'] = json.loads(item.pop('evidence_json'))
        candidates.append(item)
        if item['status'] != 'rejected' and not item['issue']:
            values.setdefault(item['field'], set()).add(json.dumps(item['value'], sort_keys=True))
    documents = [dict(r) for r in db.execute('''SELECT d.id, d.filename, d.kind, a.pages_json FROM documents d
        LEFT JOIN document_assets a ON a.document_id=d.id WHERE d.batch_id=?''', (batch_id,))]
    for document in documents:
        document['pages'] = json.loads(document.pop('pages_json') or '[]')
    return {'batch_id': batch_id, 'documents': documents, 'published_snapshot_id': batch['published_snapshot_id'],
            'conflicts': sorted(k for k, v in values.items() if len(v) > 1), 'candidates': candidates}


def review(db, candidate_id, status, reviewer):
    setup(db)
    require(status in ('accepted', 'rejected'), 'Review must accept or reject')
    require(bool(reviewer.strip()), 'Reviewer is required')
    row = db.execute('''SELECT c.*, b.published_snapshot_id FROM field_candidates c
        JOIN documents d ON d.id=c.document_id JOIN intake_batches b ON b.id=d.batch_id WHERE c.id=?''', (candidate_id,)).fetchone()
    require(row is not None, 'Unknown candidate')
    require(row['published_snapshot_id'] is None, 'Published batch is immutable')
    require(status != 'accepted' or row['issue'] is None, 'Invalid candidate cannot be accepted; reject and stage a correction')
    timestamp = now()
    with db:
        db.execute('UPDATE field_candidates SET status=?, reviewer=?, reviewed_at=? WHERE id=?', (status, reviewer, timestamp, candidate_id))
        db.execute('INSERT INTO review_events VALUES (?, ?, ?, ?, ?)', (str(uuid4()), candidate_id, status, reviewer, timestamp))


def publish(db, batch_id, snapshot_id, captured_at):
    report = inspect_batch(db, batch_id)
    require(report['published_snapshot_id'] is None, 'Batch already published')
    datetime.fromisoformat(captured_at)
    require(all(c['status'] != 'pending' for c in report['candidates']), 'Review every candidate before publishing')
    require(not report['conflicts'], 'Resolve conflicting values before publishing')
    accepted = [c for c in report['candidates'] if c['status'] == 'accepted']
    require(bool(accepted), 'No accepted fields')
    profile, evidence = {}, {}
    for c in accepted:
        profile[c['field']] = c['value']
        evidence.setdefault(c['field'], c['id'])
    validate_profile(profile)
    documents = db.execute('SELECT * FROM documents WHERE batch_id=? ORDER BY id', (batch_id,)).fetchall()
    source_id = 'intake:' + batch_id
    with db:
        db.execute('INSERT INTO sources VALUES (?, ?, ?, ?, ?)', (source_id, 'reviewed_intake', documents[0]['synthetic'], documents[0]['consent'], 'intake batch ' + batch_id))
        db.execute('INSERT INTO source_metadata VALUES (?, ?, ?)', (source_id, 'unclassified', 'unverified'))
        db.execute('INSERT OR IGNORE INTO students VALUES (?)', (documents[0]['student_id'],))
        db.execute('INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)', (snapshot_id, documents[0]['student_id'], source_id, 1, captured_at, json.dumps(profile)))
        db.executemany('INSERT INTO profile_evidence VALUES (?, ?, ?)', [(snapshot_id, f, c) for f, c in evidence.items()])
        db.execute('UPDATE intake_batches SET published_snapshot_id=? WHERE id=?', (snapshot_id, batch_id))
    return {'snapshot_id': snapshot_id, 'profile': profile, 'source_id': source_id}


def stage_document(db, path, kind, student_id, synthetic, consent, batch_id=None, ocr=False):
    from pathlib import Path
    from admissions.documents import read_pdf, combine_pages, extract_freeform
    path = Path(path)
    original = path.read_bytes()
    if kind == 'pdf':
        pages = read_pdf(path, ocr=ocr)
    else:
        require(kind == 'freeform', 'Document kind must be pdf or freeform')
        pages = [{'page': 1, 'text': original.decode('utf-8'), 'method': 'text', 'warning': None}]
    content, page_ranges = combine_pages(pages)
    records = extract_freeform(content, page_ranges)
    return stage(db, content, path.name, kind, student_id, synthetic, consent, batch_id,
                 extracted_records=records, original_bytes=original, pages=page_ranges)
