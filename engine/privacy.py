"""Privacy gate: runs in plain code, before any AI model sees an essay.

mask(text) replaces details that identify a student with tags like [NAME], and blocks text that contains
instructions aimed at an AI. No model is used here. Standard library only.

What it catches: email addresses (also written out: "jane dot doe at example dot com"), phone numbers (US,
international, run together, dotted), street addresses in any letter case (with unit, city/state/ZIP when
written), social security numbers, dates of birth (labelled, "born on/in ...", or a bare date that looks like a
birth date), names (introduced by "my name is", "I am", "I'm", "call me", a relative such as "my mother Maria
Gomez", or a title such as "Mr. Delgado"; every other place that same name appears is masked too) and any
capitalised name followed by High School / HS / High / Academy / Prep / School. What it does not do: it does not
rename people or places that the student writes about with no such cue (a neighbour, a street with no number).
Counselors should still skim the masked text.

looks_personal(text) is the one shared check other modules use to refuse text that carries a personal detail.
"""
from __future__ import annotations

import re
import unicodedata

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
_MON = MONTH + r"(?![A-Za-z])"
_YEAR = r"(?:19[89]\d|20[01]\d)"
_DAY = r"(?:0?[1-9]|[12]\d|3[01])"
_MO = r"(?:0?[1-9]|1[0-2])"
# Dates written after a birth keyword. Longest forms first: alternation takes the first that fits.
_DATE = (
    r"(?:" + _MON + r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+" + _MON + r",?\s+\d{4}"
    r"|\d{1,2}[/.\-]\d{1,2}[/.\-](?:\d{4}|\d{2})"
    r"|(?:19|20)\d{2}[/.\-]\d{1,2}[/.\-]\d{1,2}"
    r"|" + _MON + r"\s+\d{1,2}(?:st|nd|rd|th)?\b"
    r"|" + _MON + r",?\s+(?:of\s+)?\d{4}"
    r"|" + _MON + r"|(?:19|20)\d{2}\b)"
)
_SUFFIX = (r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way|place|pl|circle|cir|"
           r"terrace|ter|highway|hwy|parkway|pkwy|trail|trl|square|sq|plaza|alley|loop)")
_AMBIGUOUS_SUFFIX = {"way", "dr", "ct", "pl", "ter", "sq", "cir", "trl", "ln", "loop", "alley", "plaza", "place"}
_CITY_STATE_ZIP = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3},\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?"
_ADDR = re.compile(
    r"\b\d{1,6}[ \t]+((?:[A-Za-z0-9.'’\-]+[ \t]+){1,3}?)(" + _SUFFIX + r")\b\.?"
    r"(?:,?[ \t]+(?:apt|apartment|unit|suite|ste|#)\.?[ \t]*[\w\-]+)?"
    r"(?:,[ \t]*" + _CITY_STATE_ZIP + r")?", re.I)
_ADDR_NOT_A_STREET = {  # words that mean the number is a count or a time, not a house number
    "the", "of", "a", "an", "to", "on", "in", "at", "my", "our", "and", "or", "for", "with", "from", "by", "that",
    "this", "it", "its", "his", "her", "their", "your", "years", "year", "days", "day", "hours", "hour", "minutes",
    "minute", "weeks", "week", "months", "month", "times", "time", "people", "students", "other", "more", "few",
    "miles", "mile", "feet", "steps", "percent", "than", "about", "over", "under", "around", "nearly", "almost",
    "long", "short", "away", "off", "up", "down", "out", "was", "is", "are", "were", "be", "as", "so", "but",
    "if", "when", "while", "i", "we", "you", "they", "he", "she", "one", "two", "three", "four", "five", "ten",
}
_PO_BOX = re.compile(r"\bP\.?\s?O\.?\s+Box\s+\d+\b", re.I)

# Schools: a capitalised name followed by High School / HS / High / Academy / Prep / School.
_SCHOOL_WORD = (r"(?:High[ \t]+School|HS|High|Academy|Preparatory(?:[ \t]+School)?|Prep(?:[ \t]+School)?|"
                r"Secondary[ \t]+School|Charter[ \t]+School|Day[ \t]+School|Middle[ \t]+School|"
                r"Elementary[ \t]+School|School)")
