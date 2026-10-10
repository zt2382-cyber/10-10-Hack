"""Source-scoped outcome descriptions and ranking sensitivity, not predictions."""
from datetime import datetime, timezone

from admissions.core import require

LEAN_GAP = .03
TEXT = {'closer_to_admitted': 'Closer to the admitted examples in this evidence pool.',
        'closer_to_denied': 'Closer to the denied examples in this evidence pool.',
        'in_between': 'Similar distance to the admitted and denied examples.'}


def event_time(event):
    date = datetime.fromisoformat(event['occurred_at'])
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)


def outcome_view(match):
    events = match['outcome_events']
    latest = []
    if events:
        last = max(event_time(e) for e in events)
        latest = [e for e in events if event_time(e) == last]
    decisions = {e['decision'] for e in latest}
    decision = next(iter(decisions)) if len(decisions) == 1 else 'conflicting' if decisions else 'unknown'
    profile_pool = match.get('evidence_pool', 'unclassified')
    event_pools = {e.get('evidence_pool') or 'unclassified' for e in latest}
    synthetic = match['synthetic'] or any(e['synthetic'] for e in latest)
    if synthetic:
        pool = 'synthetic'
    elif not latest or event_pools == {profile_pool}:
        pool = profile_pool
    else:
        pool = profile_pool + ' -> ' + '+'.join(sorted(event_pools))
    supported = ('document_supported', 'counselor_reviewed')
    verified = bool(latest) and not synthetic and decision != 'conflicting' and match.get('verification_level') in supported and all(e['verified'] and e.get('verification_level') in supported for e in latest)
    return {'decision': decision, 'pool': pool, 'synthetic': bool(synthetic), 'verified': verified,
            'profile_verification': match.get('verification_level','unverified'),
            'outcome_verification': sorted({e.get('verification_level') or 'unverified' for e in latest}),
            'latest_events': latest}


def lean(gap):
    if gap >= LEAN_GAP: return 'closer_to_admitted'
    if gap <= -LEAN_GAP: return 'closer_to_denied'
    return 'in_between'


def mean(values):
    values = list(values)
    return sum(values)/len(values) if values else None


def example(match, view):
    return {'application_id': match['application_id'], 'student_id': match['student_id'],
            'distance': round(1-match['rank_score'],4), 'coverage': match['coverage'],
            'decision': view['decision'], 'synthetic':view['synthetic'],
            'source':match['source'], 'components':match['components'],
            'profile_evidence':match.get('profile_evidence',[]),
            'matching_passages':match['matching_passages'], 'outcome_evidence':view['latest_events']}


def outcome_comparisons(matches, neighbours=7, needed=15):
    require(type(neighbours) is int and neighbours > 0, 'neighbours must be positive')
    require(type(needed) is int and needed > 0, 'needed must be positive')
    groups = {}
    # Partition by provenance AND verification. Never borrow support across pools.
    for match in sorted(matches,key=lambda m:(-m['rank_score'],-m['cycle'],m['application_id'])):
        view = outcome_view(match)
        key = (view['pool'], view['synthetic'], view['verified'], view['profile_verification'], tuple(view['outcome_verification']))
        group = groups.setdefault(key, [])
        if not any(m['student_id']==match['student_id'] for m,_ in group):
            group.append((match,view))
    pools = []
    for key, rows in sorted(groups.items()):
        pool, synthetic, verified, profile_verification, outcome_verification = key
        admitted = [(m,v) for m,v in rows if v['decision']=='admit']
        denied = [(m,v) for m,v in rows if v['decision']=='deny']
        counts = {d:sum(v['decision']==d for _,v in rows) for d in ('admit','deny','waitlist','defer','withdraw','unknown','conflicting')}
        a, d = admitted[:neighbours], denied[:neighbours]
        da = mean(1-m['rank_score'] for m,_ in a)
        dd = mean(1-m['rank_score'] for m,_ in d)
        gap = dd-da if da is not None and dd is not None else None
        status = 'ok' if len(admitted)>=needed and len(denied)>=needed else 'not_enough' if admitted and denied else 'none'
        direction = lean(gap) if status=='ok' else None
        parts = []
        for field in sorted({k for m,_ in a+d for k in m['components']}):
            def component_summary(near):
                comps = [m['components'][field] for m,_ in near if field in m['components']]
                return {'n':len(comps),'mean_similarity':mean(c['similarity'] for c in comps), 'mean_coverage':mean(c['coverage'] for c in comps)}
            parts.append({'component':field,'admitted':component_summary(a),'denied':component_summary(d)})
        pool_id = '|'.join((pool,'synthetic' if synthetic else 'real','verified' if verified else 'unverified',profile_verification,','.join(outcome_verification)))
        pools.append({'pool_id':pool_id,'evidence_pool':pool,'synthetic':synthetic,'verified':verified,
            'profile_verification':profile_verification,'outcome_verification':list(outcome_verification),
            'status':status,'counts':counts,'n_students':len(rows),'needed_per_group':needed,'neighbours':neighbours,
            'sources':sorted({m['source'] for m,_ in rows}),
            'd_admitted':round(da,4) if da is not None else None,'d_denied':round(dd,4) if dd is not None else None,
            'gap':round(gap,4) if gap is not None else None,'lean':direction,
            'text':TEXT[direction] if direction else 'Not enough admitted and denied examples in this evidence pool to describe a direction.',
            'nearest_admitted':[example(m,v) for m,v in a[:3]],'nearest_denied':[example(m,v) for m,v in d[:3]],
            'parts':parts})
    return {'neighbours':neighbours,'needed_per_group':needed,'pools':pools,
            'distance_definition':'1 minus coverage-adjusted rank score',
            'caveat':'These describe selected historical examples. Self-reporting, missing information, and changing admissions policies limit interpretation. Synthetic examples are demonstrations only.'}


def stability(base_matches, base_pools, variants, top_k=10):
    """Variants contain reranked full matches; outcomes never enter reranking."""
    base_ids = [m['application_id'] for m in base_matches[:top_k]]
    scenarios, flips = [], []
    base_by_id = {p['pool_id']:p for p in base_pools['pools']}
    for name, matches, comparison in variants:
        ids = [m['application_id'] for m in matches[:top_k]]
        union = set(base_ids)|set(ids)
        by_id = {p['pool_id']:p for p in comparison['pools']}
        changes = []
        for pool_id in sorted(set(base_by_id)|set(by_id)):
            before, after = base_by_id.get(pool_id), by_id.get(pool_id)
            b = (before['status'],before['lean']) if before else ('absent',None)
            a = (after['status'],after['lean']) if after else ('absent',None)
            if b != a:
                change = {'scenario':name,'pool_id':pool_id,'before':{'status':b[0],'lean':b[1]},'after':{'status':a[0],'lean':a[1]}}
                changes.append(change); flips.append(change)
        scenarios.append({'scenario':name,'top_ids':ids,'top_k_jaccard':round(len(set(base_ids)&set(ids))/len(union),4) if union else None,
                          'top_order_changed':ids!=base_ids,'pool_changes':changes})
    return {'top_k':top_k,'status':'ok' if base_ids else 'none','scenarios':scenarios,
            'ranking_steady': all(not s['top_order_changed'] for s in scenarios) if base_ids else None,
            'outcome_direction_steady':not flips if any(p['status']=='ok' for p in base_pools['pools']) else None,
            'flips':flips,'caveat':'Sensitivity to these chosen perturbations does not measure accuracy or causal effects.'}
