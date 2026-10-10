# Review of `engine/labels.py` by mistral/mistral-large-3, through Nicrron

Here are the five most serious findings, ordered by severity:

---

### 1. **Function: `_decide`**
**What is wrong:**
The function does not handle the case where `rate` is `None` in the "likely" check (`R5`). The condition `rate is not None and rate >= LIKELY_MIN_ADMIT_RATE` will short-circuit and skip the rate check if `rate` is `None`, but the logic for "likely" should explicitly require a non-`None` rate. This can lead to a "likely" label being assigned even when the admit rate is unknown, which contradicts `R2` (missing admit rate should result in "Can't say") and `R5` (which requires a known admit rate ≥ 40%).

**Concrete input:**
- College: `{"sat25": 1200, "sat75": 1400, "admit_rate": None}`
- Student: `{"sat": 1500}`

**Result:**
The function returns `("likely", "R5")`, but it should never assign "likely" when the admit rate is missing.

**Fix:**
Change the "likely" condition to explicitly require a non-`None` rate:
```python
if score >= p75 and rate is not None and rate >= LIKELY_MIN_ADMIT_RATE:
    return "likely", "R5"
```
(Note: The current code already has this, but the bug is that `_label` does not enforce this in its edge cases. The real fix is to ensure `_label` never calls `_decide` with `rate=None` when the score is ≥ p75. Add a guard in `_label` before calling `_decide`:
```python
if rate is None and score >= p75:
    return _result("cant_say", "R2", "The college's admit rate is missing, so we cannot determine if this is a likely match.")
```

---

### 2. **Function: `_label` (edge test for admit rate)**
**What is wrong:**
The edge test for "admit rate 5 points lower" does not handle the case where `rate` is `None`. This can cause a `TypeError` when `round(max(rate - RATE_STEP, 0.0), 6)` is called with `rate=None`.

**Concrete input:**
- College: `{"sat25": 1200, "sat75": 1400, "admit_rate": None}`
- Student: `{"sat": 1300}`

**Result:**
The function crashes with `TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'`.

**Fix:**
Skip the admit rate edge test if `rate` is `None`:
```python
scenarios = [
    ("score %d %s lower" % (step, unit), rate, score - step),
    ("score %d %s higher" % (step, unit), rate, score + step),
    ("admit rate 5 points lower", None if rate is None else round(max(rate - RATE_STEP, 0.0), 6), score),
]
```

---

### 3. **Function: `_label` (ACT conversion edge case)**
**What is wrong:**
If the ACT score is converted to SAT but the converted score is outside the SAT range (e.g., 1600+), the function does not validate this. The converted score could be invalid (e.g., 1660), but the function proceeds with the label logic anyway, leading to misleading results.

**Concrete input:**
- College: `{"sat25": 1500, "sat75": 1600}`
- Student: `{"act": 36}` (converts to SAT 1600+ in some tables, but the function may not cap it at 1600)

**Result:**
The function may compare a score like 1660 (invalid SAT) against the college's SAT range, leading to incorrect labels.

**Fix:**
Cap the converted SAT score at 1600:
```python
converted = act_to_sat(act)
score = min(converted, 1600) if converted is not None else None
```

---

### 4. **Function: `_label` (missing score range handling)**
**What is wrong:**
The function does not clearly distinguish between "no usable SAT or ACT range" and "no range that matches the student's test." For example, if the student has an SAT score but the college only publishes an ACT range, the error message is:
> "The student has only an SAT score and this college publishes only an ACT range, so they cannot be compared."

This is misleading because the college *does* publish a range, just not for the student's test type. The message should clarify that the college's range is for a different test.

**Concrete input:**
- College: `{"act25": 25, "act75": 30, "sat25": None, "sat75": None}`
- Student: `{"sat": 1300}`

**Result:**
The message implies the college publishes no range, which is incorrect.

**Fix:**
Update the error message to:
```python
reasons.append("The student has an SAT score, but this college publishes only an ACT range, so they cannot be compared.")
```

---

### 5. **Function: `_publisher_labels` (exception handling)**
**What is wrong:**
The function catches all exceptions (`Exception`) when calling publisher rules, which can mask bugs in the publisher functions. For example, if `_bigfuture` crashes due to a typo, the function silently returns `"-"` instead of surfacing the error.

**Concrete input:**
- Any input where a publisher function crashes (e.g., `_bigfuture` has a typo like `s < p25` → `s < p25x`).

**Result:**
The function returns `"-"` for the publisher, hiding the bug.

**Fix:**
Narrow the exception handling to specific expected errors (e.g., `TypeError`, `ValueError`) and log or raise unexpected errors:
```python
try:
    letter = fn(score, rate, p25, p75)
except (TypeError, ValueError):
    letter = "-"
except Exception as e:
    # Log or raise unexpected errors
    raise RuntimeError(f"Publisher {name} failed: {e}")
```

---

### Summary of Fixes:
1. Guard `_decide` to never assign "likely" with `rate=None`.
2. Skip admit rate edge test if `rate=None`.
3. Cap converted SAT scores at 1600.
4. Clarify error messages for mismatched test types.
5. Narrow exception handling in `_publisher_labels`.