_SCHOOL = re.compile(
    r"\b((?:(?!(?:High|Middle|Elementary|Prep|Preparatory|Day|Charter|Secondary|School)\b)"
    r"[A-Z][A-Za-z.'’\-]*[ \t]+){1,5})(" + _SCHOOL_WORD + r")\b")
_SCHOOL_LEAD_STOP = {
    "in", "at", "the", "my", "our", "a", "an", "during", "throughout", "after", "before", "when", "since", "from",
    "to", "of", "and", "but", "or", "so", "as", "if", "then", "i", "we", "every", "each", "this", "that", "by",
    "for", "with", "about", "all", "one", "some", "going", "go", "went", "back", "leaving", "left", "between",
    "attend", "attended", "attending", "graduate", "graduated", "while", "until", "once", "now", "later",
    "also", "still", "even", "just", "because", "though", "although", "into", "through", "across", "over",
}
_SCHOOL_GENERIC = {
    "medical", "law", "business", "graduate", "summer", "sunday", "boarding", "public", "private", "art", "arts",
    "old", "technical", "trade", "driving", "grade", "primary", "online", "home", "bible", "dance", "music",
    "nursing", "dental", "flight", "night", "weekend", "hebrew", "language", "same", "new", "first", "second",
    "last", "whole", "entire", "other", "another", "high", "middle", "elementary", "junior", "senior",
}

_PHONE_PATTERNS = [
    re.compile(r"(?<![\w+])\+\s?\d{1,3}(?:[\s.\-()]*\d){7,12}(?!\w)"),                           # +44 20 7946 0958
    re.compile(r"(?<![\w\-])(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?![\w\-])"),  # 2125551212, 212.555.0147
    re.compile(r"(?<![\w\-])0\d{2,4}[\s.\-]\d{3,4}[\s.\-]\d{3,4}(?![\w\-])"),                    # 020 7946 0958
    re.compile(r"(?<![\w\-])\d{3}[\-.]\d{4}(?![\w\-])"),                                         # 555-0147
]

_OBFUSCATED_EMAIL = re.compile(
    r"(?<![\w.])(?!(?:me|us|you|him|her|them|email|mail|contact|reach|text|call|is|here|found|available|it)\s+at\b)"
    r"[A-Za-z0-9_\-]+(?:(?:\s+dot\s+|\s*\(dot\)\s*|\s*\[dot\]\s*|\.)[A-Za-z0-9_\-]+)*"
    r"(?P<at>\s+at\s+|\s*\(at\)\s*|\s*\[at\]\s*)"
    r"[A-Za-z0-9\-]+(?:(?:\s+dot\s+|\s*\(dot\)\s*|\s*\[dot\]\s*|\.)[A-Za-z]{2,}){1,3}(?![\w@])", re.I)
_DOT_WORD = re.compile(r"\sdot\s|\(dot\)|\[dot\]", re.I)

# Dates that look like a birth date, written on their own (students are roughly 1980-2019 births).
_BARE_DATES = [
    re.compile(r"(?<![\d/\-.])" + _YEAR + r"[-/.]" + _MO + r"[-/.]" + _DAY + r"(?![\d/\-])"),
    re.compile(r"(?<![\d/\-.])" + _DAY + r"[/.\-]" + _DAY + r"[/.\-]" + _YEAR + r"(?![\d/\-])"),
    re.compile(r"(?<![\d/\-.])" + _MO + r"/" + _DAY + r"/(?:0\d|1[0-5]|9\d)(?![\d/\-])"),
]
_BORN = re.compile(r"\b(?:date\s+of\s+birth|dob|birthday|birthdate|birth\s+date|born(?:\s+on|\s+in)?)\b[:\s]*(?:is\s+)?"
                   + _DATE, re.I)

