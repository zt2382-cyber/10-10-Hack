"""Masked semantic retrieval. Vectors stay in a bounded process-local cache.

Optional data/cases/essay_corpus.json contains records with case_id, essay and
activities_note. Without full essays, school cases use explicitly marked themes.
"""
from collections import OrderedDict
from hashlib import sha256
import json
import math
from pathlib import Path
from threading import Lock

from . import nicrron, privacy

CORPUS = Path(__file__).resolve().parent.parent / "data/cases/essay_corpus.json"
_CACHE = OrderedDict()
_LOCK = Lock()
CACHE_LIMIT = 2048
BATCH_SIZE = 64


def distance(a, b):
    """Cosine distance scaled to [0, 1]; invalid vectors are missing data."""
    try:
        if not a or not b or len(a) != len(b):
            return None
        if not all(math.isfinite(x) for x in (*a, *b)):
            return None
        norm = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
        if not norm:
            return None
        return max(0.0, min(1.0, (1 - sum(x*y for x, y in zip(a, b))/norm)/2))
    except (TypeError, ValueError, OverflowError):
        return None


def _masked(text):
    result = privacy.mask(str(text or ""))
    return "" if result.get("blocked") else result["text"].strip()


def _failure(result):
    """Public diagnostics use fixed messages, never provider text or credentials."""
    status = result.get("http_status")
    if result.get("error") == "no key":
        return "missing_key", "The server has no Nicrron API key. Set NICRRON_API_KEY or NICRRON_KEY_FILE in the terminal that starts the server, then restart it."
    if status in (401, 403):
        return "authentication", "The embedding gateway rejected access. Check that the Nicrron key is valid and permitted to use the embedding model."
    if status == 402:
        return "credits", "The embedding gateway requires available credits. Check the gateway account balance."
    if status in (404, 405):
        return "endpoint", "The gateway does not provide the requested embedding endpoint or model. Essay reading can work while embeddings are unavailable."
    if status in (400, 422):
        return "request_rejected", "The gateway rejected the embedding model or input format. Check support for openai/text-embedding-3-small at /v1/embeddings."
    if status == 429:
        return "rate_limit", "The embedding gateway rate limit or quota was reached. Retry after checking the account quota."
    if status == 0:
        return "network", "The server could not reach the embedding gateway. Check its network connection and retry."
    if isinstance(status, int) and status >= 500:
        return "gateway", "The embedding gateway returned a server error. Retry the comparison later."
    return "invalid_response", "The embedding service failed or returned unusable vectors. Check the gateway's embedding support."


def prepare(student, essay, rows, enabled=True, embed_fn=None):
    """Embed once per run for all selected colleges; no vectors enter responses.

    Returns an internal context; public diagnostics and retrieval expose only IDs,
    distances and whether each comparison used a full essay or theme summary.
    """
    context = {"student": {}, "cases": {}, "retrieval": [],
               "report": {"status": "off", "model": nicrron.DEFAULT_EMBED_MODEL,
                          "documents": 0, "note": "Semantic comparison is disabled."}}
    if not enabled:
        return context
    supplemental = {}
    if CORPUS.exists():
        try:
            records = json.loads(CORPUS.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError("Corpus must be an array")
            supplemental = {r["case_id"]: r for r in records}
        except (OSError, ValueError, TypeError, KeyError):
            context["report"].update(status="unavailable", error_code="invalid_corpus",
                error="The historical essay corpus could not be read. Check essay_corpus.json is an array of records with case_id.")
            return context
    documents = {}
    kinds = {}
    documents[("student", "essay")] = _masked(essay)
    activities = student.get("activities") or []
    documents[("student", "activity_text")] = _masked(
        "\n".join(json.dumps(a, ensure_ascii=False) if isinstance(a, dict) else str(a) for a in activities))
    for row in rows:
        cid = row["case_id"]
        extra = supplemental.get(cid, {})
        full = extra.get("essay") or row.get("essay")
        documents[(cid, "essay")] = _masked(full or row.get("essay_theme"))
        documents[(cid, "activity_text")] = _masked(extra.get("activities_note") or row.get("activities_note"))
        kinds[cid] = "full_essay" if full else "theme_summary"
    # Do not call an external service if neither student text field is available.
    if not any(documents[("student", field)] for field in ("essay", "activity_text")):
        context["report"].update(status="empty", note="No eligible student text to embed.")
        return context
    keys = {loc: (nicrron.DEFAULT_EMBED_MODEL, sha256(text.encode()).hexdigest())
            for loc, text in documents.items() if text}
    vectors = {}
    with _LOCK:
        for key in keys.values():
            if key in _CACHE:
                vectors[key] = _CACHE[key]
    pending = {keys[loc]: text for loc, text in documents.items() if loc in keys and keys[loc] not in vectors}
    items = list(pending.items())
    failed = False
    failure = None
    for start in range(0, len(items), BATCH_SIZE):
        batch = items[start:start+BATCH_SIZE]
        try:
            result = (embed_fn or nicrron.embed)([text for _, text in batch])
            vs = result.get("vectors", [])
            if not result.get("ok") or len(vs) != len(batch):
                failed = True
                failure = failure or _failure(result)
                continue
            for (key, _), vector in zip(batch, vs):
                if distance(vector, vector) is None:
                    failed = True
                    failure = failure or _failure({})
                    continue
                vectors[key] = tuple(vector)
                with _LOCK:
                    _CACHE[key] = tuple(vector)
                    while len(_CACHE) > CACHE_LIMIT:
                        _CACHE.popitem(last=False)
        except Exception:
            failed = True
            failure = failure or _failure({})
    for (cid, field), key in keys.items():
        if key in vectors:
            target = context["student"] if cid == "student" else context["cases"].setdefault(cid, {})
            target[field] = vectors[key]
    for cid, fields in context["cases"].items():
        d = distance(context["student"].get("essay"), fields.get("essay"))
        if d is not None:
            context["retrieval"].append({"case_id": cid, "distance": round(d, 4), "text_kind": kinds[cid]})
    if failure:
        context["report"].update(error_code=failure[0], error=failure[1])
    context["retrieval"].sort(key=lambda r: (r["distance"], r["case_id"]))
    context["report"].update(status="partial" if failed and context["student"] else
                             "unavailable" if failed else "ok", documents=len(context["cases"]),
                             note="Semantic distances compare content, not essay quality. Missing text is omitted.")
    return context
