"""Standalone essay-bank retrieval, independent of applicant outcomes.

Gateway embeddings when available, explicitly labelled local TF-IDF otherwise.
Student essays are masked before comparison and never saved.
"""
from collections import Counter
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse

from . import nicrron, privacy, semantic

BANK_DIR = Path(__file__).resolve().parent.parent / 'data/essays'
STOP = set('a an and are as at be been but by for from had has have he her him his i in is it its me my of on or our she so than that the their them they this to was we were which who with you your'.split())
NOTE = 'Content similarity describes shared subject matter, not writing quality or admission likelihood.'


def tokens(text):
    return [w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP]


def safe_url(value):
    value = str(value or '')
    return value if urlparse(value).scheme in ('https', 'http') else ''


def load_bank(directory=None):
    records = []
    for name in ('starter_bank.json', 'openessays_bank.json', 'custom_bank.json'):
        path = (directory or BANK_DIR) / name
        if not path.exists(): continue
        rows = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(rows, list): raise ValueError('Bank must contain a list')
        records.extend(rows)
    eligible, seen = [], set()
    for r in records:
        if not isinstance(r, dict) or not isinstance(r.get('text'), str) or not r.get('id'): continue
        if r['id'] in seen: continue
        if r.get('license') not in ('ORIGINAL_DEMO', 'CC0', 'CC_BY_4_0', 'CC_BY_NC_SA_4_0') and r.get('permission_confirmed') is not True: continue
        masked = privacy.mask(r['text'])
        if masked['blocked'] or not masked['text'].strip(): continue
        seen.add(r['id']); eligible.append(dict(r, text=masked['text']))
    return eligible


def lexical(query, records):
    """One shared TF-IDF space; candidates with no shared terms are omitted."""
    docs = [Counter(tokens(query))] + [Counter(tokens(r['text'])) for r in records]
    df = Counter(t for doc in docs for t in doc)
    vectors = [{t: (1+math.log(n))*(1+math.log((len(docs)+1)/(df[t]+1))) for t,n in doc.items()} for doc in docs]
    def cos(a,b):
        norm = math.sqrt(sum(x*x for x in a.values())*sum(x*x for x in b.values()))
        return sum(v*b.get(t,0) for t,v in a.items())/norm if norm else 0
    return {r['id']: cos(vectors[0], v) for r,v in zip(records,vectors[1:])}


def search(essay, degree_level='undergraduate', limit=5, use_model=True, embed_fn=None, directory=None):
    result = {'status': 'empty', 'method': None, 'note': NOTE, 'matches': [], 'bank_size': 0,
              'degree_level': degree_level, 'query_words': 0}
    if not isinstance(essay, str) or not essay.strip(): return result
    if degree_level not in ('undergraduate', 'graduate'): raise ValueError('Unsupported essay level')
    if type(limit) is not int or not 1 <= limit <= 10: raise ValueError('Limit must be 1 to 10')
    if len(essay) > 60000: raise ValueError('Essay exceeds 60,000 characters')
    masked = privacy.mask(essay)
    if masked['blocked']:
        result['status'] = 'blocked'; return result
    query = masked['text']; result['query_words'] = len(query.split())
    try: bank = [r for r in load_bank(directory) if r.get('degree_level') == degree_level]
    except (OSError, ValueError, TypeError):
        result['status'] = 'bank_unavailable'; return result
    result['bank_size'] = len(bank)
    if not bank:
        result['status'] = 'no_baseline'; return result
    scores = None
    # Reuse the bounded content/model cache without applicant IDs or outcome joins.
    if use_model and (embed_fn is not None or nicrron.has_key()):
        context = semantic.prepare({}, query, [{'case_id': r['id'], 'essay': r['text']} for r in bank], True, embed_fn)
        if len(context['retrieval']) == len(bank) and context['report']['status'] == 'ok':
            scores = {r['case_id']: max(-1.0, min(1.0, 1-2*r['distance'])) for r in context['retrieval']}
            result['method'] = 'embedding'
    if scores is None:
        scores = lexical(query, bank); result['method'] = 'local_text'
    query_terms = set(tokens(query))
    ranked = sorted(bank, key=lambda r: (-scores[r['id']], r['id']))
    for r in ranked:
        score = scores[r['id']]
        if score <= 0: continue
        shared = sorted(query_terms & set(tokens(r['text'])))[:8]
        result['matches'].append({'id': r['id'], 'title': r.get('title') or r['id'],
            'school': r.get('school') or '', 'program': r.get('program') or '',
            'essay_type': r.get('essay_type') or '', 'synthetic': bool(r.get('synthetic')),
            'similarity': round(score,4), 'shared_terms': shared,
            'excerpt': ' '.join(r['text'].split()[:65]), 'text': r['text'],
            'source_url': safe_url(r.get('source_url')), 'original_url': safe_url(r.get('original_url')),
            'attribution': r.get('attribution') or '', 'license': r.get('license') or '',
            'license_url': safe_url(r.get('license_url'))})
        if len(result['matches']) >= limit: break
    result['status'] = 'ok' if result['matches'] else 'no_matches'
    return result
