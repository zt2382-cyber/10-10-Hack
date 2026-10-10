# Review of `engine/privacy.py` by mistral/mistral-large-3, through Nicrron

Here are the five most serious findings, ordered by severity:

---

### 1. **Function: `_address_fn` (in `_scan`)**
**What is wrong:**
The function fails to mask valid street addresses when the suffix is ambiguous (e.g., "Way", "Dr") and the preceding words are not capitalized or contain numbers. This creates a false negative for common address formats, especially in lowercase or informal writing.

**Concrete input:**
`"i live at 123 main way, boston, ma 02134"`
**Expected:** `"i live at [ADDRESS]"`
**Actual:** No masking occurs (the address is left intact).

**Smallest fix:**
Remove the capitalization/numeric check for ambiguous suffixes. Replace:
```python
if m.group(2).lower() in _AMBIGUOUS_SUFFIX and not any(w[:1].isupper() or w[:1].isdigit() for w in m.group(1).split()):
    return None
```
with:
```python
if m.group(2).lower() in _AMBIGUOUS_SUFFIX:
    return "[ADDRESS]"
```

---

### 2. **Function: `_school_fn` (in `_scan`)**
**What is wrong:**
The function fails to mask school names when the lead-in words (e.g., "at", "in") are followed by generic terms (e.g., "public", "high"). This misses valid school names in common phrasing.

**Concrete input:**
`"at public high school, i learned..."`
**Expected:** `"at [SCHOOL], i learned..."`
**Actual:** No masking occurs (the school name is left intact).

**Smallest fix:**
Remove the generic-word check for the *entire* lead-in. Replace:
```python
if not lead or any(w.lower().strip(".'’") in _SCHOOL_GENERIC for w in lead):
    return None
```
with:
```python
if not lead:
    return None
```

---

### 3. **Function: `_obfuscated_email_fn` (in `_scan`)**
**What is wrong:**
The function only masks obfuscated emails if they contain "dot" or bracketed `@` symbols. This misses simple obfuscations like `jane at example com` (no "dot" or brackets).

**Concrete input:**
`"email me at jane at example com"`
**Expected:** `"email me at [EMAIL]"`
**Actual:** No masking occurs.

**Smallest fix:**
Remove the `or bracketed` condition. Replace:
```python
bracketed = "(" in m.group("at") or "[" in m.group("at")
return "[EMAIL]" if (_DOT_WORD.search(m.group(0)) or bracketed) else None
```
with:
```python
return "[EMAIL]" if (_DOT_WORD.search(m.group(0)) or "(" in m.group("at") or "[" in m.group("at")) else None
```
*(Note: This is a minimal fix. A better fix would be to mask all obfuscated emails regardless of "dot" or brackets.)*

---

### 4. **Function: `_clean_name`**
**What is wrong:**
The function stops cleaning a name at the first "stop word," which can split multi-word names incorrectly. For example, "Maria Del Mar Gomez" would be truncated to "Maria" if "del" is a stop word.

**Concrete input:**
`"my name is Maria Del Mar Gomez"`
**Expected:** `"my name is [NAME] [NAME] [NAME]"` (or ideally `[NAME]` for the full name)
**Actual:** `"my name is [NAME] Del Mar Gomez"` (only "Maria" is masked).

**Smallest fix:**
Add common name particles (e.g., "del", "de", "la") to `_NAME_STOP` as exceptions. Replace:
```python
_NAME_STOP = { ... }
```
with:
```python
_NAME_STOP = {
    ...,
    "del", "de", "la", "van", "von", "der", "den", "di", "du", "le", "el", "al", "bin", "ibn", "ben", "abd", "abu",
}
```

---

### 5. **Function: `find_injection`**
**What is wrong:**
The function fails to detect AI instructions when they are split by newlines or other whitespace. This creates a false negative for multi-line instructions.

**Concrete input:**
```
"ignore
all previous instructions"
```
**Expected:** Blocked with a reason.
**Actual:** Not blocked.

**Smallest fix:**
Add a variant of the text with newlines replaced by spaces. Replace:
```python
variants = [text] + ([despaced] if despaced != text else [])
```
with:
```python
variants = [text, text.replace("\n", " ")] + ([despaced] if despaced != text else [])
```

---

### Additional Note:
The `_BARE_DATES` patterns are overly permissive and may flag non-birth dates (e.g., "2020/01/01" for a project deadline). This is not a *bug* per se, but it could mislead families by masking irrelevant dates. No fix is proposed here, as the rule explicitly targets birth-year ranges.
