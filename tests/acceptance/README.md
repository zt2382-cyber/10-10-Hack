# Acceptance: the answer sheet and the one number we say aloud

## What the sheet is
`answer_sheet.csv` has 60 cells: 12 invented students (S01 to S12) times 5 real colleges from the College Scorecard
file. For each cell the expected label state and rule (R0 to R5 in `CONTRACT.md`) was worked out by hand from the
published row, with one line of working beside it. `run_acceptance.py` feeds every cell to
`engine.labels.label_college` and compares.

**Who wrote it:** an independent builder who did not see the label code (`engine/labels.py`, `engine/cases.py` and
`engine/balance.py` were not opened). The sheet comes only from `CONTRACT.md` and the published data. The expected
states were also re-derived with a small throwaway script of the builder's own, which agreed with the hand answers.

## Students
S01 SAT 1580 · S02 SAT 1450 · S03 SAT 1250 · S04 SAT 1000 · S05 ACT 29 only · S06 ACT 35 only · S07 no score ·
S08 SAT 1310 (exactly Rutgers 25th percentile) · S09 SAT 1500 (exactly Rutgers 75th) · S10 SAT 1490 (10 under
Rutgers 75th) · S11 SAT 1400 and ACT 30 · S12 SAT 1380, list includes a college not in the file.

## Colleges (published numbers as read from the file)
| College | Why chosen | Admit rate | SAT 25-75 | ACT 25-75 |
|---|---|---|---|---|
| Cornell University | under 15% | 8.76% | 1500-1570 | 33-35 |
| University of Michigan-Ann Arbor | 15% to 40% with a range | 15.64% | 1360-1530 | 31-34 |
| Rutgers University-New Brunswick | above 40% with a range | 58.15% | 1310-1500 | 28-33 |
| University of Lynchburg | SAT range only (tests ACT converted to SAT) | 43.01% | 980-1230 | none |
| Mississippi Christian University | no SAT range (ACT only) | 29.11% | none | 19-25 |

S12 has "Example College Not In File" in the place of Lynchburg, so the sheet still has 60 cells.
Every state appears: outside_data 1, reach_for_everyone 12, cant_say 12, reach 6, target 17, likely 12.
Not covered: a college with no admit rate (none exists in the file) and a college with no SAT or ACT range at all.

## How to run
From the repo root: `python tests\acceptance\run_acceptance.py`

It prints mismatches with the working line, then `ACCEPTANCE: N of 60 match the hand-written sheet`, then six
whole-system checks (PASS, FAIL or SKIPPED): no probability or "chance" wording anywhere in a Result; case pools
with n under 15 are never `ok`; labels identical across the five essays; the injection essay is blocked; essay 5's
phone numbers and emails are absent from the Result; same input twice gives the same `colleges` and `balance`.
Keys are cleared from the environment first so the model reader stays off. Output is saved to `last_run.txt`.
Exit code 0 only at 60 of 60 and no FAIL; 2 if `engine.labels` is missing.
Assumption: `engine.pipeline.run(student_input)` returns the Result dict (the contract does not give its signature).

## Open readings (the contract leaves these open; the sheet uses reading A)
1. **Student has SAT and ACT, college has only an ACT range** (S11 at Mississippi Christian). A: use the ACT
   (step 4 says "else the student's ACT"), giving target. B: R2 says "no usable range for the score the student
   has", read as the SAT, giving cant_say.
2. **Student with no test score at a college under 15%** (S07 at Cornell). A: R1 comes first, so
   reach_for_everyone. B: with no score nothing is known, so cant_say. (The contract's "first match wins" supports A.)
3. **Student has SAT and ACT, college has both ranges** (S11 at Michigan: SAT 1400 is target, ACT 30 alone would be
   reach). A: the SAT is used, target. B: use the more cautious of the two, reach.

## Say aloud
"Against 60 hand-worked checks written by someone who never saw the code, N of 60 labels match, and we can show you
the working for every one that does not."
