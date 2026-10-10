"""Privacy gate: runs in plain code, before any AI model sees an essay.

mask(text) replaces details that identify a student with tags like [NAME], and blocks text that contains
instructions aimed at an AI. No model is used here. Standard library only.

What it catches: email addresses, phone numbers, street addresses (with city/state/ZIP when written),
social security numbers, dates of birth (when written as a birthday or "born ..."), names introduced by
"my name is" or similar (and every other place that same name appears), and the name of the student's
own high school. What it does not do: it does not rename people or places that the student writes about
in the story (a neighbour, a street with no number). Counselors should still skim the masked text.
"""
from __future__ import annotations

import re

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
_DATE = (
    r"(?:\d{1,2}[/.\-]\d{1,2}[/.\-](?:\d{4}|\d{2})"
    r"|" + MONTH + r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+" + MONTH + r",?\s+\d{4}"
    r"|" + MONTH + r",?\s+\d{4})"
)
_STREET_SUFFIX = (
    r"(?:Street|St|Avenue|Ave|Road|Rd|Court|Ct|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl|Circle|Cir|"
    r"Terrace|Ter|Highway|Hwy|Parkway|Pkwy|Trail|Trl|Square|Sq|STREET|AVENUE|ROAD|COURT|DRIVE|LANE|BOULEVARD)"
)
_CITY_STATE_ZIP = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3},\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?"