# Order matters: more specific patterns run first so a number is not claimed by the wrong kind.
_PATTERNS = [
    ("email", "[EMAIL]", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")),
    ("ssn", "[SSN]", re.compile(r"(?<!\d)\d{3}[- ]\d{2}[- ]\d{4}(?!\d)")),
]

# ----------------------------------------------------------------------------- names
_NW = r"[A-Z][A-Za-z'’\-]+"
_NAME_TRIGGER = re.compile(
    r"(?i:\b(?:my\s+(?:full\s+)?name\s+is|my\s+name['’]s|i\s+am\s+called|i['’]m\s+called|i\s+go\s+by|call\s+me|"
    r"this\s+is\s+me,|name:|i\s+am|i['’]m))[ \t]+(" + _NW + r"(?:[ \t]+" + _NW + r"){0,3})")
_RELATIVE = re.compile(
    r"(?i:\b(?:my|our)\s+(?:(?:step|half|great|grand)[\s\-]?)?(?:mother|mom|mum|mama|father|dad|papa|brother|sister|"
    r"sibling|aunt|auntie|uncle|cousin|grandmother|grandma|grandmom|grandfather|grandpa|grandad|nephew|niece|son|daughter|"
    r"husband|wife|friend|best\s+friend|teacher|counselor|counsellor|mentor|coach|boss|neighbou?r|girlfriend|"
    r"boyfriend|partner|roommate|classmate|principal|guardian)),?[ \t]+(" + _NW + r"(?:[ \t]+" + _NW + r")?)")
_TITLE = re.compile(r"\b(?:Mr|Mrs|Ms|Mx|Dr|Prof|Professor|Coach|Mister)\b\.?[ \t]+(" + _NW + r"(?:[ \t]+" + _NW + r")?)")
_TITLE_TAIL = re.compile(r"\b(?:Mr|Mrs|Ms|Mx|Dr|Prof|Professor|Coach|Mister)\b\.?[ \t]+\[NAME\]")
_NAME_STOP = {
    "i", "the", "a", "an", "and", "but", "or", "so", "yet", "my", "is", "it", "in", "on", "at", "if", "to", "we", "he",
    "she", "they", "you", "who", "when", "while", "as", "then", "though", "although", "because", "since", "after",
    "before", "what", "that", "this", "there", "here", "not", "very", "also", "just", "still", "always", "never",
    "now", "again", "each", "every", "mr", "mrs", "ms", "mx", "dr", "miss", "coach", "prof", "professor", "was",
    "were", "has", "had", "did", "do", "does", "said", "told", "will", "would", "can", "could", "should", "with",
    "from", "for", "by", "of", "our", "your", "his", "her", "their", "its", "one", "some", "all", "no", "yes",
    "today", "yesterday", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "am", "are", "be", "been", "being", "me", "us", "them", "him", "how", "why", "where", "which", "whose",
    # nationalities, faiths and the like: "I am American" is not a name
    "american", "african", "asian", "black", "white", "latino", "latina", "latinx", "hispanic", "muslim", "christian",
    "jewish", "catholic", "hindu", "buddhist", "sikh", "indian", "chinese", "korean", "japanese", "mexican",
    "filipino", "vietnamese", "italian", "irish", "haitian", "dominican", "cuban", "puerto", "colombian", "brazilian",
    "polish", "russian", "german", "french", "greek", "turkish", "arab", "pakistani", "bangladeshi", "nigerian",
    "jamaican", "canadian", "british", "english", "spanish", "native", "bilingual", "proud", "grateful", "thankful",
    "first", "second", "third", "only", "youngest", "oldest", "middle", "eldest", "ready", "sorry", "glad",
}


def _clean_name(raw: str) -> str:
    """The name words before the first word that cannot be part of a name."""
    out = []
    for w in raw.split():
        if w.lower().strip("'’-") in _NAME_STOP:
            break
        out.append(w)
    return " ".join(out)


# ----------------------------------------------------------------------------- instructions aimed at an AI
_OBSOLETE = (r"(?:obsolete|void|invalid|outdated|cancel+ed|cancelled|superseded|irrelevant|null|revoked|"
             r"no\s+longer\s+(?:apply|valid|matter|count)|to\s+be\s+(?:ignored|disregarded|discarded)|"
             r"replaced|overridden|expired|moot|wrong)")
_INJECTION = [re.compile(p, re.I | re.M) for p in (
    r"\b(?:ignore|disregard|forget|override|bypass|discard|skip)\s+(?:(?:all|any|every|the|your|my|these|those|of|everything)\s+){0,3}"
    r"(?:(?:previous|prior|above|earlier|preceding|system|original|safety|other|former|old)\s+)*(?:instructions?|prompts?)\b",
    r"\b(?:ignore|disregard|forget|override|bypass|discard|skip)\s+(?:(?:all|any|every|the|your|my|these|those|of|everything)\s+){0,3}"
    r"(?:previous|prior|above|earlier|preceding|system|original|safety|former)\s+(?:rules|directions|guidelines|context|messages?|text|content|orders|commands)\b",
    r"\bdisregard\s+(?:all\s+|the\s+|any\s+|everything\s+)?(?:above|before|previous|prior|earlier|that|this|these|those|your|rules|instructions|guidelines|directions)\b",
    r"\b(?:earlier|previous|prior|above|former|old|original|preceding)\s+(?:directions?|instructions?|rules|guidance|guidelines|prompts?|orders|commands)\s+(?:are|is|were|was|have\s+been|has\s+been)\s+(?:now\s+)?" + _OBSOLETE,
    r"\bfollow\s+(?:only|just)\b|\bonly\s+follow\b",
    r"\bfollow\s+(?:the\s+following|these|this|my|the\s+new|new)\s+(?:instructions?|directions?|commands?|rules|orders?)\b",
    r"\bobey\s+(?:the\s+following|these|this|my|all|the)\b",
    r"\b(?:the\s+)?correct\s+(?:output|answer|response|label|result|rating)\s+(?:is|are|should\s+be|must\s+be)\b",
    r"\b(?:your|the)\s+(?:task|job|role|goal|objective|mission|instructions?)\s+(?:has\s+(?:now\s+)?changed|have\s+changed|is\s+now|are\s+now|is\s+to\s+(?:output|return|say|label|rate|respond))\b",
    r"\b(?:task|instructions?)\s+(?:has|have)\s+(?:now\s+)?changed\b",
    r"\b(?:return|output)\s+only\b",
    r"\bfrom\s+now\s+on,?\s+(?:you|ignore|always|only|label|rate|output|respond|answer)\b",
    r"\bnew\s+(?:instructions?|directives?|orders?)\b",
    r"\bas\s+an?\s+(?:ai|a\.i\.|artificial\s+intelligence|llm|language\s+model)(?:\s+(?:language\s+model|assistant|model|reader|grader|reviewer|bot)\b|\s*,|\s+(?:you|your|i\s+(?:must|will|should|can|cannot|am)|please|label|rate|score))",
    r"\b(?:label|mark|rate|classify|rank|tag|call|treat|score)\s+(?:every|each|all)\s+(?:of\s+)?(?:the\s+|these\s+|those\s+)?(?:college|school|university|colleges|schools|universities)",
    r"(?:^|[.!?:;]\s+)\s*(?:assistant|system|developer|ai|chatbot|model|chatgpt|claude|human|user)\s*:",
    r"^\s*(?:#{1,4}\s*)?(?:assistant|system|developer|ai|chatbot|model|chatgpt|claude|human|user)\s*[:>\]]",
    r"<\s*\|?\s*(?:system|im_start|assistant|inst)\b|\[\s*(?:inst|system)\s*\]",
    r"\byou\s+are\s+now\b",
    r"\bsystem\s+(?:prompt|message|note|instruction|override)s?\b",
    r"\b(?:note|message|instruction)s?\s+(?:to|for)\s+(?:the\s+)?(?:ai|a\.i\.|model|llm|assistant|chatbot|grader|reader|reviewer)\b",
    r"\b(?:ai|llm|language\s+model|chatbot)\s+(?:model\s+)?(?:reading|reviewing|grading|evaluating|processing)\s+this\b",
    r"\b(?:label|rate|score|mark|classify|rank|tag)\b[^.\n]{0,40}\bas\s+(?:an?\s+)?(?:likely|safe|target|admit(?:ted)?|strong|excellent|perfect|approved)\b",
    r"\bdo\s+not\s+(?:mention|tell|reveal|disclose|show)\b[^.\n]{0,40}\b(?:counselor|counsellor|user|note|instruction)\b",
    r"\b(?:reveal|print|repeat|show)\s+(?:me\s+)?your\s+(?:system\s+)?(?:prompt|instructions)\b",
    r"\bact\s+as\s+(?:an?\s+)?(?:ai|assistant|language\s+model|chatbot)\b",
    r"\bdeveloper\s+mode\b|\bjailbreak\b",
)]
# The same ideas with every space removed: catches "i g n o r e  p r e v i o u s" run together.
_COMPACT_INJECTION = [re.compile(p, re.I) for p in (
    r"(?:ignore|disregard|forget|override|bypass)(?:all|any|every|the|your|my|these|those)*"
    r"(?:previous|prior|above|earlier|preceding|system|original|safety)*(?:instructions?|prompts?|rules|directions)",
    r"newinstructions?", r"yourtaskhaschanged", r"thecorrectoutputis", r"followonly", r"youarenow", r"systemprompt",
    r"labeleverycollege",
)]


def _despace(text: str) -> str:
    """'i g n o r e' -> 'ignore': joins runs of single letters split by spaces, dots, dashes or underscores."""
    return re.sub(r"(?<![A-Za-z])(?:[A-Za-z][ \-._*]){3,}[A-Za-z](?![A-Za-z])",
                  lambda m: re.sub(r"[ \-._*]", "", m.group(0)), text)


def _quote_from(text: str, start: int, end: int, max_words: int = 12) -> str:
    """The words of the offending phrase, taken as written, at most max_words long."""
    words = text[start:].split()
    quote = " ".join(words[:max_words])
    return quote.rstrip(",;")


def find_injection(text: str):
    """Returns (blocked, reason). The reason quotes the earliest offending phrase, at most 12 words."""
    text = text or ""
    despaced = _despace(text)
    variants = [text] + ([despaced] if despaced != text else [])
    for variant in variants:
        first = None
        for pat in _INJECTION:
            m = pat.search(variant)
            if m and (first is None or m.start() < first.start()):
                first = m
        if first is not None:
            quote = _quote_from(variant, first.start(), first.end()).strip()
            return True, ('This text contains an instruction aimed at an AI ("%s"). '
                          "It was not sent to any model. Read that part yourself and treat it as text to ignore." % quote)
    if despaced != text:  # letters were spread out on purpose: also test with all spaces gone
        squeezed = re.sub(r"[\s\-._*]+", "", text)
        for pat in _COMPACT_INJECTION:
            if pat.search(squeezed):
                return True, ("This text contains an instruction aimed at an AI, with its letters spread out so a "
                              "filter would miss it. It was not sent to any model. Read that part yourself and "
                              "treat it as text to ignore.")
    return False, ""


def _normalise(text: str) -> str:
    """Same text with full-width forms folded and invisible characters removed, so tricks do not hide details."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"[\u200b\u200c\u200d\u2060\ufeff\u00ad]", "", text)


def _sub_counting(pat, fn, text):
    """re.sub with a callback; fn returns None to leave a match alone. Returns (text, number replaced)."""
    n = 0

    def repl(m):
        nonlocal n
        r = fn(m)
        if r is None:
            return m.group(0)
        n += 1
        return r

    return pat.sub(repl, text), n


def _address_fn(m):
    words = m.group(1).lower().replace("’", "'").split()
    if any(w.strip(".,'") in _ADDR_NOT_A_STREET for w in words):
        return None
    if m.group(2).lower() in _AMBIGUOUS_SUFFIX and not any(w[:1].isupper() or w[:1].isdigit() for w in m.group(1).split()):
        return None
    return "[ADDRESS]"


def _school_fn(m):
    words = m.group(1).split()
    lead = list(words)
    while lead and lead[0].lower().strip(".'’") in _SCHOOL_LEAD_STOP:
        lead.pop(0)
    if not lead or any(w.lower().strip(".'’") in _SCHOOL_GENERIC for w in lead):
        return None
    stripped = words[:len(words) - len(lead)]  # lead-in words such as "In" or "At" stay in the text
    return (" ".join(stripped) + " " if stripped else "") + "[SCHOOL]"


def _obfuscated_email_fn(m):
    bracketed = "(" in m.group("at") or "[" in m.group("at")
    return "[EMAIL]" if (_DOT_WORD.search(m.group(0)) or bracketed) else None


def _scan(text: str):
    """Mask every detail. Returns (masked text, {kind: count})."""
    counts: dict[str, int] = {}

    def bump(kind, n=1):
        if n:
            counts[kind] = counts.get(kind, 0) + n

    # 1. Names (introduced by a phrase, a relative or a title): find them first, then replace every appearance.
    names = []
    for pat in (_NAME_TRIGGER, _RELATIVE, _TITLE):
        for m in pat.finditer(text):
            nm = _clean_name(m.group(1))
            if nm:
                names.append(nm)
    out = text
    for full in sorted(set(names), key=len, reverse=True):
        for variant in sorted({full, *[p for p in full.split() if len(p) >= 3]}, key=len, reverse=True):
            pat = re.compile(r"(?<![A-Za-z])" + re.escape(variant) + r"(?![A-Za-z])")
            out, n = pat.subn("[NAME]", out)
            bump("name", n)
    out = _TITLE_TAIL.sub("[NAME]", out)
    merged = re.subn(r"\[NAME\](?:[ \t]+\[NAME\])+", "[NAME]", out)
    out = merged[0]
    if merged[1] and "name" in counts:
        # each merged run lost tags; recount from the text so the number matches what the reader sees
        counts["name"] = out.count("[NAME]")

    # 2. Specific patterns, then the looser ones.
    for kind, tag, pat in _PATTERNS:
        out, n = pat.subn(tag, out)
        bump(kind, n)
    out, n = _sub_counting(_OBFUSCATED_EMAIL, _obfuscated_email_fn, out)
    bump("email", n)
    out, n = _sub_counting(_ADDR, _address_fn, out)
    bump("address", n)
    out, n = _PO_BOX.subn("[ADDRESS]", out)
    bump("address", n)
    out, n = re.subn(_CITY_STATE_ZIP, "[ADDRESS]", out)
    bump("address", n)
    out, n = _BORN.subn("[DOB]", out)
    bump("date of birth", n)
    for pat in _BARE_DATES:
        out, n = pat.subn("[DOB]", out)
        bump("date of birth", n)
    for pat in _PHONE_PATTERNS:
        out, n = pat.subn("[PHONE]", out)
        bump("phone", n)
    out, n = _sub_counting(_SCHOOL, _school_fn, out)
    bump("school", n)
    return out, counts


def mask(text: str) -> dict:
    """Mask identifying details and detect instructions aimed at an AI.

    Returns {"text": masked, "masked": [{"kind": "email", "count": 1}], "blocked": bool, "reason": str,
             "sensitive": [..]} where "sensitive" lists topics (health, immigration status) that were NOT masked
             because they are the substance of the essay, so the counselor knows they are present.
    """
    text = _normalise(text if isinstance(text, str) else ("" if text is None else str(text)))
    out, counts = _scan(text)

    blocked, reason = find_injection(text)  # check the original words, not the masked ones
    low = text.lower()
    sensitive = []
    if re.search(r"\b(diagnos|diabet|cancer|depress|anxiety|disorder|illness|disabilit|therapy|medication)", low):
        sensitive.append("health")
    if re.search(r"\b(undocumented|immigration|deport|visa status|asylum)", low):
        sensitive.append("immigration status")

    return {
        "text": out,
        "masked": [{"kind": k, "count": v} for k, v in counts.items()],
        "blocked": blocked,
        "reason": reason,
        "sensitive": sensitive,
    }


def looks_personal(text) -> list:
    """The kinds of personal detail (or AI instruction) found in text: [] when it looks clean.

    Kinds: email, phone, address, ssn, date of birth, school, name, instruction. One shared check for the reader,
    the case log and anything else that must refuse text carrying a personal detail.
    """
    if text is None:
        return []
    r = mask(text if isinstance(text, str) else str(text))
    kinds = [m["kind"] for m in r["masked"]]
    if r["blocked"]:
        kinds.append("instruction")
    return kinds


def summary(masked: dict) -> str:
    """One plain sentence for the screen, built from mask()'s result."""
    masked = masked or {}
    total = sum(int(m.get("count", 0)) for m in masked.get("masked", []))
    kinds = ", ".join("%d %s" % (m["count"], m["kind"]) for m in masked.get("masked", []))
    if masked.get("blocked"):
        return "This essay was held back: it contains an instruction aimed at an AI, so no model read it."
    if total == 0:
        line = "No personal details were found to mask, and the text went to the model as written."
    elif total == 1:
        line = "1 personal detail (%s) was masked before any model read the essay." % kinds
    else:
        line = "%d personal details (%s) were masked before any model read the essay." % (total, kinds)
    if masked.get("sensitive"):
        line += " Sensitive topics (%s) were left in because they are the substance of the essay." % ", ".join(masked["sensitive"])
    return line


if __name__ == "__main__":
    from pathlib import Path

    folder = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    for f in sorted(folder.glob("SYNTHETIC_essay_*.txt")):
        raw = f.read_text(encoding="utf-8")
        body = raw.split("\n", 2)[2] if raw.startswith("NOTE:") else raw
        r = mask(body)
        print("%-48s blocked=%-5s masked=%s" % (f.name, r["blocked"], r["masked"]))
        if r["blocked"]:
            print("   reason:", r["reason"])
        print("   ", summary(r))
