# Review of `engine/balance.py` by mistral/mistral-large-3, through Nicrron

Here are the five most serious findings, ordered by severity:

---

### 1. **Function: `_suggest`**
**What is wrong:**
The function fails to filter out colleges where the student's test score is below the 25th percentile (i.e., "reach" colleges) when generating suggestions. This can mislead families into thinking a college is a "likely" or "target" when it is actually a reach for the student, violating the tool's rule to avoid misleading results.

**Concrete input:**
- Student: `{"sat": 1200, "home_state": "CA"}`
- College list: `[{"name": "Stanford University", "college": {"id": "123", "admit_rate": 0.04, "sat25": 1420, "sat75": 1570}}]`
- The tool may suggest other colleges where the student's SAT (1200) is below the 25th percentile, but those colleges should not be labeled as "likely" or "target" for this student.

**Smallest fix:**
Add a check in `_suggest` to ensure the student's score is at or above the 25th percentile for the college to be considered a "likely" or "target" suggestion:
```python
if label.get("state") in pools and score >= lo:
    pools[label["state"]].append((c, label))
```

---

### 2. **Function: `_entry_admit_rate`**
**What is wrong:**
The function falls back to using the `admit_rate` from the label's `inputs` if the college's `admit_rate` is missing. However, the label's `inputs` may contain an outdated or incorrect rate, leading to inconsistent or misleading warnings (e.g., "prestige_pile" warning may not trigger correctly).

**Concrete input:**
- College entry: `{"college": None, "name": "Fake College", "label": {"state": "reach", "inputs": {"admit_rate": 0.05}}}`
- The tool may incorrectly count this as a "selective" college (admit rate < 0.15) even if the actual college data is missing or outdated.

**Smallest fix:**
Remove the fallback to `label["inputs"].get("admit_rate")` and rely only on the college's `admit_rate`:
```python
def _entry_admit_rate(entry):
    c = _college_of(entry)
    return _num(c.get("admit_rate")) if c else None
```

---

### 3. **Function: `_warnings`**
**What is wrong:**
The "prestige_pile" warning counts colleges with `admit_rate < 0.15` but does not verify if the student's test scores are competitive for those colleges. This can mislead families into thinking the list is "too reach-heavy" even if the student is a strong candidate for some of those colleges.

**Concrete input:**
- Student: `{"sat": 1550, "home_state": "NY"}`
- College list: `[{"name": "Harvard", "college": {"admit_rate": 0.04, "sat25": 1460, "sat75": 1580}}]`
- The warning will trigger even though the student is above the 75th percentile for Harvard.

**Smallest fix:**
Modify the "prestige_pile" warning to only count colleges where the student's score is below the 25th percentile:
```python
selective = 0
sat, act = _student_scores(student)
for e in entries:
    rate = _entry_admit_rate(e)
    if rate is not None and rate < 0.15:
        c = _college_of(e)
        if c and (sat is not None or act is not None):
            s25 = _num(c.get("sat25"))
            a25 = _num(c.get("act25"))
            if (sat is not None and s25 is not None and sat < s25) or (act is not None and a25 is not None and act < a25):
                selective += 1
        else:
            selective += 1
if selective >= 4:
    warns.append({"id": "prestige_pile", "text": ...})
```

---

### 4. **Function: `_cost_notes`**
**What is wrong:**
The function does not handle cases where `cost_year` is missing but `tuition_in` or `tuition_out` is available. This can lead to incomplete or misleading cost notes, violating the tool's rule to state uncertainty plainly.

**Concrete input:**
- College entry: `{"college": {"control": "public", "state": "CA", "tuition_in": 15000, "tuition_out": 40000, "cost_year": None}}`
- Student: `{"home_state": "NY"}`
- The output will only show tuition but not clarify that the full cost of attendance is unknown.

**Smallest fix:**
Add a note when `cost_year` is missing:
```python
if cost is not None:
    parts.append("the full sticker cost of attendance is about {} a year".format(_money(cost)))
else:
    parts.append("the full sticker cost of attendance is not published")
```

---

### 5. **Function: `_rank_key`**
**What is wrong:**
The function prioritizes colleges with missing `grad_rate` or `undergrads` over those with valid data (due to the `0 if grad is not None else 1` logic). This can lead to misleading suggestions, as colleges with missing data may appear higher-ranked than they should.

**Concrete input:**
- Two colleges:
  1. `{"name": "College A", "grad_rate": None, "undergrads": None, "state": "CA"}`
  2. `{"name": "College B", "grad_rate": 0.85, "undergrads": 10000, "state": "CA"}`
- Student: `{"home_state": "CA"}`
- College A may appear higher-ranked than College B, even though College B has valid data.

**Smallest fix:**
Reverse the logic to prioritize colleges with valid data:
```python
return (tier,
        1 if grad is None else 0, -(grad if grad is not None else 0.0),
        1 if size is None else 0, -(size if size is not None else 0.0),
        str(c.get("name") or ""))
```