# Order matters: more specific patterns run first so a number is not claimed by the wrong kind.
_PATTERNS = [
    ("email", "[EMAIL]", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")),
    ("ssn", "[SSN]", re.compile(r"(?<!\d)\d{3}[- ]\d{2}[- ]\d{4}(?!\d)")),
    ("address", "[ADDRESS]", re.compile(
        r"\b\d{1,6}\s+(?:[A-Z][A-Za-z.'\-]*\s+){1,4}" + _STREET_SUFFIX + r"\b\.?"
        r"(?:,?\s+(?:Apt|Apartment|Unit|Suite|Ste|#)\.?\s*[\w\-]+)?"
        r"(?:,\s*" + _CITY_STATE_ZIP + r")?")),
    ("address", "[ADDRESS]", re.compile(_CITY_STATE_ZIP)),
    ("phone", "[PHONE]", re.compile(
        r"(?<![\w\-])(?:\+?1[\s.\-]?)?(?:\(\d{3}\)\s*|\d{3}[\s.\-])\d{3}[\s.\-]\d{4}(?![\w\-])"
        r"|(?<![\w\-])\d{3}[\-.]\d{4}(?![\w\-])")),
    ("date of birth", "[DOB]", re.compile(
        r"(?i:\b(?:date\s+of\s+birth|dob|birthday|birthdate|born(?:\s+on|\s+in)?)\b[:\s]*(?:is\s+)?)" + _DATE)),
    ("school", "[SCHOOL]", re.compile(
        r"\b(?:[A-Z][A-Za-z.'\-]*\s+){1,5}(?:High\s+School|Preparatory(?:\s+School)?|Prep(?:\s+School)?|Academy|"
        r"Secondary\s+School|Charter\s+School|Day\s+School)\b")),
]

# Names introduced as "my name is Jane Doe" and similar. The trigger is case-insensitive, the name is not.
_NAME_TRIGGER = re.compile(
    r"(?i:\b(?:my\s+(?:full\s+)?name\s+is|my\s+name['’]s|i\s+am\s+called|i['’]m\s+called|i\s+go\s+by|call\s+me|"
    r"this\s+is\s+me,|name:))\s+((?:[A-Z][A-Za-z'’\-]+)(?:\s+(?:[A-Z][A-Za-z'’\-]+)){0,3})")
_NAME_STOP = {"I", "The", "A", "An", "And", "But", "My", "Is", "It", "In", "On", "At", "If", "So", "To", "We", "He", "She"}

# Instructions aimed at an AI. Each is a phrase that has no ordinary place in a personal essay.
_INJECTION = [re.compile(p, re.I) for p in (
    r"\b(?:ignore|disregard|forget|override|bypass)\s+(?:(?:all|any|every|the|your|my|these|those|of)\s+){0,3}"
    r"(?:(?:previous|prior|above|earlier|preceding|system|original|safety|other)\s+)*(?:instructions?|prompts?)\b",
    r"\b(?:ignore|disregard|forget|override|bypass)\s+(?:(?:all|any|every|the|your|my|these|those|of)\s+){0,3}"
    r"(?:previous|prior|above|earlier|preceding|system|original|safety)\s+(?:rules|directions|guidelines|context|messages?)\b",
    r"\byou\s+are\s+now\b",
    r"\bsystem\s+(?:prompt|message|note|instruction|override)s?\b",
    r"\b(?:note|message|instruction)s?\s+(?:to|for)\s+(?:the\s+)?(?:ai|a\.i\.|model|llm|assistant|chatbot|grader|reader|reviewer)\b",
    r"\b(?:ai|llm|language\s+model|chatbot)\s+(?:model\s+)?(?:reading|reviewing|grading|evaluating|processing)\s+this\b",
    r"\b(?:label|rate|score|mark|classify|rank|tag)\b[^.\n]{0,40}\bas\s+(?:an?\s+)?(?:likely|safe|target|admit(?:ted)?|strong|excellent|perfect)\b",
    r"\bdo\s+not\s+(?:mention|tell|reveal|disclose|show)\b[^.\n]{0,40}\b(?:counselor|counsellor|user|note|instruction)\b",
    r"\bnew\s+instructions?\b",
    r"\b(?:reveal|print|repeat|show)\s+(?:me\s+)?your\s+(?:system\s+)?(?:prompt|instructions)\b",
    r"\bact\s+as\s+(?:an?\s+)?(?:ai|assistant|language\s+model|chatbot)\b",
    r"\bdeveloper\s+mode\b|\bjailbreak\b",
)]


def _quote_from(text: str, start: int, end: int, max_words: int = 12) -> str:
    """The words of the offending phrase, taken as written, at most max_words long."""
    words = text[start:].split()
    quote = " ".join(words[:max_words])
    return quote.rstrip(",;")


def find_injection(text: str):
    """Returns (blocked, reason). The reason quotes the earliest offending phrase, at most 12 words."""
    first = None
    for pat in _INJECTION:
        m = pat.search(text)
        if m and (first is None or m.start() < first.start()):
            first = m
    if first is None:
        return False, ""
    quote = _quote_from(text, first.start(), first.end())
    return True, ('This text contains an instruction aimed at an AI ("%s"). '
                  "It was not sent to any model. Read that part yourself and treat it as text to ignore." % quote)


def mask(text: str) -> dict:
    """Mask identifying details and detect instructions aimed at an AI.

    Returns {"text": masked, "masked": [{"kind": "email", "count": 1}], "blocked": bool, "reason": str,
             "sensitive": [..]} where "sensitive" lists topics (health, immigration status) that were NOT masked
             because they are the substance of the essay, so the counselor knows they are present.
    """
    text = text or ""
    counts: dict[str, int] = {}

    def bump(kind, n=1):
        counts[kind] = counts.get(kind, 0) + n

    # 1. Names introduced by "my name is ...": find them first, then replace every appearance of that name.
    names = []
    for m in _NAME_TRIGGER.finditer(text):
        parts = [p for p in m.group(1).split() if p not in _NAME_STOP]
        if parts:
            names.append(" ".join(parts))
    out = text
    for full in sorted(set(names), key=len, reverse=True):
        for variant in sorted({full, *[p for p in full.split() if len(p) >= 3]}, key=len, reverse=True):
            pat = re.compile(r"(?<![A-Za-z])" + re.escape(variant) + r"(?![A-Za-z])")
            out, n = pat.subn("[NAME]", out)
            if n:
                bump("name", n)
    # "[NAME] [NAME]" from a first and last name replaced one by one reads as one name; count it as one.
    merged = re.subn(r"\[NAME\](?:\s+\[NAME\])+", "[NAME]", out)
    out = merged[0]
    if merged[1] and "name" in counts:
        # each merged run lost (k-1) tags; recount from the text so the number matches what the reader sees
        counts["name"] = out.count("[NAME]")

    # 2. Everything else.
    for kind, tag, pat in _PATTERNS:
        out, n = pat.subn(tag, out)
        if n:
            bump(kind, n)

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
