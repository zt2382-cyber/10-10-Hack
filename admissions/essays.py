"""Local semantic essay retrieval. Scores describe content, not admission chances."""
import hashlib
import json
import math

from admissions.core import require, search

DEFAULT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
INDEX_SCHEMA = '''
CREATE TABLE IF NOT EXISTS essay_embeddings (
 snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 model_key TEXT NOT NULL, text_hash TEXT NOT NULL,
 chunks_json TEXT NOT NULL, vectors_json TEXT NOT NULL,
 PRIMARY KEY (snapshot_id, model_key)
);
'''


class LocalEmbedder:
    def __init__(self, model=DEFAULT_MODEL, revision=None):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError('Install essay dependencies: pip install -e ".[essays]"') from exc
        self.model = SentenceTransformer(model, revision=revision, trust_remote_code=False)
        resolved = getattr(self.model[0].auto_model.config, '_commit_hash', None)
        require(bool(resolved), 'Model must have a resolved repository revision for cache versioning')
        self.key = f'{model}@{resolved}:passages-v1'

    def chunks(self, text):
        # Offsets preserve verbatim evidence; reserve room for model special tokens.
        tokenizer = self.model.tokenizer
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
        offsets = encoded['offset_mapping']
        size = self.model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
        require(size > 0, 'Invalid model token limit')
        overlap = min(32, size // 4)
        chunks = []
        for start in range(0, len(offsets), size - overlap):
            window = offsets[start:start + size]
            if not window:
                break
            a, b = window[0][0], window[-1][1]
            chunks.append({'start_char': a, 'end_char': b, 'text': text[a:b]})
            if start + size >= len(offsets):
                break
        return chunks

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def essay_text(profile):
    text = profile.get('essay_draft')
    require(text is None or isinstance(text, str), 'essay_draft must be text or null')
    return text if text and text.strip() else None


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normalize(vector):
    require(isinstance(vector, (list, tuple)) and bool(vector), 'Empty embedding')
    require(all(type(v) in (int, float) and math.isfinite(v) for v in vector), 'Invalid embedding values')
    norm = math.sqrt(sum(v * v for v in vector))
    require(norm > 0, 'Zero embedding')
    return [v / norm for v in vector]


def embed_text(embedder, text):
    chunks = embedder.chunks(text)
    require(bool(chunks), 'Essay produced no passages')
    vectors = embedder.encode([c['text'] for c in chunks])
    require(len(vectors) == len(chunks), 'Embedding count mismatch')
    vectors = [normalize(v) for v in vectors]
    require(len({len(v) for v in vectors}) == 1, 'Embedding dimension mismatch')
    return chunks, vectors


def index_essays(db, embedder, include_synthetic=False):
    db.executescript(INDEX_SCHEMA)
    indexed = skipped = 0
    rows = db.execute('''SELECT s.id, s.profile_json, src.synthetic FROM snapshots s
        JOIN sources src ON src.id=s.source_id''').fetchall()
    # Compute before the transaction so a model failure cannot partially update the index.
    pending = []
    for row in rows:
        if row['synthetic'] and not include_synthetic:
            continue
        text = essay_text(json.loads(row['profile_json']))
        if text is None:
            skipped += 1
            continue
        digest = text_hash(text)
        cached = db.execute('SELECT text_hash FROM essay_embeddings WHERE snapshot_id=? AND model_key=?',
                            (row['id'], embedder.key)).fetchone()
        if cached and cached['text_hash'] == digest:
            skipped += 1
            continue
        chunks, vectors = embed_text(embedder, text)
        pending.append((row['id'], embedder.key, digest, json.dumps(chunks), json.dumps(vectors)))
    with db:
        db.executemany('INSERT OR REPLACE INTO essay_embeddings VALUES (?, ?, ?, ?, ?)', pending)
    indexed = len(pending)
    return {'model': embedder.key, 'indexed': indexed, 'skipped': skipped}


def essay_search(db, query, embedder, college_id, cycle, round_, program, residency,
                 limit=10, include_synthetic=False, exclude_student_id=None,
                 min_academic_coverage=0.5, min_academic_score=0.5):
    require(limit > 0, 'limit must be positive')
    require(0 <= min_academic_coverage <= 1 and 0 <= min_academic_score <= 1, 'Academic thresholds must be between 0 and 1')
    text = essay_text(query)
    require(text is not None, 'Query requires a nonempty essay_draft')
    db.executescript(INDEX_SCHEMA)
    # Use every comparable student, rather than just the academic top ten.
    pool = search(db, query, college_id, cycle, round_, program, residency,
                  limit=2147483647, include_synthetic=include_synthetic, exclude_student_id=exclude_student_id, deduplicate=False)
    query_chunks, query_vectors = embed_text(embedder, text)
    matches, unindexed, excluded = [], 0, 0
    for match in pool['matches']:
        if match['coverage'] < min_academic_coverage or match['score'] < min_academic_score:
            excluded += 1
            continue
        row = db.execute('''SELECT e.*, s.profile_json FROM applications a
            JOIN snapshots s ON s.id=a.snapshot_id
            LEFT JOIN essay_embeddings e ON e.snapshot_id=s.id AND e.model_key=?
            WHERE a.id=?''', (embedder.key, match['application_id'])).fetchone()
        candidate_text = essay_text(json.loads(row['profile_json']))
        if not candidate_text or row['text_hash'] != text_hash(candidate_text):
            unindexed += 1
            continue
        comparison = compare_passages(query_chunks, query_vectors, json.loads(row['chunks_json']), json.loads(row['vectors_json']))
        matches.append({**match, **comparison})
    matches.sort(key=lambda m: (-m['essay_similarity'], -m['rank_score'], m['application_id']))
    unique, seen = [], set()
    for match in matches:
        if match['student_id'] not in seen:
            unique.append(match)
            seen.add(match['student_id'])
    return {'college_id': college_id, 'model': embedder.key, 'category': 'insufficient evidence',
            'reason': 'Essay similarity measures content resemblance, not quality or admission probability.',
            'eligible_students': len({m['student_id'] for m in pool['matches']}), 'unindexed_or_missing_essays': unindexed,
            'excluded_by_academic_thresholds': excluded, 'synthetic_included': include_synthetic,
            'matches': unique[:limit]}


def compare_passages(query_chunks, query_vectors, chunks, vectors):
    require(len(chunks) == len(vectors) and bool(vectors), 'Invalid cached embedding record')
    vectors = [normalize(v) for v in vectors]
    require(all(len(v) == len(query_vectors[0]) for v in vectors), 'Query/index embedding dimensions differ')
    scores = [[max(-1.0, min(1.0, sum(a*b for a, b in zip(q, v)))) for v in vectors] for q in query_vectors]
    # Symmetric mean of best passage matches: less dominated by a single shared phrase.
    score = (sum(max(r) for r in scores) / len(scores)
             + sum(max(r[j] for r in scores) for j in range(len(vectors))) / len(vectors)) / 2
    best_i, best_j = max(((i, j) for i in range(len(scores)) for j in range(len(vectors))), key=lambda ij: scores[ij[0]][ij[1]])
    return {'essay_similarity': round(score, 4), 'matching_passages': {'query': query_chunks[best_i], 'historical': chunks[best_j], 'cosine_similarity': round(scores[best_i][best_j], 4)}}
